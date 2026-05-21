import logging
import operator
from datetime import timedelta
from django.utils import timezone

from common.service.base_service import BaseService
from common.exceptions import NotFoundException, ValidationException

from apps.accounts.models import Organization, User
from .models import (
    AlertRule, AlertHistory, NotificationChannel, AlertRuleChannel,
    AlertStatusChoices, ConditionOperatorChoices
)
from .repositories import AlertRuleRepository, AlertHistoryRepository, NotificationChannelRepository

logger = logging.getLogger(__name__)

OPERATOR_MAP = {
    ConditionOperatorChoices.GT: operator.gt,
    ConditionOperatorChoices.GTE: operator.ge,
    ConditionOperatorChoices.LT: operator.lt,
    ConditionOperatorChoices.LTE: operator.le,
    ConditionOperatorChoices.EQ: operator.eq,
}


class AlertRuleService(BaseService):
    def __init__(self):
        self.repo = AlertRuleRepository()
        self.history_repo = AlertHistoryRepository()
        self.channel_repo = NotificationChannelRepository()

    def list_rules(self, org: Organization):
        return self.repo.get_org_rules(org.id)

    def get_rule(self, org: Organization, rule_uuid: str) -> AlertRule:
        rule = self.repo.get_by_uuid_and_org(rule_uuid, org.id)
        if not rule:
            raise NotFoundException('Alert rule not found.')
        return rule

    def create_rule(self, org: Organization, user: User, data: dict) -> AlertRule:
        rule = self.repo.create({
            'organization': org,
            'created_by': user,
            'name': data['name'],
            'description': data.get('description', ''),
            'event_name': data['event_name'],
            'condition_operator': data['condition_operator'],
            'threshold_value': data['threshold_value'],
            'window_minutes': data.get('window_minutes', 10),
        })

        for channel_uuid in data.get('channel_uuids', []):
            channel = self.channel_repo.get_by_uuid_and_org(str(channel_uuid), org.id)
            if channel:
                AlertRuleChannel.objects.create(alert_rule=rule, channel=channel)

        return rule

    def update_rule(self, org: Organization, rule_uuid: str, data: dict) -> AlertRule:
        rule = self.get_rule(org, rule_uuid)
        updatable = ['name', 'description', 'threshold_value', 'window_minutes']
        for field in updatable:
            if field in data:
                setattr(rule, field, data[field])
        rule.save(update_fields=[f for f in updatable if f in data] + ['updated_at'])
        return rule

    def delete_rule(self, org: Organization, rule_uuid: str):
        rule = self.get_rule(org, rule_uuid)
        rule.deleted_at = timezone.now()
        rule.save(update_fields=['deleted_at', 'updated_at'])

    def mute_rule(self, org: Organization, rule_uuid: str, mute_minutes: int):
        rule = self.get_rule(org, rule_uuid)
        rule.status = AlertStatusChoices.MUTED
        rule.muted_until = timezone.now() + timedelta(minutes=mute_minutes)
        rule.save(update_fields=['status', 'muted_until', 'updated_at'])
        return rule

    def unmute_rule(self, org: Organization, rule_uuid: str):
        rule = self.get_rule(org, rule_uuid)
        rule.status = AlertStatusChoices.ACTIVE
        rule.muted_until = None
        rule.save(update_fields=['status', 'muted_until', 'updated_at'])
        return rule

    def evaluate_rule(self, rule: AlertRule) -> bool:
        """Evaluates a single alert rule. Returns True if triggered."""
        from apps.ingestion.models import Event

        now = timezone.now()
        window_start = now - timedelta(minutes=rule.window_minutes)

        count = Event.objects.filter(
            organization=rule.organization,
            event_name=rule.event_name,
            timestamp__gte=window_start,
            timestamp__lte=now,
        ).count()

        op_func = OPERATOR_MAP.get(rule.condition_operator)
        triggered = op_func(count, rule.threshold_value) if op_func else False

        rule.last_evaluated_at = now
        if triggered:
            rule.status = AlertStatusChoices.TRIGGERED
            rule.last_triggered_at = now
            rule.save(update_fields=['status', 'last_evaluated_at', 'last_triggered_at', 'updated_at'])

            entry = self.history_repo.create({
                'alert_rule': rule,
                'organization': rule.organization,
                'triggered_value': float(count),
                'message': (
                    f'Alert "{rule.name}": {rule.event_name} count was {count} '
                    f'({rule.condition_operator} {rule.threshold_value}) '
                    f'in the last {rule.window_minutes} minutes.'
                ),
            })
            self._send_notifications(rule, entry)
            self._push_alert_to_ws(rule)
        else:
            if rule.status == AlertStatusChoices.TRIGGERED:
                rule.status = AlertStatusChoices.RESOLVED
            rule.save(update_fields=['status', 'last_evaluated_at', 'updated_at'])
            # Resolve open history entries
            self.history_repo.model.objects.filter(
                alert_rule=rule, resolved_at__isnull=True
            ).update(resolved_at=now)

        return triggered

    def _send_notifications(self, rule: AlertRule, history_entry: AlertHistory):
        from apps.alerts.tasks import send_alert_notification
        for arc in rule.channels.select_related('channel').all():
            if arc.channel.is_active:
                send_alert_notification.delay(history_entry.id, arc.channel.id)

    def _push_alert_to_ws(self, rule: AlertRule):
        try:
            from channels.layers import get_channel_layer
            from asgiref.sync import async_to_sync
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f'alerts_{rule.organization_id}',
                {
                    'type': 'alert.triggered',
                    'alert': {
                        'rule_uuid': str(rule.uuid),
                        'rule_name': rule.name,
                        'event_name': rule.event_name,
                        'threshold': rule.threshold_value,
                        'triggered_at': rule.last_triggered_at.isoformat(),
                    },
                }
            )
        except Exception:
            pass


class AlertHistoryService(BaseService):
    def __init__(self):
        self.repo = AlertHistoryRepository()

    def list_history(self, org: Organization, rule_uuid: str = None):
        rule_id = None
        if rule_uuid:
            rule = AlertRule.objects.filter(uuid=rule_uuid, organization=org).first()
            if rule:
                rule_id = rule.id
        return self.repo.get_org_history(org.id, rule_id)


class NotificationChannelService(BaseService):
    def __init__(self):
        self.repo = NotificationChannelRepository()

    def list_channels(self, org: Organization):
        return self.repo.get_org_channels(org.id)

    def create_channel(self, org: Organization, data: dict) -> NotificationChannel:
        return self.repo.create({
            'organization': org,
            'name': data['name'],
            'channel_type': data['channel_type'],
            'config': data.get('config', {}),
        })

    def delete_channel(self, org: Organization, channel_uuid: str):
        channel = self.repo.get_by_uuid_and_org(channel_uuid, org.id)
        if not channel:
            raise NotFoundException('Notification channel not found.')
        channel.deleted_at = timezone.now()
        channel.save(update_fields=['deleted_at', 'updated_at'])
