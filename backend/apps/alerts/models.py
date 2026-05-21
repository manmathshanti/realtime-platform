from django.db import models

from common.models import BaseModel
from apps.accounts.models import Organization, User


class ConditionOperatorChoices(models.TextChoices):
    GT = 'gt', 'Greater Than'
    GTE = 'gte', 'Greater Than or Equal'
    LT = 'lt', 'Less Than'
    LTE = 'lte', 'Less Than or Equal'
    EQ = 'eq', 'Equal'


class AlertStatusChoices(models.TextChoices):
    ACTIVE = 'active', 'Active'
    TRIGGERED = 'triggered', 'Triggered'
    RESOLVED = 'resolved', 'Resolved'
    MUTED = 'muted', 'Muted'


class NotificationChannelTypeChoices(models.TextChoices):
    EMAIL = 'email', 'Email'
    WEBHOOK = 'webhook', 'Webhook (Slack-compatible)'
    IN_APP = 'in_app', 'In-App'


class AlertRule(BaseModel):
    """
    Threshold-based alert rule.
    Example: "error_rate > 5 over 10 minutes"
    """
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='alert_rules')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, default='')
    event_name = models.CharField(max_length=255)
    condition_operator = models.CharField(max_length=10, choices=ConditionOperatorChoices.choices)
    threshold_value = models.FloatField()
    window_minutes = models.IntegerField(default=10)
    status = models.CharField(
        max_length=20, choices=AlertStatusChoices.choices, default=AlertStatusChoices.ACTIVE, db_index=True
    )
    muted_until = models.DateTimeField(null=True, blank=True)
    last_evaluated_at = models.DateTimeField(null=True, blank=True)
    last_triggered_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'alert_rules'
        indexes = [
            models.Index(fields=['organization', 'status']),
            models.Index(fields=['organization', 'event_name']),
        ]

    def __str__(self) -> str:
        return f'{self.name} ({self.event_name} {self.condition_operator} {self.threshold_value})'


class AlertHistory(BaseModel):
    """Records each time an alert rule fires."""
    alert_rule = models.ForeignKey(AlertRule, on_delete=models.CASCADE, related_name='history')
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='alert_history')
    triggered_value = models.FloatField()
    message = models.TextField(default='')
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'alert_history'
        indexes = [
            models.Index(fields=['organization', 'created_at']),
            models.Index(fields=['alert_rule', 'created_at']),
        ]
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f'Alert {self.alert_rule.name} triggered @ {self.created_at}'


class NotificationChannel(BaseModel):
    """Delivery target for alert notifications."""
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='notification_channels')
    name = models.CharField(max_length=255)
    channel_type = models.CharField(max_length=20, choices=NotificationChannelTypeChoices.choices)
    config = models.JSONField(default=dict)
    # config examples:
    #   email: {"recipients": ["a@b.com"]}
    #   webhook: {"url": "https://hooks.slack.com/...", "headers": {}}
    #   in_app: {}
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'notification_channels'
        indexes = [models.Index(fields=['organization', 'channel_type'])]

    def __str__(self) -> str:
        return f'{self.name} ({self.channel_type})'


class AlertRuleChannel(BaseModel):
    """Many-to-many link between AlertRule and NotificationChannel."""
    alert_rule = models.ForeignKey(AlertRule, on_delete=models.CASCADE, related_name='channels')
    channel = models.ForeignKey(NotificationChannel, on_delete=models.CASCADE, related_name='alert_rules')

    class Meta:
        db_table = 'alert_rule_channels'
        unique_together = [['alert_rule', 'channel']]
