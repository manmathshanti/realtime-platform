import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'realtime_platform.settings')

app = Celery('realtime_platform')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

app.conf.beat_schedule = {
    'evaluate-alert-rules': {
        'task': 'apps.alerts.tasks.evaluate_all_alert_rules',
        'schedule': 60.0,  # every 60 seconds
    },
    'resolve-triggered-alerts': {
        'task': 'apps.alerts.tasks.resolve_triggered_alerts',
        'schedule': 120.0,  # every 2 minutes
    },
    'process-scheduled-reports': {
        'task': 'apps.alerts.tasks.process_scheduled_reports',
        'schedule': crontab(minute=0),  # every hour
    },
}
