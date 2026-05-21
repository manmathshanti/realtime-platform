import logging
from datetime import timedelta
from django.utils import timezone
from django.core.cache import cache

from common.service.base_service import BaseService
from common.exceptions import NotFoundException, ForbiddenException, ValidationException

from apps.accounts.models import Organization, User
from .models import Dashboard, Widget, SavedQuery
from .repositories import DashboardRepository, WidgetRepository, SavedQueryRepository

logger = logging.getLogger(__name__)

QUERY_CACHE_TTL = 120  # seconds


class DashboardService(BaseService):
    def __init__(self):
        self.repo = DashboardRepository()
        self.widget_repo = WidgetRepository()
        self.query_repo = SavedQueryRepository()

    def list_dashboards(self, org: Organization):
        return self.repo.get_org_dashboards(org.id)

    def get_dashboard(self, org: Organization, dashboard_uuid: str) -> Dashboard:
        dashboard = self.repo.get_by_uuid_and_org(dashboard_uuid, org.id)
        if not dashboard:
            raise NotFoundException('Dashboard not found.')
        return dashboard

    def get_public_dashboard(self, token: str) -> Dashboard:
        dashboard = self.repo.get_by_share_token(token)
        if not dashboard:
            raise NotFoundException('Public dashboard not found or link is invalid.')
        return dashboard

    def create_dashboard(self, org: Organization, user: User, data: dict) -> Dashboard:
        return self.repo.create({
            'organization': org,
            'created_by': user,
            'name': data['name'],
            'description': data.get('description', ''),
            'refresh_interval': data.get('refresh_interval', 0),
        })

    def update_dashboard(self, org: Organization, dashboard_uuid: str, data: dict) -> Dashboard:
        dashboard = self.get_dashboard(org, dashboard_uuid)
        updatable = ['name', 'description', 'refresh_interval', 'layout']
        for field in updatable:
            if field in data:
                setattr(dashboard, field, data[field])
        dashboard.save(update_fields=[f for f in updatable if f in data] + ['updated_at'])
        return dashboard

    def delete_dashboard(self, org: Organization, dashboard_uuid: str):
        dashboard = self.get_dashboard(org, dashboard_uuid)
        dashboard.deleted_at = timezone.now()
        dashboard.save(update_fields=['deleted_at', 'updated_at'])

    def enable_sharing(self, org: Organization, dashboard_uuid: str) -> str:
        dashboard = self.get_dashboard(org, dashboard_uuid)
        return dashboard.generate_share_token()

    def disable_sharing(self, org: Organization, dashboard_uuid: str):
        dashboard = self.get_dashboard(org, dashboard_uuid)
        dashboard.revoke_share_token()

    def get_overview(self, org: Organization) -> dict:
        from django.db.models import Count
        from apps.ingestion.models import Event
        from apps.alerts.models import AlertRule, AlertHistory, AlertStatusChoices

        now = timezone.now()
        day_ago = now - timedelta(hours=24)

        total_events = Event.objects.filter(organization=org).count()
        events_last_24h = Event.objects.filter(organization=org, timestamp__gte=day_ago).count()
        dashboards_count = Dashboard.objects.filter(organization=org, deleted_at__isnull=True).count()
        active_alerts = AlertRule.objects.filter(
            organization=org,
            deleted_at__isnull=True,
            status__in=[AlertStatusChoices.ACTIVE, AlertStatusChoices.TRIGGERED],
        ).count()
        top_events = list(
            Event.objects.filter(organization=org, timestamp__gte=day_ago)
            .values('event_name')
            .annotate(count=Count('id'))
            .order_by('-count', 'event_name')[:5]
        )
        recent_alerts = list(
            AlertHistory.objects.filter(organization=org)
            .select_related('alert_rule')
            .order_by('-created_at')[:5]
            .values('uuid', 'triggered_value', 'message', 'created_at', 'alert_rule__name')
        )

        return {
            'organization': {
                'uuid': str(org.uuid),
                'name': org.name,
                'slug': org.slug,
            },
            'kpis': {
                'total_events': total_events,
                'events_last_24h': events_last_24h,
                'dashboards': dashboards_count,
                'active_alerts': active_alerts,
            },
            'top_events': top_events,
            'recent_alerts': [
                {
                    'uuid': str(item['uuid']),
                    'rule_name': item['alert_rule__name'],
                    'triggered_value': item['triggered_value'],
                    'message': item['message'],
                    'created_at': item['created_at'].isoformat(),
                }
                for item in recent_alerts
            ],
        }

    def get_templates(self) -> list[dict]:
        return [
            {
                'id': 'web-analytics',
                'name': 'Web Analytics',
                'description': 'Traffic, page views, top events, and acquisition trends.',
                'widgets': ['line_chart', 'bar_chart', 'kpi_card', 'table'],
            },
            {
                'id': 'sales-pipeline',
                'name': 'Sales Pipeline',
                'description': 'Track conversion events, revenue checkpoints, and campaign wins.',
                'widgets': ['kpi_card', 'bar_chart', 'pie_chart', 'table'],
            },
            {
                'id': 'devops-health',
                'name': 'DevOps Health',
                'description': 'Monitor deploy events, error spikes, and incident response signals.',
                'widgets': ['line_chart', 'kpi_card', 'table', 'pie_chart'],
            },
        ]


