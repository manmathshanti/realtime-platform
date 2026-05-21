import csv
import io
import logging
from datetime import datetime
from celery import shared_task
from django.utils import timezone
from django.utils.dateparse import parse_datetime

logger = logging.getLogger(__name__)

REQUIRED_CSV_COLUMNS = {'event_name'}


@shared_task(bind=True, max_retries=2, default_retry_delay=30)
def process_csv_ingestion(self, job_id: int, file_content: str):
    from .models import IngestionJob, IngestionJobStatusChoices, Event
    from .repositories import IngestionJobRepository

    job_repo = IngestionJobRepository()
    job = IngestionJob.objects.select_related('organization').get(pk=job_id)

    job.status = IngestionJobStatusChoices.PROCESSING
    job.started_at = timezone.now()
    job.save(update_fields=['status', 'started_at'])

    try:
        reader = csv.DictReader(io.StringIO(file_content))
        fieldnames = set(reader.fieldnames or [])
        missing = REQUIRED_CSV_COLUMNS - fieldnames
        if missing:
            raise ValueError(f'CSV missing required columns: {missing}')

        rows = list(reader)
        job.total_records = len(rows)
        job.save(update_fields=['total_records'])

        events = []
        errors = []

        for i, row in enumerate(rows, start=1):
            try:
                event_name = row.get('event_name', '').strip()
                if not event_name:
                    raise ValueError('event_name is empty')

                ts_raw = row.get('timestamp')
                timestamp = parse_datetime(ts_raw) if ts_raw else timezone.now()
                if not timestamp:
                    timestamp = timezone.now()

                properties = {k: v for k, v in row.items()
                              if k not in ('event_name', 'timestamp') and v}

                events.append(Event(
                    organization=job.organization,
                    source=job.source,
                    event_name=event_name,
                    properties=properties,
                    timestamp=timestamp,
                ))

                if len(events) >= 500:
                    Event.objects.bulk_create(events, batch_size=500)
                    job.processed_records += len(events)
                    events = []
                    job.save(update_fields=['processed_records'])

            except Exception as exc:
                errors.append({'row': i, 'error': str(exc)})

        if events:
            Event.objects.bulk_create(events, batch_size=500)
            job.processed_records += len(events)

        job.failed_records = len(errors)
        job.error_log = errors[:100]  # cap stored errors
        job.status = (
            IngestionJobStatusChoices.PARTIAL if errors else IngestionJobStatusChoices.COMPLETED
        )
        job.completed_at = timezone.now()
        job.save(update_fields=['processed_records', 'failed_records', 'error_log', 'status', 'completed_at'])
        logger.info('CSV job %s done: %s processed, %s failed', job_id, job.processed_records, job.failed_records)

    except Exception as exc:
        job.status = IngestionJobStatusChoices.FAILED
        job.error_log = [{'error': str(exc)}]
        job.completed_at = timezone.now()
        job.save(update_fields=['status', 'error_log', 'completed_at'])
        logger.exception('CSV job %s failed', job_id)
        raise self.retry(exc=exc)
