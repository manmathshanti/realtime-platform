from django.urls import path
from .views import (
    DashboardListCreateView, DashboardOverviewView, DashboardTemplateListView,
    DashboardDetailView, DashboardShareView, PublicDashboardView,
    WidgetListCreateView, WidgetDetailView, WidgetDataView,
    SavedQueryListCreateView, SavedQueryDetailView,
)

urlpatterns = [
    path('', DashboardListCreateView.as_view(), name='dashboard-list'),
    path('overview/', DashboardOverviewView.as_view(), name='dashboard-overview'),
    path('templates/', DashboardTemplateListView.as_view(), name='dashboard-template-list'),
    path('<str:dashboard_uuid>/', DashboardDetailView.as_view(), name='dashboard-detail'),
    path('<str:dashboard_uuid>/share/', DashboardShareView.as_view(), name='dashboard-share'),

    # Widgets
    path('<str:dashboard_uuid>/widgets/', WidgetListCreateView.as_view(), name='widget-list'),
    path('<str:dashboard_uuid>/widgets/<str:widget_uuid>/', WidgetDetailView.as_view(), name='widget-detail'),
    path('<str:dashboard_uuid>/widgets/<str:widget_uuid>/data/', WidgetDataView.as_view(), name='widget-data'),

    # Public (no auth)
    path('public/<str:token>/', PublicDashboardView.as_view(), name='dashboard-public'),

    # Saved Queries
    path('queries/', SavedQueryListCreateView.as_view(), name='saved-query-list'),
    path('queries/<str:query_uuid>/', SavedQueryDetailView.as_view(), name='saved-query-detail'),
]
