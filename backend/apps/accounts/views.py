from django.conf import settings
from rest_framework import status

from common.api.base_api_view import BaseAPIView
from common.decorators.auth_guard_decorator import auth_guard, require_role
from common.decorators.validate_request_decorator import validate_request
from common.helper.constants import StatusCodes

from .serializers import (
    RegisterSerializer, LoginSerializer, RefreshTokenSerializer,
    ChangePasswordSerializer, InviteMemberSerializer, AcceptInviteSerializer,
    UpdateMemberRoleSerializer, CreateAPIKeySerializer,
    UserSerializer, OrganizationSerializer, MemberListSerializer,
    InviteSerializer, APIKeySerializer, APIKeyCreatedSerializer,
    UpdateOrganizationSerializer,
)
from .services import AuthService, OrganizationService, APIKeyService

sc = StatusCodes()


# ── Auth Views ────────────────────────────────────────────────────────────────

class RegisterView(BaseAPIView):
    @validate_request(RegisterSerializer)
    def post(self, request, data):
        result = AuthService().register(data)
        return self.success(
            {
                'user': UserSerializer(result['user']).data,
                'organization': OrganizationSerializer(result['organization']).data,
                'access_token': result['access_token'],
                'refresh_token': result['refresh_token'],
            },
            code=sc.CREATED,
            msg='Registration successful.',
        )


class LoginView(BaseAPIView):
    @validate_request(LoginSerializer)
    def post(self, request, data):
        result = AuthService().login(data)
        response = self.success(
            {
                'user': UserSerializer(result['user']).data,
                'access_token': result['access_token'],
            },
            msg='Login successful.',
        )
        response.set_cookie(
            key='refresh_token',
            value=result['refresh_token'],
            httponly=True,
            secure=not settings.DEBUG,
            samesite='Lax',
            max_age=30 * 24 * 60 * 60,
        )
        return response


class RefreshTokenView(BaseAPIView):
    def post(self, request):
        token = request.COOKIES.get('refresh_token') or request.data.get('refresh_token')
        if not token:
            return self.error_message('Refresh token required', sc.UNAUTHORIZED)
        result = AuthService().refresh(token)
        response = self.success({'access_token': result['access_token']}, msg='Token refreshed.')
        response.set_cookie(
            key='refresh_token',
            value=result['refresh_token'],
            httponly=True,
            secure=not settings.DEBUG,
            samesite='Lax',
            max_age=30 * 24 * 60 * 60,
        )
        return response


class LogoutView(BaseAPIView):
    @auth_guard()
    def post(self, request):
        token = request.COOKIES.get('refresh_token') or request.data.get('refresh_token')
        if token:
            AuthService().logout(token)
        response = self.no_content()
        response.delete_cookie('refresh_token')
        return response


class MeView(BaseAPIView):
    @auth_guard()
    def get(self, request):
        return self.success(UserSerializer(request.jwt_user).data)

    @auth_guard()
    def patch(self, request):
        user = request.jwt_user
        allowed = ['first_name', 'last_name']
        for field in allowed:
            if field in request.data:
                setattr(user, field, request.data[field])
        user.save(update_fields=allowed + ['updated_at'])
        return self.success(UserSerializer(user).data)


class ChangePasswordView(BaseAPIView):
    @auth_guard()
    @validate_request(ChangePasswordSerializer)
    def post(self, request, data):
        AuthService().change_password(request.jwt_user, data['current_password'], data['new_password'])
        return self.success(None, msg='Password changed successfully.')


class AcceptInvitePublicView(BaseAPIView):
    @validate_request(AcceptInviteSerializer)
    def post(self, request, data):
        result = OrganizationService().accept_invite(data['token'], data)
        response = self.success(
            {
                'user': UserSerializer(result['user']).data,
                'organization': OrganizationSerializer(result['organization']).data,
                'access_token': result['access_token'],
            },
            code=sc.CREATED,
        )
        response.set_cookie(
            key='refresh_token',
            value=result['refresh_token'],
            httponly=True,
            secure=not settings.DEBUG,
            samesite='Lax',
            max_age=30 * 24 * 60 * 60,
        )
        return response


