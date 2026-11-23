from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, field_validator

ALLOWED_STATUSES = {"Запланировано", "В процессе", "Завершено", "Отменено"}

class EventCreate(BaseModel):
    title: str = Field(min_length=2, max_length=120)
    description: str = Field(default="", max_length=2000)
    location: str = Field(min_length=2, max_length=200)
    event_date: datetime
    status: str = "Запланировано"
    max_attendees: int = Field(default=100, ge=1, le=100000)

    @field_validator("status")
    @classmethod
    def validate_status(cls, value):
        if value not in ALLOWED_STATUSES:
            raise ValueError("Недопустимый статус мероприятия")
        return value

class EventUpdate(EventCreate):
    pass

class EventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    description: str
    location: str
    event_date: datetime
    status: str
    max_attendees: int
    registered_count: int
    created_at: datetime
