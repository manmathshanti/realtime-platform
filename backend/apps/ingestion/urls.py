from django.urls import path
from .views import (
    IngestSingleEventView, IngestBatchEventsView, IngestCSVView,
    DataSourceListCreateView, IngestionJobListView, IngestionJobDetailView,
    EventListView, EventNamesView, EventTimeseriesView,
)

urlpatterns = [
    # Ingestion endpoints (API key auth)
    path('events/', IngestSingleEventView.as_view(), name='ingest-single'),
    path('batch/', IngestBatchEventsView.as_view(), name='ingest-batch'),
    path('csv/', IngestCSVView.as_view(), name='ingest-csv'),

    # Data Sources
    path('sources/', DataSourceListCreateView.as_view(), name='data-source-list'),

    # Jobs
    path('jobs/', IngestionJobListView.as_view(), name='ingestion-job-list'),
    path('jobs/<str:job_uuid>/', IngestionJobDetailView.as_view(), name='ingestion-job-detail'),

    # Query
    path('query/events/', EventListView.as_view(), name='event-list'),
    path('query/event-names/', EventNamesView.as_view(), name='event-names'),
    path('query/timeseries/', EventTimeseriesView.as_view(), name='event-timeseries'),
]
