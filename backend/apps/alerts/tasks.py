import logging
import requests
from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings

logger = logging.getLogger(__name__)


@shared_task
def evaluate_all_alert_rules():
    """Celery Beat task: evaluates every active alert rule."""
    from .models import AlertRule
    from .services import AlertRuleService

    service = AlertRuleService()
    rules = service.repo.get_active_rules_for_evaluation()
    triggered_count = 0

    for rule in rules:
        try:
            if service.evaluate_rule(rule):
                triggered_count += 1
        except Exception:
            logger.exception('Error evaluating rule id=%s', rule.id)

    logger.info('Alert evaluation complete. Triggered: %s/%s', triggered_count, rules.count())


@shared_task
def resolve_triggered_alerts():
    """Re-evaluate TRIGGERED rules to see if they have resolved."""
    from .models import AlertRule, AlertStatusChoices
    from .services import AlertRuleService

    service = AlertRuleService()
    rules = AlertRule.objects.filter(
        status=AlertStatusChoices.TRIGGERED,
        deleted_at__isnull=True,
    ).select_related('organization')

    for rule in rules:
        try:
            service.evaluate_rule(rule)
        except Exception:
            logger.exception('Error resolving rule id=%s', rule.id)


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def send_alert_notification(self, history_entry_id: int, channel_id: int):
    from .models import AlertHistory, NotificationChannel, NotificationChannelTypeChoices

    try:
        entry = AlertHistory.objects.select_related('alert_rule').get(pk=history_entry_id)
        channel = NotificationChannel.objects.get(pk=channel_id)
    except Exception as exc:
        logger.exception('Could not load notification objects')
        return

    try:
        if channel.channel_type == NotificationChannelTypeChoices.EMAIL:
            _send_email_notification(entry, channel)
        elif channel.channel_type == NotificationChannelTypeChoices.WEBHOOK:
            _send_webhook_notification(entry, channel)
        elif channel.channel_type == NotificationChannelTypeChoices.IN_APP:
            _send_inapp_notification(entry, channel)
    except Exception as exc:
        logger.exception('Notification failed for channel %s', channel_id)
        raise self.retry(exc=exc)


def _send_email_notification(entry, channel):
    recipients = channel.config.get('recipients', [])
    if not recipients:
        return
    rule = entry.alert_rule
    send_mail(
        subject=f'[ALERT] {rule.name} triggered',
        message=entry.message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=recipients,
        fail_silently=False,
    )
    logger.info('Alert email sent for rule %s', rule.name)


def _send_webhook_notification(entry, channel):
    url = channel.config.get('url')
    if not url:
        return
    rule = entry.alert_rule
    payload = {
        'text': entry.message,
        'attachments': [{
            'color': 'danger',
            'title': f'Alert: {rule.name}',
            'text': entry.message,
            'fields': [
                {'title': 'Event', 'value': rule.event_name, 'short': True},
                {'title': 'Triggered Value', 'value': str(entry.triggered_value), 'short': True},
            ],
            'ts': int(entry.created_at.timestamp()),
        }]
    }
    headers = channel.config.get('headers', {})
    response = requests.post(url, json=payload, headers=headers, timeout=10)
    response.raise_for_status()
    logger.info('Webhook notification sent for rule %s', rule.name)


def _send_inapp_notification(entry, channel):
    """Push an in-app notification via WebSocket to all org members."""
    try:
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync
        channel_layer = get_channel_layer()
        rule = entry.alert_rule
        async_to_sync(channel_layer.group_send)(
            f'alerts_{rule.organization_id}',
            {
                'type': 'alert.notification',
                'data': {
                    'rule_name': rule.name,
                    'message': entry.message,
                    'triggered_value': entry.triggered_value,
                    'triggered_at': entry.created_at.isoformat(),
                },
            }
        )
    except Exception:
        logger.exception('Failed to send in-app notification')


@shared_task
def process_scheduled_reports():
    """Placeholder for scheduled report generation (extend as needed)."""
    logger.info('Processing scheduled reports...')