class WidgetService(BaseService):
    def __init__(self):
        self.repo = WidgetRepository()
        self.dashboard_repo = DashboardRepository()
        self.query_repo = SavedQueryRepository()

    def _get_dashboard(self, org: Organization, dashboard_uuid: str) -> Dashboard:
        dashboard = self.dashboard_repo.get_by_uuid_and_org(dashboard_uuid, org.id)
        if not dashboard:
            raise NotFoundException('Dashboard not found.')
        return dashboard

    def list_widgets(self, org: Organization, dashboard_uuid: str):
        dashboard = self._get_dashboard(org, dashboard_uuid)
        return self.repo.get_dashboard_widgets(dashboard.id)

    def create_widget(self, org: Organization, dashboard_uuid: str, data: dict) -> Widget:
        dashboard = self._get_dashboard(org, dashboard_uuid)
        saved_query = None
        if data.get('saved_query_uuid'):
            saved_query = self.query_repo.get_by_uuid_and_org(str(data['saved_query_uuid']), org.id)
            if not saved_query:
                raise NotFoundException('Saved query not found.')

        return self.repo.create({
            'dashboard': dashboard,
            'saved_query': saved_query,
            'title': data['title'],
            'widget_type': data['widget_type'],
            'config': data.get('config', {}),
            'position_x': data.get('position_x', 0),
            'position_y': data.get('position_y', 0),
            'width': data.get('width', 4),
            'height': data.get('height', 3),
        })

    def update_widget(self, org: Organization, dashboard_uuid: str, widget_uuid: str, data: dict) -> Widget:
        dashboard = self._get_dashboard(org, dashboard_uuid)
        widget = self.repo.get_by_uuid_and_dashboard(widget_uuid, dashboard.id)
        if not widget:
            raise NotFoundException('Widget not found.')
        updatable = ['title', 'config', 'position_x', 'position_y', 'width', 'height']
        for field in updatable:
            if field in data:
                setattr(widget, field, data[field])
        widget.save(update_fields=[f for f in updatable if f in data] + ['updated_at'])
        return widget

    def delete_widget(self, org: Organization, dashboard_uuid: str, widget_uuid: str):
        dashboard = self._get_dashboard(org, dashboard_uuid)
        widget = self.repo.get_by_uuid_and_dashboard(widget_uuid, dashboard.id)
        if not widget:
            raise NotFoundException('Widget not found.')
        widget.deleted_at = timezone.now()
        widget.save(update_fields=['deleted_at', 'updated_at'])

    def execute_widget_query(self, org: Organization, dashboard_uuid: str, widget_uuid: str) -> dict:
        dashboard = self._get_dashboard(org, dashboard_uuid)
        widget = self.repo.get_by_uuid_and_dashboard(widget_uuid, dashboard.id)
        if not widget:
            raise NotFoundException('Widget not found.')
        if not widget.saved_query:
            return {'data': [], 'widget_type': widget.widget_type, 'title': widget.title}

        cache_key = f'widget_data:{widget.id}:{widget.saved_query.time_range}'
        cached = cache.get(cache_key)
        if cached:
            return cached

        result = self._run_query(org, widget.saved_query)
        result['widget_type'] = widget.widget_type
        result['title'] = widget.title
        cache.set(cache_key, result, QUERY_CACHE_TTL)
        return result

    def _run_query(self, org: Organization, query: SavedQuery) -> dict:
        from django.db.models.functions import Trunc
        from django.db.models import Count
        from apps.ingestion.models import Event

        now = timezone.now()
        time_range_map = {
            '1h': timedelta(hours=1),
            '24h': timedelta(hours=24),
            '7d': timedelta(days=7),
            '30d': timedelta(days=30),
            '90d': timedelta(days=90),
        }
        delta = time_range_map.get(query.time_range, timedelta(days=7))
        from_ts = now - delta

        qs = Event.objects.filter(
            organization=org,
            event_name=query.event_name,
            timestamp__gte=from_ts,
            timestamp__lte=now,
        )

        data = list(
            qs.annotate(bucket=Trunc('timestamp', query.interval))
            .values('bucket')
            .annotate(count=Count('id'))
            .order_by('bucket')
            .values('bucket', 'count')
        )

        return {
            'data': [{'bucket': row['bucket'].isoformat(), 'value': row['count']} for row in data],
            'from_ts': from_ts.isoformat(),
            'to_ts': now.isoformat(),
            'event_name': query.event_name,
        }


class SavedQueryService(BaseService):
    def __init__(self):
        self.repo = SavedQueryRepository()

    def list(self, org: Organization):
        return self.repo.get_org_queries(org.id)

    def create(self, org: Organization, user: User, data: dict) -> SavedQuery:
        return self.repo.create({
            'organization': org,
            'created_by': user,
            'name': data['name'],
            'event_name': data['event_name'],
            'aggregation': data.get('aggregation', 'count'),
            'group_by': data.get('group_by', ''),
            'filters': data.get('filters', {}),
            'time_range': data.get('time_range', '7d'),
            'interval': data.get('interval', 'hour'),
        })

    def get(self, org: Organization, query_uuid: str) -> SavedQuery:
        q = self.repo.get_by_uuid_and_org(query_uuid, org.id)
        if not q:
            raise NotFoundException('Saved query not found.')
        return q

    def delete(self, org: Organization, query_uuid: str):
        q = self.get(org, query_uuid)
        q.deleted_at = timezone.now()
        q.save(update_fields=['deleted_at', 'updated_at'])
