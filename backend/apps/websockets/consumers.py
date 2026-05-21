import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async

logger = logging.getLogger(__name__)


class BaseAuthConsumer(AsyncWebsocketConsumer):
    """Base consumer that enforces JWT authentication."""

    @database_sync_to_async
    def get_membership(self, user, org_id: int):
        from apps.accounts.models import OrganizationMembership
        return OrganizationMembership.objects.filter(
            user=user, organization_id=org_id, is_active=True
        ).select_related('organization').first()

    async def websocket_connect(self, message):
        user = self.scope.get('user')
        if not user or not user.is_authenticated:
            await self.close(code=4001)
            return
        await super().websocket_connect(message)

    async def send_json(self, content: dict):
        await self.send(text_data=json.dumps(content))

    async def send_error(self, message: str, code: int = 4000):
        await self.send_json({'type': 'error', 'message': message, 'code': code})


class DashboardConsumer(BaseAuthConsumer):
    """
    Live dashboard updates.
    Connect: ws://.../ws/dashboards/<dashboard_uuid>/
    Receives event.new messages and pushes them to the client.
    """

    async def connect(self):
        user = self.scope.get('user')
        if not user or not user.is_authenticated:
            await self.close(code=4001)
            return

        self.dashboard_uuid = self.scope['url_route']['kwargs']['dashboard_uuid']
        self.group_name = f'dashboard_{self.dashboard_uuid}'

        dashboard = await self.get_dashboard(self.dashboard_uuid, user)
        if not dashboard:
            await self.close(code=4004)
            return

        self.org_id = dashboard.organization_id
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.channel_layer.group_add(f'events_{self.org_id}', self.channel_name)
        await self.accept()
        await self.send_json({'type': 'connected', 'dashboard_uuid': self.dashboard_uuid})

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)
        if hasattr(self, 'org_id'):
            await self.channel_layer.group_discard(f'events_{self.org_id}', self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        try:
            data = json.loads(text_data or '{}')
            msg_type = data.get('type')
            if msg_type == 'ping':
                await self.send_json({'type': 'pong'})
        except json.JSONDecodeError:
            await self.send_error('Invalid JSON')

    # ── Channel layer message handlers ─────────────────────────────────────

    async def event_new(self, event):
        """Triggered by ingestion service when a new event arrives."""
        await self.send_json({'type': 'event.new', 'event': event['event']})

    async def dashboard_refresh(self, event):
        """Tells client to re-fetch widget data."""
        await self.send_json({'type': 'dashboard.refresh'})

    @database_sync_to_async
    def get_dashboard(self, dashboard_uuid: str, user):
        from apps.dashboards.models import Dashboard
        from apps.accounts.models import OrganizationMembership

        dashboard = Dashboard.objects.filter(
            uuid=dashboard_uuid, deleted_at__isnull=True
        ).select_related('organization').first()

        if not dashboard:
            return None

        if dashboard.is_public:
            return dashboard

        membership = OrganizationMembership.objects.filter(
            user=user, organization=dashboard.organization, is_active=True
        ).first()
        return dashboard if membership else None


class AlertConsumer(BaseAuthConsumer):
    """
    Real-time alert notifications.
    Connect: ws://.../ws/alerts/
    Receives alert.triggered and alert.notification messages.
    """

    async def connect(self):
        user = self.scope.get('user')
        if not user or not user.is_authenticated:
            await self.close(code=4001)
            return

        membership = await self.get_primary_membership(user)
        if not membership:
            await self.close(code=4003)
            return

        self.org_id = membership.organization_id
        self.group_name = f'alerts_{self.org_id}'
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        await self.send_json({'type': 'connected', 'org_id': self.org_id})

    async def disconnect(self, close_code):
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        try:
            data = json.loads(text_data or '{}')
            if data.get('type') == 'ping':
                await self.send_json({'type': 'pong'})
        except json.JSONDecodeError:
            pass

    async def alert_triggered(self, event):
        await self.send_json({'type': 'alert.triggered', 'alert': event['alert']})

    async def alert_notification(self, event):
        await self.send_json({'type': 'alert.notification', 'data': event['data']})

    @database_sync_to_async
    def get_primary_membership(self, user):
        from apps.accounts.models import OrganizationMembership
        return OrganizationMembership.objects.select_related('organization').filter(
            user=user, is_active=True, organization__is_active=True
        ).first()


class EventStreamConsumer(BaseAuthConsumer):
    """
    Live event stream viewer (tail).
    Connect: ws://.../ws/events/stream/
    Streams new events as they are ingested.
    """

    async def connect(self):
        user = self.scope.get('user')
        if not user or not user.is_authenticated:
            await self.close(code=4001)
            return

        membership = await self.get_primary_membership(user)
        if not membership:
            await self.close(code=4003)
            return

        self.org_id = membership.organization_id
        self.group_name = f'events_{self.org_id}'
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        await self.send_json({'type': 'connected', 'message': 'Streaming events...'})

    async def disconnect(self, close_code):
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        try:
            data = json.loads(text_data or '{}')
            if data.get('type') == 'ping':
                await self.send_json({'type': 'pong'})
        except json.JSONDecodeError:
            pass

    async def event_new(self, event):
        await self.send_json({'type': 'event.new', 'event': event['event']})

    @database_sync_to_async
    def get_primary_membership(self, user):
        from apps.accounts.models import OrganizationMembership
        return OrganizationMembership.objects.select_related('organization').filter(
            user=user, is_active=True, organization__is_active=True
        ).first()
