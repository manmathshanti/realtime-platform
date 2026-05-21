import secrets
from typing import Optional
from datetime import timedelta
from django.utils import timezone
from django.utils.text import slugify
from django.conf import settings

from common.auth.jwt_service import JWTService
from common.exceptions import (
    ConflictException, UnauthorizedException, NotFoundException,
    ValidationException, ForbiddenException
)
from common.service.base_service import BaseService

from .models import (
    User, Organization, OrganizationMembership, OrganizationInvite,
    RefreshToken, APIKey, RoleChoices
)
from .repositories import (
    UserRepository, OrganizationRepository, MembershipRepository,
    InviteRepository, RefreshTokenRepository, APIKeyRepository
)

_REFRESH_COOKIE_MAX_AGE = 30 * 24 * 60 * 60


class AuthService(BaseService):
    def __init__(self):
        self.user_repo = UserRepository()
        self.org_repo = OrganizationRepository()
        self.membership_repo = MembershipRepository()
        self.refresh_repo = RefreshTokenRepository()
        self.jwt = JWTService()

    def register(self, data: dict) -> dict:
        email = data['email'].lower()
        if self.user_repo.email_exists(email):
            raise ConflictException('An account with this email already exists.')

        # Build org slug
        base_slug = slugify(data['org_name'])
        slug = base_slug
        counter = 1
        while self.org_repo.slug_exists(slug):
            slug = f'{base_slug}-{counter}'
            counter += 1

        user = self.user_repo.create({
            'email': email,
            'first_name': data['first_name'],
            'last_name': data.get('last_name', ''),
        })
        user.set_password(data['password'])
        user.save(update_fields=['password'])

        org = self.org_repo.create({'name': data['org_name'], 'slug': slug})
        self.membership_repo.create({
            'user': user,
            'organization': org,
            'role': RoleChoices.OWNER,
        })

        tokens = self._issue_tokens(user)
        return {'user': user, 'organization': org, **tokens}

    def login(self, data: dict) -> dict:
        email = data['email'].lower()
        user = self.user_repo.get_by_email(email)
        if not user or not user.check_password(data['password']):
            raise UnauthorizedException('Invalid email or password.')
        if not user.is_active:
            raise UnauthorizedException('Account is disabled.')

        tokens = self._issue_tokens(user)
        return {'user': user, **tokens}

    def refresh(self, token: str) -> dict:
        stored = self.refresh_repo.get_valid_token(token)
        if not stored:
            raise UnauthorizedException('Invalid or expired refresh token.')

        stored.is_revoked = True
        stored.save(update_fields=['is_revoked'])

        return self._issue_tokens(stored.user)

    def logout(self, token: str):
        self.refresh_repo.update_where(
            [('token', token)], [('is_revoked', True)]
        )

    def change_password(self, user: User, current_password: str, new_password: str):
        if not user.check_password(current_password):
            raise ValidationException('Current password is incorrect.')
        user.set_password(new_password)
        user.save(update_fields=['password'])
        self.refresh_repo.revoke_all_for_user(user.id)

    def _issue_tokens(self, user: User) -> dict:
        access_token = self.jwt.create_access_token(str(user.uuid))
        raw_refresh = self.jwt.create_refresh_token(str(user.uuid))
        exp_days = getattr(settings, 'JWT_REFRESH_EXP_DAYS', 30)
        self.refresh_repo.create({
            'user': user,
            'token': raw_refresh,
            'expires_at': timezone.now() + timedelta(days=exp_days),
        })
        return {'access_token': access_token, 'refresh_token': raw_refresh}


