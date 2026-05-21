import logging
from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_invite_email(self, invite_id: int):
    try:
        from .models import OrganizationInvite
        invite = OrganizationInvite.objects.select_related('organization', 'invited_by').get(pk=invite_id)
        frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
        accept_url = f'{frontend_url}/invite/accept?token={invite.token}'
        send_mail(
            subject=f'You\'re invited to join {invite.organization.name}',
            message=(
                f'Hi,\n\n'
                f'{invite.invited_by.full_name if invite.invited_by else "Someone"} has invited you '
                f'to join {invite.organization.name} as {invite.get_role_display()}.\n\n'
                f'Accept your invitation:\n{accept_url}\n\n'
                f'This invite expires in 7 days.'
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[invite.email],
            fail_silently=False,
        )
        logger.info('Invite email sent to %s for org %s', invite.email, invite.organization.name)
    except Exception as exc:
        logger.exception('Failed to send invite email for invite_id=%s', invite_id)
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_password_reset_email(self, user_id: int, reset_token: str):
    try:
        from .models import User
        user = User.objects.get(pk=user_id)
        frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
        reset_url = f'{frontend_url}/auth/reset-password?token={reset_token}'
        send_mail(
            subject='Reset your password',
            message=f'Hi {user.first_name},\n\nClick the link to reset your password:\n{reset_url}\n\nThis link expires in 1 hour.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
    except Exception as exc:
        logger.exception('Failed to send password reset email for user_id=%s', user_id)
        raise self.retry(exc=exc)
