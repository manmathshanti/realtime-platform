from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from common.exceptions import ValidationException

from .schemas import validate_batch_payload, validate_event_payload


class EventSchemaValidationTests(TestCase):
    def test_single_event_defaults_timestamp(self):
        payload = validate_event_payload({'event_name': 'page_view', 'properties': {'path': '/'}})
        self.assertEqual(payload['event_name'], 'page_view')
        self.assertIn('timestamp', payload)

    def test_batch_rejects_future_timestamps(self):
        with self.assertRaises(ValidationException):
            validate_batch_payload([
                {
                    'event_name': 'page_view',
                    'timestamp': timezone.now() + timedelta(minutes=5),
                }
            ])
