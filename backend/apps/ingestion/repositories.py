from typing import Optional, List
from django.utils import timezone

from common.repositories.base_repository import BaseRepository
from .models import DataSource, Event, IngestionJob


class DataSourceRepository(BaseRepository):
    def __init__(self):
        super().__init__(DataSource)

    def get_org_sources(self, org_id: int):
        return self.model.objects.filter(
            organization_id=org_id, is_active=True, deleted_at__isnull=True
        ).order_by('-created_at')

    def get_by_uuid_and_org(self, source_uuid: str, org_id: int) -> Optional[DataSource]:
        return self.model.objects.filter(
            uuid=source_uuid, organization_id=org_id, deleted_at__isnull=True
        ).first()


class EventRepository(BaseRepository):
    def __init__(self):
        super().__init__(Event)

    def bulk_create_events(self, events: List[dict]) -> int:
        objs = [Event(**e) for e in events]
        created = Event.objects.bulk_create(objs, batch_size=500, ignore_conflicts=False)
        return len(created)

    def get_org_events(self, org_id: int, filters: dict):
        qs = self.model.objects.filter(organization_id=org_id, deleted_at__isnull=True)
        if filters.get('event_name'):
            qs = qs.filter(event_name=filters['event_name'])
        if filters.get('from_ts'):
            qs = qs.filter(timestamp__gte=filters['from_ts'])
        if filters.get('to_ts'):
            qs = qs.filter(timestamp__lte=filters['to_ts'])
        return qs.order_by('-timestamp')

    def get_event_names_for_org(self, org_id: int) -> List[str]:
        return list(
            self.model.objects.filter(organization_id=org_id)
            .values_list('event_name', flat=True)
            .distinct()
            .order_by('event_name')
        )

    def count_events_in_window(self, org_id: int, event_name: str, from_ts, to_ts) -> int:
        return self.model.objects.filter(
            organization_id=org_id,
            event_name=event_name,
            timestamp__gte=from_ts,
            timestamp__lte=to_ts,
        ).count()

    def aggregate_timeseries(self, org_id: int, event_name: str, from_ts, to_ts, interval: str = 'hour'):
        """Returns time-bucketed counts for charting."""
        trunc_map = {
            'minute': 'minute',
            'hour': 'hour',
            'day': 'day',
            'week': 'week',
            'month': 'month',
        }
        trunc = trunc_map.get(interval, 'hour')
        from django.db.models.functions import Trunc
        from django.db.models import Count

        return (
            self.model.objects
            .filter(organization_id=org_id, event_name=event_name,
                    timestamp__gte=from_ts, timestamp__lte=to_ts)
            .annotate(bucket=Trunc('timestamp', trunc))
            .values('bucket')
            .annotate(count=Count('id'))
            .order_by('bucket')
        )


class IngestionJobRepository(BaseRepository):
    def __init__(self):
        super().__init__(IngestionJob)

    def get_org_jobs(self, org_id: int):
        return self.model.objects.filter(organization_id=org_id).order_by('-created_at')

    def get_by_uuid_and_org(self, job_uuid: str, org_id: int) -> Optional[IngestionJob]:
        return self.model.objects.filter(uuid=job_uuid, organization_id=org_id).first()
