from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/dashboards/(?P<dashboard_uuid>[^/]+)/$', consumers.DashboardConsumer.as_asgi()),
    re_path(r'ws/alerts/$', consumers.AlertConsumer.as_asgi()),
    re_path(r'ws/events/stream/$', consumers.EventStreamConsumer.as_asgi()),
]
