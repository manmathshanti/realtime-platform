from typing import Optional

from common.repositories.base_repository import BaseRepository
from .models import Dashboard, Widget, SavedQuery


class DashboardRepository(BaseRepository):
    def __init__(self):
        super().__init__(Dashboard)

    def get_org_dashboards(self, org_id: int):
        return self.model.objects.filter(
            organization_id=org_id, deleted_at__isnull=True
        ).select_related('created_by').order_by('-created_at')

    def get_by_uuid_and_org(self, dashboard_uuid: str, org_id: int) -> Optional[Dashboard]:
        return self.model.objects.filter(
            uuid=dashboard_uuid, organization_id=org_id, deleted_at__isnull=True
        ).prefetch_related('widgets').first()

    def get_by_share_token(self, token: str) -> Optional[Dashboard]:
        return self.model.objects.filter(
            share_token=token, is_public=True, deleted_at__isnull=True
        ).prefetch_related('widgets').first()


class WidgetRepository(BaseRepository):
    def __init__(self):
        super().__init__(Widget)

    def get_dashboard_widgets(self, dashboard_id: int):
        return self.model.objects.filter(
            dashboard_id=dashboard_id, deleted_at__isnull=True
        ).select_related('saved_query').order_by('position_y', 'position_x')

    def get_by_uuid_and_dashboard(self, widget_uuid: str, dashboard_id: int) -> Optional[Widget]:
        return self.model.objects.filter(
            uuid=widget_uuid, dashboard_id=dashboard_id, deleted_at__isnull=True
        ).first()


class SavedQueryRepository(BaseRepository):
    def __init__(self):
        super().__init__(SavedQuery)

    def get_org_queries(self, org_id: int):
        return self.model.objects.filter(
            organization_id=org_id, deleted_at__isnull=True
        ).order_by('-created_at')

    def get_by_uuid_and_org(self, query_uuid: str, org_id: int) -> Optional[SavedQuery]:
        return self.model.objects.filter(
            uuid=query_uuid, organization_id=org_id, deleted_at__isnull=True
        ).first()
