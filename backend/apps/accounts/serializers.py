from rest_framework import serializers
from django.utils.text import slugify

from .models import User, Organization, OrganizationMembership, OrganizationInvite, APIKey, RoleChoices


# ── Auth ──────────────────────────────────────────────────────────────────────

class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(min_length=8, write_only=True)
    first_name = serializers.CharField(max_length=100)
    last_name = serializers.CharField(max_length=100, required=False, default='')
    org_name = serializers.CharField(max_length=255)

    def validate_password(self, value: str) -> str:
        if not any(c.isdigit() for c in value):
            raise serializers.ValidationError('Password must contain at least one digit.')
        return value


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class RefreshTokenSerializer(serializers.Serializer):
    refresh_token = serializers.CharField()


class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(min_length=8, write_only=True)


class InviteMemberSerializer(serializers.Serializer):
    email = serializers.EmailField()
    role = serializers.ChoiceField(choices=RoleChoices.choices, default=RoleChoices.VIEWER)


class AcceptInviteSerializer(serializers.Serializer):
    token = serializers.CharField()
    password = serializers.CharField(min_length=8, write_only=True, required=False)
    first_name = serializers.CharField(max_length=100, required=False)
    last_name = serializers.CharField(max_length=100, required=False, default='')


class UpdateMemberRoleSerializer(serializers.Serializer):
    role = serializers.ChoiceField(choices=RoleChoices.choices)


# ── Response ──────────────────────────────────────────────────────────────────

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['uuid', 'email', 'first_name', 'last_name', 'full_name',
                  'is_email_verified', 'created_at']
        read_only_fields = fields


class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = ['uuid', 'name', 'slug', 'created_at']
        read_only_fields = fields


class MembershipSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    organization = OrganizationSerializer(read_only=True)

    class Meta:
        model = OrganizationMembership
        fields = ['uuid', 'user', 'organization', 'role', 'joined_at']
        read_only_fields = fields


class MemberListSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = OrganizationMembership
        fields = ['uuid', 'user', 'role', 'joined_at', 'is_active']
        read_only_fields = fields


class InviteSerializer(serializers.ModelSerializer):
    organization = OrganizationSerializer(read_only=True)

    class Meta:
        model = OrganizationInvite
        fields = ['uuid', 'email', 'role', 'status', 'expires_at', 'organization', 'created_at']
        read_only_fields = fields


# ── API Key ───────────────────────────────────────────────────────────────────

class CreateAPIKeySerializer(serializers.Serializer):
    name = serializers.CharField(max_length=100)
    expires_at = serializers.DateTimeField(required=False, allow_null=True)


class APIKeySerializer(serializers.ModelSerializer):
    class Meta:
        model = APIKey
        fields = ['uuid', 'name', 'key_prefix', 'is_active', 'last_used_at',
                  'expires_at', 'created_at']
        read_only_fields = fields


class APIKeyCreatedSerializer(serializers.ModelSerializer):
    """Returned once on creation. Caller adds 'full_key' to the dict after serializing."""

    class Meta:
        model = APIKey
        fields = ['uuid', 'name', 'key_prefix', 'expires_at', 'created_at']
        read_only_fields = fields


# ── Org Update ────────────────────────────────────────────────────────────────

class UpdateOrganizationSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255, required=False)
