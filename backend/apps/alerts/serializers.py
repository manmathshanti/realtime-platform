from rest_framework import serializers
from .models import (
    AlertRule, AlertHistory, NotificationChannel,
    ConditionOperatorChoices, AlertStatusChoices, NotificationChannelTypeChoices
)


class NotificationChannelSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationChannel
        fields = ['id', 'uuid', 'name', 'channel_type', 'config', 'is_active', 'created_at']
        read_only_fields = ['id', 'uuid', 'created_at']


class CreateNotificationChannelSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)
    channel_type = serializers.ChoiceField(choices=NotificationChannelTypeChoices.choices)
    config = serializers.DictField(default=dict)

    def validate(self, attrs):
        ch_type = attrs.get('channel_type')
        config = attrs.get('config', {})
        if ch_type == 'email' and not config.get('recipients'):
            raise serializers.ValidationError({'config': 'Email channel requires "recipients" list.'})
        if ch_type == 'webhook' and not config.get('url'):
            raise serializers.ValidationError({'config': 'Webhook channel requires "url".'})
        return attrs


class AlertRuleSerializer(serializers.ModelSerializer):
    channels = serializers.SerializerMethodField()

    class Meta:
        model = AlertRule
        fields = [
            'id', 'uuid', 'name', 'description', 'event_name',
            'condition_operator', 'threshold_value', 'window_minutes',
            'status', 'muted_until', 'last_evaluated_at', 'last_triggered_at',
            'channels', 'created_at',
        ]
        read_only_fields = ['id', 'uuid', 'last_evaluated_at', 'last_triggered_at', 'created_at']

    def get_channels(self, obj) -> list:
        return [
            {'uuid': str(arc.channel.uuid), 'name': arc.channel.name, 'type': arc.channel.channel_type}
            for arc in obj.channels.select_related('channel').all()
            if arc.channel.is_active
        ]


class CreateAlertRuleSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)
    description = serializers.CharField(required=False, default='', allow_blank=True)
    event_name = serializers.CharField(max_length=255)
    condition_operator = serializers.ChoiceField(choices=ConditionOperatorChoices.choices)
    threshold_value = serializers.FloatField()
    window_minutes = serializers.IntegerField(min_value=1, max_value=1440, default=10)
    channel_uuids = serializers.ListField(
        child=serializers.UUIDField(), required=False, default=list
    )


class UpdateAlertRuleSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255, required=False)
    description = serializers.CharField(required=False, allow_blank=True)
    threshold_value = serializers.FloatField(required=False)
    window_minutes = serializers.IntegerField(min_value=1, max_value=1440, required=False)


class MuteAlertSerializer(serializers.Serializer):
    mute_minutes = serializers.IntegerField(min_value=1, max_value=10080, default=60)


class AlertHistorySerializer(serializers.ModelSerializer):
    rule_name = serializers.CharField(source='alert_rule.name', read_only=True)
    rule_uuid = serializers.UUIDField(source='alert_rule.uuid', read_only=True)

    class Meta:
        model = AlertHistory
        fields = ['id', 'uuid', 'rule_name', 'rule_uuid', 'triggered_value',
                  'message', 'resolved_at', 'created_at']
        read_only_fields = fields
