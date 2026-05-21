from common.api.base_api_view import BaseAPIView
from common.boilerplate.custom_pagination import CustomPagination
from common.decorators.auth_guard_decorator import auth_guard, require_role
from common.decorators.validate_request_decorator import validate_request
from common.helper.constants import StatusCodes

from .serializers import (
    AlertRuleSerializer, CreateAlertRuleSerializer, UpdateAlertRuleSerializer,
    MuteAlertSerializer, AlertHistorySerializer,
    NotificationChannelSerializer, CreateNotificationChannelSerializer,
)
from .services import AlertRuleService, AlertHistoryService, NotificationChannelService

sc = StatusCodes()


class AlertRuleListCreateView(BaseAPIView):
    @auth_guard()
    def get(self, request):
        rules = AlertRuleService().list_rules(request.org)
        return self.success(AlertRuleSerializer(rules, many=True).data)

    @auth_guard()
    @require_role('analyst')
    @validate_request(CreateAlertRuleSerializer)
    def post(self, request, data):
        rule = AlertRuleService().create_rule(request.org, request.jwt_user, data)
        return self.success(AlertRuleSerializer(rule).data, code=sc.CREATED)


class AlertRuleDetailView(BaseAPIView):
    @auth_guard()
    def get(self, request, rule_uuid):
        rule = AlertRuleService().get_rule(request.org, rule_uuid)
        return self.success(AlertRuleSerializer(rule).data)

    @auth_guard()
    @require_role('analyst')
    @validate_request(UpdateAlertRuleSerializer)
    def patch(self, request, data, rule_uuid):
        rule = AlertRuleService().update_rule(request.org, rule_uuid, data)
        return self.success(AlertRuleSerializer(rule).data)

    @auth_guard()
    @require_role('analyst')
    def delete(self, request, rule_uuid):
        AlertRuleService().delete_rule(request.org, rule_uuid)
        return self.no_content()


class AlertRuleMuteView(BaseAPIView):
    @auth_guard()
    @require_role('analyst')
    @validate_request(MuteAlertSerializer)
    def post(self, request, data, rule_uuid):
        rule = AlertRuleService().mute_rule(request.org, rule_uuid, data['mute_minutes'])
        return self.success(AlertRuleSerializer(rule).data)

    @auth_guard()
    @require_role('analyst')
    def delete(self, request, rule_uuid):
        rule = AlertRuleService().unmute_rule(request.org, rule_uuid)
        return self.success(AlertRuleSerializer(rule).data)


class AlertHistoryListView(BaseAPIView):
    @auth_guard()
    def get(self, request):
        rule_uuid = request.query_params.get('rule_uuid')
        history = AlertHistoryService().list_history(request.org, rule_uuid)
        paginator = CustomPagination()
        page = paginator.paginate_queryset(history, request)
        return paginator.get_paginated_response(AlertHistorySerializer(page, many=True).data)


class NotificationChannelListCreateView(BaseAPIView):
    @auth_guard()
    def get(self, request):
        channels = NotificationChannelService().list_channels(request.org)
        return self.success(NotificationChannelSerializer(channels, many=True).data)

    @auth_guard()
    @require_role('admin')
    @validate_request(CreateNotificationChannelSerializer)
    def post(self, request, data):
        channel = NotificationChannelService().create_channel(request.org, data)
        return self.success(NotificationChannelSerializer(channel).data, code=sc.CREATED)


class NotificationChannelDetailView(BaseAPIView):
    @auth_guard()
    @require_role('admin')
    def delete(self, request, channel_uuid):
        NotificationChannelService().delete_channel(request.org, channel_uuid)
        return self.no_content()
