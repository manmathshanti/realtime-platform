from django.contrib import admin
from .models import DataSource, Event, IngestionJob


@admin.register(DataSource)
class DataSourceAdmin(admin.ModelAdmin):
    list_display = ['name', 'organization', 'source_type', 'is_active', 'created_at']
    list_filter = ['source_type', 'is_active']
    search_fields = ['name', 'organization__name']
    raw_id_fields = ['organization']


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ['event_name', 'organization', 'timestamp', 'ingested_at']
    list_filter = ['event_name']
    search_fields = ['event_name', 'organization__name']
    raw_id_fields = ['organization', 'source']
    date_hierarchy = 'timestamp'


@admin.register(IngestionJob)
class IngestionJobAdmin(admin.ModelAdmin):
    list_display = ['id', 'organization', 'status', 'total_records', 'processed_records',
                    'failed_records', 'file_name', 'created_at']
    list_filter = ['status']
    search_fields = ['organization__name', 'file_name']
    raw_id_fields = ['organization', 'source']
    readonly_fields = ['error_log']
