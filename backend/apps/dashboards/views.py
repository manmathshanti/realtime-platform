from common.api.base_api_view import BaseAPIView
from common.decorators.auth_guard_decorator import auth_guard, require_role
from common.decorators.validate_request_decorator import validate_request
from common.helper.constants import StatusCodes

from .serializers import (
    DashboardSerializer, DashboardListSerializer, CreateDashboardSerializer,
    UpdateDashboardSerializer, WidgetSerializer, CreateWidgetSerializer,
    UpdateWidgetSerializer, SavedQuerySerializer, CreateSavedQuerySerializer,
)
from .services import DashboardService, WidgetService, SavedQueryService

sc = StatusCodes()


# ── Dashboards ────────────────────────────────────────────────────────────────

class DashboardListCreateView(BaseAPIView):
    @auth_guard()
    def get(self, request):
        dashboards = DashboardService().list_dashboards(request.org)
        return self.success(DashboardListSerializer(dashboards, many=True).data)

    @auth_guard()
    @require_role('analyst')
    @validate_request(CreateDashboardSerializer)
    def post(self, request, data):
        dashboard = DashboardService().create_dashboard(request.org, request.jwt_user, data)
        return self.success(DashboardSerializer(dashboard).data, code=sc.CREATED)


class DashboardDetailView(BaseAPIView):
    @auth_guard()
    def get(self, request, dashboard_uuid):
        dashboard = DashboardService().get_dashboard(request.org, dashboard_uuid)
        return self.success(DashboardSerializer(dashboard).data)

    @auth_guard()
    @require_role('analyst')
    @validate_request(UpdateDashboardSerializer)
    def patch(self, request, data, dashboard_uuid):
        dashboard = DashboardService().update_dashboard(request.org, dashboard_uuid, data)
        return self.success(DashboardSerializer(dashboard).data)

    @auth_guard()
    @require_role('analyst')
    def delete(self, request, dashboard_uuid):
        DashboardService().delete_dashboard(request.org, dashboard_uuid)
        return self.no_content()


class DashboardShareView(BaseAPIView):
    @auth_guard()
    @require_role('analyst')
    def post(self, request, dashboard_uuid):
        token = DashboardService().enable_sharing(request.org, dashboard_uuid)
        return self.success({'share_token': token, 'is_public': True})

    @auth_guard()
    @require_role('analyst')
    def delete(self, request, dashboard_uuid):
        DashboardService().disable_sharing(request.org, dashboard_uuid)
        return self.success({'is_public': False})


class PublicDashboardView(BaseAPIView):
    """No auth — readable via share_token."""
    def get(self, request, token):
        dashboard = DashboardService().get_public_dashboard(token)
        return self.success(DashboardSerializer(dashboard).data)


# ── Widgets ───────────────────────────────────────────────────────────────────

class WidgetListCreateView(BaseAPIView):
    @auth_guard()
    def get(self, request, dashboard_uuid):
        widgets = WidgetService().list_widgets(request.org, dashboard_uuid)
        return self.success(WidgetSerializer(widgets, many=True).data)

    @auth_guard()
    @require_role('analyst')
    @validate_request(CreateWidgetSerializer)
    def post(self, request, data, dashboard_uuid):
        widget = WidgetService().create_widget(request.org, dashboard_uuid, data)
        return self.success(WidgetSerializer(widget).data, code=sc.CREATED)


class WidgetDetailView(BaseAPIView):
    @auth_guard()
    @require_role('analyst')
    @validate_request(UpdateWidgetSerializer)
    def patch(self, request, data, dashboard_uuid, widget_uuid):
        widget = WidgetService().update_widget(request.org, dashboard_uuid, widget_uuid, data)
        return self.success(WidgetSerializer(widget).data)

    @auth_guard()
    @require_role('analyst')
    def delete(self, request, dashboard_uuid, widget_uuid):
        WidgetService().delete_widget(request.org, dashboard_uuid, widget_uuid)
        return self.no_content()


class WidgetDataView(BaseAPIView):
    """Execute the widget's saved query and return chart data."""
    @auth_guard()
    def get(self, request, dashboard_uuid, widget_uuid):
        data = WidgetService().execute_widget_query(request.org, dashboard_uuid, widget_uuid)
        return self.success(data)


# ── Saved Queries ─────────────────────────────────────────────────────────────

class SavedQueryListCreateView(BaseAPIView):
    @auth_guard()
    def get(self, request):
        queries = SavedQueryService().list(request.org)
        return self.success(SavedQuerySerializer(queries, many=True).data)

    @auth_guard()
    @require_role('analyst')
    @validate_request(CreateSavedQuerySerializer)
    def post(self, request, data):
        query = SavedQueryService().create(request.org, request.jwt_user, data)
        return self.success(SavedQuerySerializer(query).data, code=sc.CREATED)


class SavedQueryDetailView(BaseAPIView):
    @auth_guard()
    def get(self, request, query_uuid):
        query = SavedQueryService().get(request.org, query_uuid)
        return self.success(SavedQuerySerializer(query).data)

    @auth_guard()
    @require_role('analyst')
    def delete(self, request, query_uuid):
        SavedQueryService().delete(request.org, query_uuid)
        return self.no_content()
