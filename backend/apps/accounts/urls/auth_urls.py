from django.urls import path
from apps.accounts.views import (
    RegisterView, LoginView, RefreshTokenView, LogoutView,
    MeView, ChangePasswordView, AcceptInvitePublicView, GoogleAuthView,
)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='auth-register'),
    path('login/', LoginView.as_view(), name='auth-login'),
    path('google/', GoogleAuthView.as_view(), name='auth-google'),
    path('refresh/', RefreshTokenView.as_view(), name='auth-refresh'),
    path('logout/', LogoutView.as_view(), name='auth-logout'),
    path('me/', MeView.as_view(), name='auth-me'),
    path('me/password/', ChangePasswordView.as_view(), name='auth-change-password'),
    path('invite/accept/', AcceptInvitePublicView.as_view(), name='auth-accept-invite'),
]
