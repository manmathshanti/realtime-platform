from rest_framework import serializers
from .models import Dashboard, Widget, SavedQuery, WidgetTypeChoices, RefreshIntervalChoices


class SavedQuerySerializer(serializers.ModelSerializer):
    class Meta:
        model = SavedQuery
        fields = ['id', 'uuid', 'name', 'event_name', 'aggregation', 'group_by',
                  'filters', 'time_range', 'interval', 'created_at']
        read_only_fields = ['id', 'uuid', 'created_at']


class CreateSavedQuerySerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)
    event_name = serializers.CharField(max_length=255)
    aggregation = serializers.ChoiceField(choices=['count', 'sum', 'avg', 'min', 'max'], default='count')
    group_by = serializers.CharField(max_length=255, required=False, default='', allow_blank=True)
    filters = serializers.DictField(required=False, default=dict)
    time_range = serializers.ChoiceField(
        choices=['1h', '24h', '7d', '30d', '90d', 'custom'], default='7d'
    )
    interval = serializers.ChoiceField(
        choices=['minute', 'hour', 'day', 'week', 'month'], default='hour'
    )


class WidgetSerializer(serializers.ModelSerializer):
    saved_query = SavedQuerySerializer(read_only=True)

    class Meta:
        model = Widget
        fields = ['id', 'uuid', 'title', 'widget_type', 'config', 'saved_query',
                  'position_x', 'position_y', 'width', 'height', 'created_at']
        read_only_fields = ['id', 'uuid', 'created_at']


class CreateWidgetSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=255)
    widget_type = serializers.ChoiceField(choices=WidgetTypeChoices.choices)
    saved_query_uuid = serializers.UUIDField(required=False, allow_null=True)
    config = serializers.DictField(required=False, default=dict)
    position_x = serializers.IntegerField(default=0, min_value=0)
    position_y = serializers.IntegerField(default=0, min_value=0)
    width = serializers.IntegerField(default=4, min_value=1, max_value=12)
    height = serializers.IntegerField(default=3, min_value=1, max_value=10)


class UpdateWidgetSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=255, required=False)
    config = serializers.DictField(required=False)
    position_x = serializers.IntegerField(min_value=0, required=False)
    position_y = serializers.IntegerField(min_value=0, required=False)
    width = serializers.IntegerField(min_value=1, max_value=12, required=False)
    height = serializers.IntegerField(min_value=1, max_value=10, required=False)


class DashboardSerializer(serializers.ModelSerializer):
    widgets = WidgetSerializer(many=True, read_only=True)
    widget_count = serializers.SerializerMethodField()

    class Meta:
        model = Dashboard
        fields = ['id', 'uuid', 'name', 'description', 'is_public', 'share_token',
                  'refresh_interval', 'layout', 'widget_count', 'widgets', 'created_at', 'updated_at']
        read_only_fields = ['id', 'uuid', 'share_token', 'widget_count', 'created_at', 'updated_at']

    def get_widget_count(self, obj) -> int:
        return obj.widgets.filter(deleted_at__isnull=True).count()


class DashboardListSerializer(serializers.ModelSerializer):
    widget_count = serializers.SerializerMethodField()

    class Meta:
        model = Dashboard
        fields = ['id', 'uuid', 'name', 'description', 'is_public',
                  'refresh_interval', 'widget_count', 'created_at', 'updated_at']
        read_only_fields = fields

    def get_widget_count(self, obj) -> int:
        return obj.widgets.filter(deleted_at__isnull=True).count()


class CreateDashboardSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)
    description = serializers.CharField(required=False, default='', allow_blank=True)
    refresh_interval = serializers.ChoiceField(
        choices=RefreshIntervalChoices.choices, default=RefreshIntervalChoices.OFF
    )


class UpdateDashboardSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255, required=False)
    description = serializers.CharField(required=False, allow_blank=True)
    refresh_interval = serializers.ChoiceField(choices=RefreshIntervalChoices.choices, required=False)
    layout = serializers.ListField(required=False)
