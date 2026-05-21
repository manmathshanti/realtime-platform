from rest_framework import status

from common.api.base_api_view import BaseAPIView
from common.boilerplate.custom_pagination import CustomPagination
from common.decorators.auth_guard_decorator import auth_guard, require_role
from common.decorators.validate_request_decorator import validate_request
from common.exceptions import UnauthorizedException
from common.helper.constants import StatusCodes

from apps.accounts.services import APIKeyService
from .serializers import (
    EventPayloadSerializer, BatchIngestionSerializer, CreateDataSourceSerializer,
    DataSourceSerializer, EventSerializer, IngestionJobSerializer, EventQuerySerializer,
)
from .services import IngestionService

sc = StatusCodes()


def _get_org_from_api_key(request):
    """Resolves organization from X-API-Key header."""
    raw_key = request.headers.get('X-Api-Key') or request.headers.get('X-API-KEY')
    if not raw_key:
        raise UnauthorizedException('API key required. Provide X-Api-Key header.')
    org = APIKeyService().authenticate_api_key(raw_key)
    if not org:
        raise UnauthorizedException('Invalid or inactive API key.')
    return org


# ── Ingestion endpoints (API key auth) ────────────────────────────────────────

class IngestSingleEventView(BaseAPIView):
    @validate_request(EventPayloadSerializer)
    def post(self, request, data):
        org = _get_org_from_api_key(request)
        source_id = request.data.get('source_id')
        event = IngestionService().ingest_single_event(org, data, source_id)
        return self.success(
            EventSerializer(event).data,
            code=sc.CREATED,
            msg='Event ingested.',
        )


class IngestBatchEventsView(BaseAPIView):
    @validate_request(BatchIngestionSerializer)
    def post(self, request, data):
        org = _get_org_from_api_key(request)
        result = IngestionService().ingest_batch_events(org, data['events'], data.get('source_id'))
        return self.success(result, code=sc.CREATED, msg=f'{result["ingested"]} events ingested.')


class IngestCSVView(BaseAPIView):
    @auth_guard()
    @require_role('analyst')
    def post(self, request):
        file_obj = request.FILES.get('file')
        if not file_obj:
            return self.error_message('No file provided. Send file as multipart/form-data field "file".', sc.BAD_REQUEST)
        if not file_obj.name.endswith('.csv'):
            return self.error_message('Only CSV files are supported.', sc.BAD_REQUEST)
        if file_obj.size > 10 * 1024 * 1024:
            return self.error_message('File exceeds 10MB limit.', sc.BAD_REQUEST)

        source_id = request.data.get('source_id')
        job = IngestionService().ingest_csv(request.org, file_obj, source_id)
        return self.success(IngestionJobSerializer(job).data, code=sc.CREATED,
                            msg='CSV upload queued for processing.')


# ── Data Sources (JWT auth) ───────────────────────────────────────────────────

class DataSourceListCreateView(BaseAPIView):
    @auth_guard()
    def get(self, request):
        sources = IngestionService().list_data_sources(request.org)
        return self.success(DataSourceSerializer(sources, many=True).data)

    @auth_guard()
    @require_role('admin')
    @validate_request(CreateDataSourceSerializer)
    def post(self, request, data):
        source = IngestionService().create_data_source(request.org, data)
        return self.success(DataSourceSerializer(source).data, code=sc.CREATED)


# ── Ingestion Jobs (JWT auth) ─────────────────────────────────────────────────

class IngestionJobListView(BaseAPIView):
    @auth_guard()
    def get(self, request):
        jobs = IngestionService().list_jobs(request.org)
        paginator = CustomPagination()
        page = paginator.paginate_queryset(jobs, request)
        return paginator.get_paginated_response(IngestionJobSerializer(page, many=True).data)


class IngestionJobDetailView(BaseAPIView):
    @auth_guard()
    def get(self, request, job_uuid):
        job = IngestionService().get_job(request.org, job_uuid)
        return self.success(IngestionJobSerializer(job).data)


# ── Event Query (JWT auth) ────────────────────────────────────────────────────

class EventListView(BaseAPIView):
    @auth_guard()
    def get(self, request):
        params = {
            'event_name': request.query_params.get('event_name'),
            'from_ts': request.query_params.get('from_ts'),
            'to_ts': request.query_params.get('to_ts'),
        }
        events = IngestionService().get_events(request.org, params)
        paginator = CustomPagination()
        page = paginator.paginate_queryset(events, request)
        return paginator.get_paginated_response(EventSerializer(page, many=True).data)


class EventNamesView(BaseAPIView):
    @auth_guard()
    def get(self, request):
        names = IngestionService().get_event_names(request.org)
        return self.success(names)


class EventTimeseriesView(BaseAPIView):
    @auth_guard()
    def get(self, request):
        from django.utils.dateparse import parse_datetime
        event_name = request.query_params.get('event_name')
        from_ts = request.query_params.get('from_ts')
        to_ts = request.query_params.get('to_ts')
        interval = request.query_params.get('interval', 'hour')

        if not event_name:
            return self.error_message('event_name is required', sc.BAD_REQUEST)

        from_dt = parse_datetime(from_ts) if from_ts else None
        to_dt = parse_datetime(to_ts) if to_ts else None

        if not from_dt or not to_dt:
            from django.utils import timezone
            from datetime import timedelta
            to_dt = timezone.now()
            from_dt = to_dt - timedelta(days=7)

        data = IngestionService().get_timeseries(request.org, event_name, from_dt, to_dt, interval)
        result = [{'bucket': row['bucket'].isoformat(), 'count': row['count']} for row in data]
        return self.success(result)
