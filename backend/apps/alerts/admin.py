from django.contrib import admin
from .models import AlertRule, AlertHistory, NotificationChannel, AlertRuleChannel


@admin.register(AlertRule)
class AlertRuleAdmin(admin.ModelAdmin):
    list_display = ['name', 'organization', 'event_name', 'condition_operator',
                    'threshold_value', 'window_minutes', 'status', 'last_triggered_at']
    list_filter = ['status', 'condition_operator']
    search_fields = ['name', 'event_name', 'organization__name']
    raw_id_fields = ['organization', 'created_by']


@admin.register(AlertHistory)
class AlertHistoryAdmin(admin.ModelAdmin):
    list_display = ['alert_rule', 'organization', 'triggered_value', 'resolved_at', 'created_at']
    list_filter = ['organization']
    raw_id_fields = ['alert_rule', 'organization']
    date_hierarchy = 'created_at'


@admin.register(NotificationChannel)
class NotificationChannelAdmin(admin.ModelAdmin):
    list_display = ['name', 'organization', 'channel_type', 'is_active', 'created_at']
    list_filter = ['channel_type', 'is_active']
    search_fields = ['name', 'organization__name']
    raw_id_fields = ['organization']