class OrganizationService(BaseService):
    def __init__(self):
        self.org_repo = OrganizationRepository()
        self.membership_repo = MembershipRepository()
        self.invite_repo = InviteRepository()
        self.user_repo = UserRepository()
        self.refresh_repo = RefreshTokenRepository()
        self.jwt = JWTService()

    def get_org(self, org) -> Organization:
        return org

    def update_org(self, org: Organization, data: dict) -> Organization:
        if 'name' in data:
            org.name = data['name']
            org.save(update_fields=['name', 'updated_at'])
        return org

    def list_members(self, org: Organization):
        return self.membership_repo.get_org_members(org.id)

    def update_member_role(self, org: Organization, requesting_user: User, target_user_uuid: str, role: str):
        target_user = self.user_repo.get_by_uuid(target_user_uuid)
        if not target_user:
            raise NotFoundException('User not found.')

        target_membership = self.membership_repo.get_membership(target_user.id, org.id)
        if not target_membership:
            raise NotFoundException('User is not a member of this organization.')

        if target_membership.role == RoleChoices.OWNER and requesting_user != target_user:
            raise ForbiddenException('Cannot change the owner role.')

        target_membership.role = role
        target_membership.save(update_fields=['role', 'updated_at'])
        return target_membership

    def remove_member(self, org: Organization, requesting_user: User, target_user_uuid: str):
        target_user = self.user_repo.get_by_uuid(target_user_uuid)
        if not target_user:
            raise NotFoundException('User not found.')
        if target_user == requesting_user:
            raise ValidationException('You cannot remove yourself.')

        target_membership = self.membership_repo.get_membership(target_user.id, org.id)
        if not target_membership:
            raise NotFoundException('User is not a member.')
        if target_membership.role == RoleChoices.OWNER:
            raise ForbiddenException('Cannot remove the owner.')

        target_membership.is_active = False
        target_membership.save(update_fields=['is_active', 'updated_at'])

    def invite_member(self, org: Organization, invited_by: User, email: str, role: str) -> OrganizationInvite:
        email = email.lower()
        existing = self.invite_repo.get_pending_for_email_and_org(email, org.id)
        if existing:
            raise ConflictException('A pending invite already exists for this email.')

        invite = self.invite_repo.create({
            'organization': org,
            'invited_by': invited_by,
            'email': email,
            'role': role,
            'token': OrganizationInvite.generate_token(),
            'expires_at': timezone.now() + timedelta(days=7),
        })

        from apps.accounts.tasks import send_invite_email
        send_invite_email.delay(invite.id)
        return invite

    def accept_invite(self, token: str, data: dict) -> dict:
        invite = self.invite_repo.get_by_token(token)
        if not invite:
            raise NotFoundException('Invite not found.')
        if invite.status != OrganizationInvite.StatusChoices.PENDING:
            raise ValidationException(f'Invite is already {invite.status}.')
        if invite.is_expired:
            invite.status = OrganizationInvite.StatusChoices.EXPIRED
            invite.save(update_fields=['status'])
            raise ValidationException('Invite has expired.')

        user = self.user_repo.get_by_email(invite.email)
        if not user:
            if not data.get('password') or not data.get('first_name'):
                raise ValidationException('New users must provide first_name and password.')
            user = self.user_repo.create({
                'email': invite.email,
                'first_name': data['first_name'],
                'last_name': data.get('last_name', ''),
            })
            user.set_password(data['password'])
            user.save(update_fields=['password'])

        existing_membership = self.membership_repo.get_membership(user.id, invite.organization_id)
        if existing_membership:
            raise ConflictException('User is already a member of this organization.')

        self.membership_repo.create({
            'user': user,
            'organization': invite.organization,
            'role': invite.role,
        })

        invite.status = OrganizationInvite.StatusChoices.ACCEPTED
        invite.accepted_at = timezone.now()
        invite.save(update_fields=['status', 'accepted_at'])

        exp_days = getattr(settings, 'JWT_REFRESH_EXP_DAYS', 30)
        access_token = self.jwt.create_access_token(str(user.uuid))
        raw_refresh = self.jwt.create_refresh_token(str(user.uuid))
        self.refresh_repo.create({
            'user': user,
            'token': raw_refresh,
            'expires_at': timezone.now() + timedelta(days=exp_days),
        })
        return {
            'user': user,
            'organization': invite.organization,
            'access_token': access_token,
            'refresh_token': raw_refresh,
        }


class APIKeyService(BaseService):
    def __init__(self):
        self.repo = APIKeyRepository()

    def list_keys(self, org: Organization):
        return self.repo.get_active_keys_for_org(org.id)

    def create_key(self, org: Organization, created_by: User, name: str, expires_at=None) -> tuple:
        raw_key, prefix, key_hash = APIKey.generate_key()
        api_key = self.repo.create({
            'organization': org,
            'created_by': created_by,
            'name': name,
            'key_prefix': prefix,
            'key_hash': key_hash,
            'expires_at': expires_at,
        })
        return api_key, raw_key

    def revoke_key(self, org: Organization, key_uuid: str):
        key = self.repo.get_first(
            filters=[('uuid', key_uuid), ('organization', org), ('is_active', True)],
            err_detail='API key not found.'
        )
        key.is_active = False
        key.revoked_at = timezone.now()
        key.save(update_fields=['is_active', 'revoked_at', 'updated_at'])

    def rotate_key(self, org: Organization, key_uuid: str) -> tuple:
        old_key = self.repo.get_first(
            filters=[('uuid', key_uuid), ('organization', org), ('is_active', True)],
            err_detail='API key not found.'
        )
        old_key.is_active = False
        old_key.revoked_at = timezone.now()
        old_key.save(update_fields=['is_active', 'revoked_at', 'updated_at'])
        return self.create_key(org, old_key.created_by, f'{old_key.name} (rotated)', old_key.expires_at)

    def authenticate_api_key(self, raw_key: str) -> Optional[Organization]:
        """Verifies an API key and returns the organization. Returns None on failure."""
        if not raw_key or len(raw_key) < 12:
            return None
        prefix = raw_key[:12]
        api_key_obj = self.repo.get_by_prefix(prefix)
        if not api_key_obj:
            return None
        if not APIKey.verify_key(raw_key, api_key_obj.key_hash):
            return None
        if api_key_obj.expires_at and timezone.now() > api_key_obj.expires_at:
            return None
        api_key_obj.last_used_at = timezone.now()
        api_key_obj.save(update_fields=['last_used_at'])
        return api_key_obj.organization
