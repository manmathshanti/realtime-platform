from typing import Optional
from django.utils import timezone

from common.repositories.base_repository import BaseRepository
from .models import AlertRule, AlertHistory, NotificationChannel, AlertRuleChannel, AlertStatusChoices


class AlertRuleRepository(BaseRepository):
    def __init__(self):
        super().__init__(AlertRule)

    def get_org_rules(self, org_id: int):
        return self.model.objects.filter(
            organization_id=org_id, deleted_at__isnull=True
        ).prefetch_related('channels__channel').order_by('-created_at')

    def get_active_rules_for_evaluation(self):
        """All non-muted, non-deleted rules that need evaluation."""
        return self.model.objects.filter(
            deleted_at__isnull=True,
            status__in=[AlertStatusChoices.ACTIVE, AlertStatusChoices.TRIGGERED],
        ).exclude(
            status=AlertStatusChoices.MUTED,
            muted_until__gt=timezone.now(),
        ).select_related('organization')

    def get_by_uuid_and_org(self, rule_uuid: str, org_id: int) -> Optional[AlertRule]:
        return self.model.objects.filter(
            uuid=rule_uuid, organization_id=org_id, deleted_at__isnull=True
        ).first()


class AlertHistoryRepository(BaseRepository):
    def __init__(self):
        super().__init__(AlertHistory)

    def get_org_history(self, org_id: int, rule_id: int = None):
        qs = self.model.objects.filter(organization_id=org_id)
        if rule_id:
            qs = qs.filter(alert_rule_id=rule_id)
        return qs.select_related('alert_rule').order_by('-created_at')

    def get_unresolved_for_rule(self, rule_id: int):
        return self.model.objects.filter(alert_rule_id=rule_id, resolved_at__isnull=True)


class NotificationChannelRepository(BaseRepository):
    def __init__(self):
        super().__init__(NotificationChannel)

    def get_org_channels(self, org_id: int):
        return self.model.objects.filter(
            organization_id=org_id, is_active=True, deleted_at__isnull=True
        ).order_by('-created_at')

    def get_by_uuid_and_org(self, channel_uuid: str, org_id: int) -> Optional[NotificationChannel]:
        return self.model.objects.filter(
            uuid=channel_uuid, organization_id=org_id, deleted_at__isnull=True
        ).first()
