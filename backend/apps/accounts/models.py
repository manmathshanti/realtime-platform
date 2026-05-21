import uuid
import secrets
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.utils import timezone

from common.models import BaseModel


class UserManager(BaseUserManager):
    def create_user(self, email: str, password: str = None, **extra_fields):
        if not email:
            raise ValueError('Email is required')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email: str, password: str = None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, db_index=True, editable=False)
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100, blank=True, default='')
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_email_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name']

    objects = UserManager()

    class Meta:
        db_table = 'users'
        indexes = [models.Index(fields=['email'])]

    @property
    def full_name(self) -> str:
        return f'{self.first_name} {self.last_name}'.strip()

    def __str__(self) -> str:
        return self.email


class Organization(BaseModel):
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=100, unique=True, db_index=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'organizations'

    def __str__(self) -> str:
        return self.name


class RoleChoices(models.TextChoices):
    OWNER = 'owner', 'Owner'
    ADMIN = 'admin', 'Admin'
    ANALYST = 'analyst', 'Analyst'
    VIEWER = 'viewer', 'Viewer'


class OrganizationMembership(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='memberships')
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='memberships')
    role = models.CharField(max_length=20, choices=RoleChoices.choices, default=RoleChoices.VIEWER)
    is_active = models.BooleanField(default=True)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'organization_memberships'
        unique_together = [['user', 'organization']]
        indexes = [
            models.Index(fields=['user', 'organization']),
            models.Index(fields=['organization', 'role']),
        ]

    def __str__(self) -> str:
        return f'{self.user.email} @ {self.organization.name} ({self.role})'


class OrganizationInvite(BaseModel):
    class StatusChoices(models.TextChoices):
        PENDING = 'pending', 'Pending'
        ACCEPTED = 'accepted', 'Accepted'
        EXPIRED = 'expired', 'Expired'
        REVOKED = 'revoked', 'Revoked'

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='invites')
    invited_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='sent_invites')
    email = models.EmailField()
    role = models.CharField(max_length=20, choices=RoleChoices.choices, default=RoleChoices.VIEWER)
    token = models.CharField(max_length=255, unique=True, db_index=True)
    status = models.CharField(max_length=20, choices=StatusChoices.choices, default=StatusChoices.PENDING)
    expires_at = models.DateTimeField()
    accepted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'organization_invites'
        indexes = [
            models.Index(fields=['token']),
            models.Index(fields=['email', 'organization']),
        ]

    @classmethod
    def generate_token(cls) -> str:
        return secrets.token_urlsafe(32)

    @property
    def is_expired(self) -> bool:
        return timezone.now() > self.expires_at

    def __str__(self) -> str:
        return f'Invite {self.email} → {self.organization.name}'


class RefreshToken(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='refresh_tokens')
    token = models.CharField(max_length=512, unique=True, db_index=True)
    is_revoked = models.BooleanField(default=False, db_index=True)
    expires_at = models.DateTimeField()

    class Meta:
        db_table = 'refresh_tokens'

    @property
    def is_expired(self) -> bool:
        return timezone.now() > self.expires_at


class APIKey(BaseModel):
    """Org-scoped API key for data ingestion endpoints."""

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='api_keys')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_api_keys')
    name = models.CharField(max_length=100)
    key_prefix = models.CharField(max_length=12)
    key_hash = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True, db_index=True)
    last_used_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    revoked_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'api_keys'
        indexes = [
            models.Index(fields=['key_prefix']),
            models.Index(fields=['organization', 'is_active']),
        ]

    @classmethod
    def generate_key(cls) -> tuple[str, str, str]:
        """Returns (full_key, prefix, hash). Call once — full key is not stored."""
        import hashlib
        raw = f'rpk_{secrets.token_urlsafe(40)}'
        prefix = raw[:12]
        key_hash = hashlib.sha256(raw.encode()).hexdigest()
        return raw, prefix, key_hash

    @classmethod
    def verify_key(cls, raw_key: str, stored_hash: str) -> bool:
        import hashlib
        return hashlib.sha256(raw_key.encode()).hexdigest() == stored_hash

    def __str__(self) -> str:
        return f'{self.name} ({self.key_prefix}...)'
