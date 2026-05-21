from typing import Optional
from datetime import timedelta
from django.utils import timezone

from common.repositories.base_repository import BaseRepository
from .models import User, Organization, OrganizationMembership, OrganizationInvite, RefreshToken, APIKey


class UserRepository(BaseRepository):
    def __init__(self):
        super().__init__(User)

    def get_by_email(self, email: str) -> Optional[User]:
        return self.get_first(filters=[('email', email)], error=False)

    def get_by_uuid(self, user_uuid: str) -> Optional[User]:
        return self.get_first(filters=[('uuid', user_uuid), ('deleted_at__isnull', True)], error=False)

    def email_exists(self, email: str) -> bool:
        return self.model.objects.filter(email=email).exists()


class OrganizationRepository(BaseRepository):
    def __init__(self):
        super().__init__(Organization)

    def get_by_slug(self, slug: str) -> Optional[Organization]:
        return self.get_first(filters=[('slug', slug), ('is_active', True)], error=False)

    def slug_exists(self, slug: str) -> bool:
        return self.model.objects.filter(slug=slug).exists()


class MembershipRepository(BaseRepository):
    def __init__(self):
        super().__init__(OrganizationMembership)

    def get_membership(self, user_id: int, org_id: int) -> Optional[OrganizationMembership]:
        return self.model.objects.select_related('organization', 'user').filter(
            user_id=user_id, organization_id=org_id, is_active=True
        ).first()

    def get_org_members(self, org_id: int):
        return self.model.objects.select_related('user').filter(
            organization_id=org_id, is_active=True, deleted_at__isnull=True
        ).order_by('joined_at')

    def user_has_role_or_above(self, user_id: int, org_id: int, minimum_role: str) -> bool:
        from common.permissions import ROLE_HIERARCHY
        membership = self.get_membership(user_id, org_id)
        if not membership:
            return False
        return ROLE_HIERARCHY.get(membership.role, 0) >= ROLE_HIERARCHY.get(minimum_role, 0)


class InviteRepository(BaseRepository):
    def __init__(self):
        super().__init__(OrganizationInvite)

    def get_by_token(self, token: str) -> Optional[OrganizationInvite]:
        return self.model.objects.select_related('organization').filter(token=token).first()

    def get_pending_for_email_and_org(self, email: str, org_id: int) -> Optional[OrganizationInvite]:
        return self.model.objects.filter(
            email=email,
            organization_id=org_id,
            status=OrganizationInvite.StatusChoices.PENDING,
            expires_at__gt=timezone.now(),
        ).first()


class RefreshTokenRepository(BaseRepository):
    def __init__(self):
        super().__init__(RefreshToken)

    def get_valid_token(self, token: str) -> Optional[RefreshToken]:
        return self.model.objects.select_related('user').filter(
            token=token, is_revoked=False, expires_at__gt=timezone.now()
        ).first()

    def revoke_all_for_user(self, user_id: int) -> int:
        return self.model.objects.filter(user_id=user_id, is_revoked=False).update(is_revoked=True)

    def cleanup_expired(self):
        self.model.objects.filter(expires_at__lt=timezone.now()).delete()


class APIKeyRepository(BaseRepository):
    def __init__(self):
        super().__init__(APIKey)

    def get_active_keys_for_org(self, org_id: int):
        return self.model.objects.filter(
            organization_id=org_id, is_active=True, deleted_at__isnull=True
        ).order_by('-created_at')

    def get_by_prefix(self, prefix: str) -> Optional[APIKey]:
        return self.model.objects.select_related('organization').filter(
            key_prefix=prefix, is_active=True
        ).first()
