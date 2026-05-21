from rest_framework import serializers
from django.utils import timezone

from .models import DataSource, Event, IngestionJob, DataSourceTypeChoices


class EventPayloadSerializer(serializers.Serializer):
    """Validates a single inbound event."""
    event_name = serializers.CharField(max_length=255)
    properties = serializers.DictField(required=False, default=dict)
    timestamp = serializers.DateTimeField(required=False)
    source_id = serializers.IntegerField(required=False, allow_null=True)

    def validate_timestamp(self, value):
        if value and value > timezone.now():
            raise serializers.ValidationError('Timestamp cannot be in the future.')
        return value

    def validate(self, attrs):
        if not attrs.get('timestamp'):
            attrs['timestamp'] = timezone.now()
        return attrs


class BatchIngestionSerializer(serializers.Serializer):
    """Validates batch event ingestion payload."""
    events = serializers.ListField(
        child=EventPayloadSerializer(),
        min_length=1,
        max_length=1000,
    )
    source_id = serializers.IntegerField(required=False, allow_null=True)


class CreateDataSourceSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)
    source_type = serializers.ChoiceField(choices=DataSourceTypeChoices.choices)
    description = serializers.CharField(required=False, default='', allow_blank=True)


class DataSourceSerializer(serializers.ModelSerializer):
    has_webhook_secret = serializers.SerializerMethodField()

    class Meta:
        model = DataSource
        fields = ['id', 'uuid', 'name', 'source_type', 'description', 'is_active', 'has_webhook_secret', 'created_at']
        read_only_fields = fields

    def get_has_webhook_secret(self, obj) -> bool:
        return bool(obj.webhook_secret)


class EventSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = ['id', 'uuid', 'event_name', 'properties', 'timestamp', 'ingested_at']
        read_only_fields = fields


class IngestionJobSerializer(serializers.ModelSerializer):
    class Meta:
        model = IngestionJob
        fields = [
            'id', 'uuid', 'status', 'total_records', 'processed_records',
            'failed_records', 'file_name', 'started_at', 'completed_at', 'created_at',
        ]
        read_only_fields = fields


class EventQuerySerializer(serializers.Serializer):
    """Query params for listing/aggregating events."""
    event_name = serializers.CharField(required=False)
    from_ts = serializers.DateTimeField(required=False)
    to_ts = serializers.DateTimeField(required=False)
    page = serializers.IntegerField(required=False, min_value=1, default=1)
    per_page = serializers.IntegerField(required=False, min_value=1, max_value=500, default=50)
