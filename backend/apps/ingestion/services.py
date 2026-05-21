import csv
import io
import logging
import secrets
from typing import Optional
from django.utils import timezone
from django.core.cache import cache
from django.conf import settings

from common.service.base_service import BaseService
from common.exceptions import RateLimitException, NotFoundException, UnauthorizedException

from apps.accounts.models import Organization
from .models import DataSource, Event, IngestionJob, IngestionJobStatusChoices
from .repositories import DataSourceRepository, EventRepository, IngestionJobRepository
from .schemas import validate_batch_payload, validate_event_payload

logger = logging.getLogger(__name__)

RATE_LIMIT_PREFIX = 'rate_limit:ingestion'


class RateLimiter:
    """Redis-backed fixed-window rate limiter using atomic add+incr."""

    @staticmethod
    def check_and_increment(key: str, limit: int, window_seconds: int = 60) -> bool:
        """Returns True if within limit, False if exceeded. Thread-safe via atomic ops."""
        cache_key = f'{RATE_LIMIT_PREFIX}:{key}'
        # add() is atomic: sets key=0 with TTL only when it does not yet exist.
        cache.add(cache_key, 0, window_seconds)
        try:
            new_count = cache.incr(cache_key)
        except ValueError:
            # Key expired between add() and incr() — treat as first request in new window.
            cache.set(cache_key, 1, window_seconds)
            new_count = 1
        return new_count <= limit


class IngestionService(BaseService):
    def __init__(self):
        self.event_repo = EventRepository()
        self.source_repo = DataSourceRepository()
        self.job_repo = IngestionJobRepository()

    def _check_rate_limit(self, org: Organization):
        limit = getattr(settings, 'RATE_LIMIT_PER_ORG', 1000)
        if not RateLimiter.check_and_increment(f'org:{org.id}', limit):
            raise RateLimitException(f'Rate limit exceeded. Max {limit} requests/minute per organization.')

    def ingest_single_event(self, org: Organization, event_data: dict, source_id: int = None) -> Event:
        self._check_rate_limit(org)
        normalized_event = validate_event_payload(event_data)
        source = None
        if source_id:
            source = self.source_repo.get_first(
                filters=[('id', source_id), ('organization', org)], error=False
            )

        event = self.event_repo.create({
            'organization': org,
            'source': source,
            'event_name': normalized_event['event_name'],
            'properties': normalized_event['properties'],
            'timestamp': normalized_event['timestamp'],
        })

        self._broadcast_event(org.id, event)
        self._broadcast_dashboard_refresh(org.id)
        return event

    def ingest_batch_events(self, org: Organization, events_data: list[dict], source_id: int = None) -> dict:
        self._check_rate_limit(org)
        normalized_events = validate_batch_payload(events_data)
        source = None
        if source_id:
            source = self.source_repo.get_first(
                filters=[('id', source_id), ('organization', org)], error=False
            )

        records = []
        for evt in normalized_events:
            records.append({
                'organization': org,
                'source': source,
                'event_name': evt['event_name'],
                'properties': evt['properties'],
                'timestamp': evt['timestamp'],
            })

        count = self.event_repo.bulk_create_events(records)
        self._broadcast_dashboard_refresh(org.id)
        return {'ingested': count, 'total': len(events_data)}

    def ingest_csv(self, org: Organization, file_obj, source_id: int = None) -> IngestionJob:
        source = None
        if source_id:
            source = self.source_repo.get_first(
                filters=[('id', source_id), ('organization', org)], error=False
            )

        job = self.job_repo.create({
            'organization': org,
            'source': source,
            'file_name': getattr(file_obj, 'name', 'upload.csv'),
            'status': IngestionJobStatusChoices.PENDING,
        })

        # Read file content before it's closed
        file_content = file_obj.read().decode('utf-8')

        from apps.ingestion.tasks import process_csv_ingestion
        process_csv_ingestion.delay(job.id, file_content)
        return job

    def get_events(self, org: Organization, filters: dict):
        return self.event_repo.get_org_events(org.id, filters)

    def get_event_names(self, org: Organization) -> list[str]:
        return self.event_repo.get_event_names_for_org(org.id)

    def get_timeseries(self, org: Organization, event_name: str, from_ts, to_ts, interval: str):
        return list(self.event_repo.aggregate_timeseries(org.id, event_name, from_ts, to_ts, interval))

    def get_job(self, org: Organization, job_uuid: str) -> IngestionJob:
        job = self.job_repo.get_by_uuid_and_org(job_uuid, org.id)
        if not job:
            raise NotFoundException('Ingestion job not found.')
        return job

    def list_jobs(self, org: Organization):
        return self.job_repo.get_org_jobs(org.id)

    def create_data_source(self, org: Organization, data: dict) -> DataSource:
        webhook_secret = secrets.token_urlsafe(24) if data['source_type'] == 'webhook' else ''
        return self.source_repo.create({
            'organization': org,
            'name': data['name'],
            'source_type': data['source_type'],
            'description': data.get('description', ''),
            'webhook_secret': webhook_secret,
        })

    def list_data_sources(self, org: Organization):
        return self.source_repo.get_org_sources(org.id)

    def authenticate_webhook_source(self, source_uuid: str, provided_secret: Optional[str]) -> DataSource:
        source = self.source_repo.get_first(
            filters=[('uuid', source_uuid), ('deleted_at__isnull', True), ('is_active', True)],
            err_detail='Webhook source not found.',
        )
        if source.source_type != 'webhook':
            raise UnauthorizedException('Source is not configured for webhook ingestion.')
        if not provided_secret or provided_secret != source.webhook_secret:
            raise UnauthorizedException('Invalid webhook secret.')
        return source

    def _broadcast_event(self, org_id: int, event: Event):
        try:
            from channels.layers import get_channel_layer
            from asgiref.sync import async_to_sync
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f'events_{org_id}',
                {
                    'type': 'event.new',
                    'event': {
                        'id': event.id,
                        'event_name': event.event_name,
                        'properties': event.properties,
                        'timestamp': event.timestamp.isoformat(),
                    },
                }
            )
        except Exception:
            pass  # Don't fail ingestion because of WS broadcast error

    def _broadcast_dashboard_refresh(self, org_id: int):
        try:
            from channels.layers import get_channel_layer
            from asgiref.sync import async_to_sync

            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f'events_{org_id}',
                {
                    'type': 'dashboard.refresh',
                }
            )
        except Exception:
            pass
