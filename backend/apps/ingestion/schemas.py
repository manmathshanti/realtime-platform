from datetime import datetime
from typing import Any, Optional

from django.utils import timezone
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

from common.exceptions import ValidationException


class EventIn(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    event_name: str = Field(..., min_length=1, max_length=255)
    properties: dict[str, Any] = Field(default_factory=dict)
    timestamp: Optional[datetime] = None

    @field_validator('timestamp')
    @classmethod
    def validate_timestamp(cls, value: Optional[datetime]) -> Optional[datetime]:
        if value and value > timezone.now():
            raise ValueError('Timestamp cannot be in the future.')
        return value

    def normalized(self) -> dict[str, Any]:
        return {
            'event_name': self.event_name,
            'properties': self.properties,
            'timestamp': self.timestamp or timezone.now(),
        }


def validate_event_payload(payload: dict[str, Any]) -> dict[str, Any]:
    try:
        return EventIn.model_validate(payload).normalized()
    except ValidationError as exc:
        raise ValidationException(exc.errors()[0]['msg'])


def validate_batch_payload(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    try:
        return [EventIn.model_validate(item).normalized() for item in events]
    except ValidationError as exc:
        raise ValidationException(exc.errors()[0]['msg'])
