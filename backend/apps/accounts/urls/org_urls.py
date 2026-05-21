from django.urls import path
from apps.accounts.views import (
    OrganizationDetailView, MemberListView, InviteMemberView,
    UpdateMemberRoleView, RemoveMemberView,
)

urlpatterns = [
    path('', OrganizationDetailView.as_view(), name='org-detail'),
    path('members/', MemberListView.as_view(), name='org-members'),
    path('members/invite/', InviteMemberView.as_view(), name='org-invite'),
    path('members/<str:user_uuid>/role/', UpdateMemberRoleView.as_view(), name='org-member-role'),
    path('members/<str:user_uuid>/', RemoveMemberView.as_view(), name='org-remove-member'),
]
