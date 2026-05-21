from django.contrib import admin
from .models import Dashboard, Widget, SavedQuery


@admin.register(Dashboard)
class DashboardAdmin(admin.ModelAdmin):
    list_display = ['name', 'organization', 'is_public', 'refresh_interval', 'created_at']
    list_filter = ['is_public', 'refresh_interval']
    search_fields = ['name', 'organization__name']
    raw_id_fields = ['organization', 'created_by']


@admin.register(Widget)
class WidgetAdmin(admin.ModelAdmin):
    list_display = ['title', 'dashboard', 'widget_type', 'position_x', 'position_y', 'created_at']
    list_filter = ['widget_type']
    search_fields = ['title', 'dashboard__name']
    raw_id_fields = ['dashboard', 'saved_query']


@admin.register(SavedQuery)
class SavedQueryAdmin(admin.ModelAdmin):
    list_display = ['name', 'organization', 'event_name', 'aggregation', 'time_range', 'created_at']
    search_fields = ['name', 'event_name', 'organization__name']
    raw_id_fields = ['organization', 'created_by']
