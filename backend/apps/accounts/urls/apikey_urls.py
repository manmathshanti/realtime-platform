from django.urls import path
from apps.accounts.views import APIKeyListCreateView, APIKeyRevokeView, APIKeyRotateView

urlpatterns = [
    path('', APIKeyListCreateView.as_view(), name='apikey-list-create'),
    path('<str:key_uuid>/', APIKeyRevokeView.as_view(), name='apikey-revoke'),
    path('<str:key_uuid>/rotate/', APIKeyRotateView.as_view(), name='apikey-rotate'),
]