class GoogleAuthView(BaseAPIView):
    def post(self, request):
        credential = request.data.get('credential', '').strip()
        if not credential:
            return self.error_message('credential is required', sc.BAD_REQUEST)
        result = AuthService().google_auth(credential)
        response = self.success(
            {
                'user': UserSerializer(result['user']).data,
                'access_token': result['access_token'],
            },
            msg='Google login successful.',
        )
        response.set_cookie(
            key='refresh_token',
            value=result['refresh_token'],
            httponly=True,
            secure=not settings.DEBUG,
            samesite='Lax',
            max_age=30 * 24 * 60 * 60,
        )
        return response


# ── Org Views ─────────────────────────────────────────────────────────────────

class OrganizationDetailView(BaseAPIView):
    @auth_guard()
    def get(self, request):
        if not request.org:
            return self.error_message('No organization found', sc.NOT_FOUND)
        return self.success(OrganizationSerializer(request.org).data)

    @auth_guard()
    @require_role('admin')
    @validate_request(UpdateOrganizationSerializer)
    def patch(self, request, data):
        org = OrganizationService().update_org(request.org, data)
        return self.success(OrganizationSerializer(org).data)


class MemberListView(BaseAPIView):
    @auth_guard()
    def get(self, request):
        if not request.org:
            return self.error_message('No organization found', sc.NOT_FOUND)
        members = OrganizationService().list_members(request.org)
        return self.success(MemberListSerializer(members, many=True).data)


class InviteMemberView(BaseAPIView):
    @auth_guard()
    @require_role('admin')
    @validate_request(InviteMemberSerializer)
    def post(self, request, data):
        invite = OrganizationService().invite_member(
            request.org, request.jwt_user, data['email'], data['role']
        )
        return self.success(InviteSerializer(invite).data, code=sc.CREATED)


class UpdateMemberRoleView(BaseAPIView):
    @auth_guard()
    @require_role('admin')
    @validate_request(UpdateMemberRoleSerializer)
    def patch(self, request, data, user_uuid):
        membership = OrganizationService().update_member_role(
            request.org, request.jwt_user, user_uuid, data['role']
        )
        return self.success(MemberListSerializer(membership).data)


class RemoveMemberView(BaseAPIView):
    @auth_guard()
    @require_role('admin')
    def delete(self, request, user_uuid):
        OrganizationService().remove_member(request.org, request.jwt_user, user_uuid)
        return self.no_content()


# ── API Key Views ─────────────────────────────────────────────────────────────

class APIKeyListCreateView(BaseAPIView):
    @auth_guard()
    def get(self, request):
        keys = APIKeyService().list_keys(request.org)
        return self.success(APIKeySerializer(keys, many=True).data)

    @auth_guard()
    @require_role('admin')
    @validate_request(CreateAPIKeySerializer)
    def post(self, request, data):
        api_key, raw_key = APIKeyService().create_key(
            request.org, request.jwt_user, data['name'], data.get('expires_at')
        )
        response_data = dict(APIKeyCreatedSerializer(api_key).data)
        response_data['full_key'] = raw_key
        return self.success(response_data, code=sc.CREATED,
                            msg='Store this key securely — it will not be shown again.')


class APIKeyRevokeView(BaseAPIView):
    @auth_guard()
    @require_role('admin')
    def delete(self, request, key_uuid):
        APIKeyService().revoke_key(request.org, key_uuid)
        return self.no_content()


class APIKeyRotateView(BaseAPIView):
    @auth_guard()
    @require_role('admin')
    def post(self, request, key_uuid):
        api_key, raw_key = APIKeyService().rotate_key(request.org, key_uuid)
        response_data = dict(APIKeyCreatedSerializer(api_key).data)
        response_data['full_key'] = raw_key
        return self.success(response_data, msg='Key rotated successfully. Store the new key securely.')
