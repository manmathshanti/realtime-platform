from django.db import models

from common.models import BaseModel
from apps.accounts.models import Organization


class DataSourceTypeChoices(models.TextChoices):
    API = 'api', 'API'
    CSV = 'csv', 'CSV Upload'
    WEBHOOK = 'webhook', 'Webhook'


class DataSource(BaseModel):
    """Named data source belonging to an org (API endpoint, CSV, webhook)."""
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='data_sources')
    name = models.CharField(max_length=255)
    source_type = models.CharField(max_length=20, choices=DataSourceTypeChoices.choices)
    description = models.TextField(blank=True, default='')
    is_active = models.BooleanField(default=True)
    webhook_secret = models.CharField(max_length=255, blank=True, default='')

    class Meta:
        db_table = 'data_sources'
        indexes = [models.Index(fields=['organization', 'source_type'])]

    def __str__(self) -> str:
        return f'{self.name} ({self.source_type})'


class Event(BaseModel):
    """
    Core time-series event record.
    Indexed for fast org + event_name + timestamp queries.
    """
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='events', db_index=True)
    source = models.ForeignKey(DataSource, on_delete=models.SET_NULL, null=True, blank=True, related_name='events')
    event_name = models.CharField(max_length=255, db_index=True)
    properties = models.JSONField(default=dict)
    timestamp = models.DateTimeField(db_index=True)
    ingested_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = 'events'
        indexes = [
            models.Index(fields=['organization', 'event_name', 'timestamp']),
            models.Index(fields=['organization', 'timestamp']),
            models.Index(fields=['event_name', 'timestamp']),
        ]
        ordering = ['-timestamp']

    def __str__(self) -> str:
        return f'{self.event_name} @ {self.timestamp}'


class IngestionJobStatusChoices(models.TextChoices):
    PENDING = 'pending', 'Pending'
    PROCESSING = 'processing', 'Processing'
    COMPLETED = 'completed', 'Completed'
    FAILED = 'failed', 'Failed'
    PARTIAL = 'partial', 'Partial'


class IngestionJob(BaseModel):
    """Tracks batch and CSV ingestion jobs."""
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='ingestion_jobs')
    source = models.ForeignKey(DataSource, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=IngestionJobStatusChoices.choices,
        default=IngestionJobStatusChoices.PENDING,
        db_index=True,
    )
    total_records = models.IntegerField(default=0)
    processed_records = models.IntegerField(default=0)
    failed_records = models.IntegerField(default=0)
    error_log = models.JSONField(default=list)
    file_name = models.CharField(max_length=255, blank=True, default='')
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'ingestion_jobs'
        indexes = [
            models.Index(fields=['organization', 'status']),
            models.Index(fields=['organization', 'created_at']),
        ]

    def __str__(self) -> str:
        return f'Job {self.id} [{self.status}] {self.file_name or "batch"}'
