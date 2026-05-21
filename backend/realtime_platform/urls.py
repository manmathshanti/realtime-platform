from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse


def health_check(request):
    return JsonResponse({'status': 'ok', 'service': 'realtime-platform'})


urlpatterns = [
    path('admin/', admin.site.urls),
    path('health/', health_check, name='health_check'),
    path('api/v1/auth/', include('apps.accounts.urls.auth_urls')),
    path('api/v1/org/', include('apps.accounts.urls.org_urls')),
    path('api/v1/api-keys/', include('apps.accounts.urls.apikey_urls')),
    path('api/v1/ingest/', include('apps.ingestion.urls')),
    path('api/v1/dashboards/', include('apps.dashboards.urls')),
    path('api/v1/alerts/', include('apps.alerts.urls')),
]
