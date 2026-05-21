from django.urls import path
from .views import (
    AlertRuleListCreateView, AlertRuleDetailView, AlertRuleMuteView,
    AlertHistoryListView,
    NotificationChannelListCreateView, NotificationChannelDetailView,
)

urlpatterns = [
    # Rules
    path('rules/', AlertRuleListCreateView.as_view(), name='alert-rule-list'),
    path('rules/<str:rule_uuid>/', AlertRuleDetailView.as_view(), name='alert-rule-detail'),
    path('rules/<str:rule_uuid>/mute/', AlertRuleMuteView.as_view(), name='alert-rule-mute'),

    # History
    path('history/', AlertHistoryListView.as_view(), name='alert-history'),

    # Notification Channels
    path('channels/', NotificationChannelListCreateView.as_view(), name='notification-channel-list'),
    path('channels/<str:channel_uuid>/', NotificationChannelDetailView.as_view(), name='notification-channel-detail'),
]
