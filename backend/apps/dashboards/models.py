import secrets
from django.db import models

from common.models import BaseModel
from apps.accounts.models import Organization, User


class WidgetTypeChoices(models.TextChoices):
    LINE_CHART = 'line_chart', 'Line Chart'
    BAR_CHART = 'bar_chart', 'Bar Chart'
    PIE_CHART = 'pie_chart', 'Pie Chart'
    KPI_CARD = 'kpi_card', 'KPI Card'
    TABLE = 'table', 'Table'


class RefreshIntervalChoices(models.IntegerChoices):
    OFF = 0, 'Off'
    THIRTY_SECONDS = 30, '30 Seconds'
    ONE_MINUTE = 60, '1 Minute'
    FIVE_MINUTES = 300, '5 Minutes'


class Dashboard(BaseModel):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='dashboards')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='dashboards')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, default='')
    is_public = models.BooleanField(default=False)
    share_token = models.CharField(max_length=64, unique=True, null=True, blank=True, db_index=True)
    refresh_interval = models.IntegerField(
        choices=RefreshIntervalChoices.choices, default=RefreshIntervalChoices.OFF
    )
    layout = models.JSONField(default=list)  # stores widget position/size grid state

    class Meta:
        db_table = 'dashboards'
        indexes = [
            models.Index(fields=['organization', 'deleted_at']),
            models.Index(fields=['share_token']),
        ]

    def generate_share_token(self) -> str:
        token = secrets.token_urlsafe(32)
        self.share_token = token
        self.is_public = True
        self.save(update_fields=['share_token', 'is_public', 'updated_at'])
        return token

    def revoke_share_token(self):
        self.share_token = None
        self.is_public = False
        self.save(update_fields=['share_token', 'is_public', 'updated_at'])

    def __str__(self) -> str:
        return f'{self.name} ({self.organization.name})'


class SavedQuery(BaseModel):
    """Reusable named query that a widget executes."""
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='saved_queries')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    name = models.CharField(max_length=255)
    event_name = models.CharField(max_length=255)
    aggregation = models.CharField(max_length=50, default='count')  # count, sum, avg, p95…
    group_by = models.CharField(max_length=255, blank=True, default='')
    filters = models.JSONField(default=dict)
    time_range = models.CharField(max_length=50, default='7d')  # 1h, 24h, 7d, 30d, custom
    interval = models.CharField(max_length=20, default='hour')  # minute, hour, day

    class Meta:
        db_table = 'saved_queries'
        indexes = [models.Index(fields=['organization'])]

    def __str__(self) -> str:
        return self.name


class Widget(BaseModel):
    """A chart/metric widget on a dashboard connected to a saved query."""
    dashboard = models.ForeignKey(Dashboard, on_delete=models.CASCADE, related_name='widgets')
    saved_query = models.ForeignKey(SavedQuery, on_delete=models.SET_NULL, null=True, blank=True)
    title = models.CharField(max_length=255)
    widget_type = models.CharField(max_length=30, choices=WidgetTypeChoices.choices)
    config = models.JSONField(default=dict)  # chart colors, units, thresholds, …
    position_x = models.IntegerField(default=0)
    position_y = models.IntegerField(default=0)
    width = models.IntegerField(default=4)
    height = models.IntegerField(default=3)

    class Meta:
        db_table = 'widgets'
        indexes = [models.Index(fields=['dashboard'])]
        ordering = ['position_y', 'position_x']

    def __str__(self) -> str:
        return f'{self.title} ({self.widget_type})'
