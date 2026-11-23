from sqlalchemy.orm import Session
from sqlalchemy import select
from .models import Event
from .schemas import EventCreate
from .exceptions import (
    EventNotFoundError, EventCapacityError, InvalidRegistrationError
)
from .logger import logger

class EventService:
    """Содержит бизнес-логику управления мероприятиями."""

    def __init__(self, db: Session):
        self.db = db

    def list_events(self):
        return list(self.db.scalars(select(Event).order_by(Event.event_date)).all())

    def get_event(self, event_id: int):
        event = self.db.get(Event, event_id)
        if event is None:
            raise EventNotFoundError(f"Мероприятие с ID {event_id} не найдено")
        return event

    def create_event(self, data: EventCreate):
        event = Event(**data.model_dump())
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)
        logger.info("Создано мероприятие id=%s title=%s", event.id, event.title)
        return event

    def update_event(self, event_id: int, data: EventCreate):
        event = self.get_event(event_id)
        for key, value in data.model_dump().items():
            setattr(event, key, value)
        if event.registered_count > event.max_attendees:
            raise EventCapacityError("Новый лимит меньше числа зарегистрированных участников")
        self.db.commit()
        self.db.refresh(event)
        logger.info("Обновлено мероприятие id=%s", event.id)
        return event

    def delete_event(self, event_id: int):
        event = self.get_event(event_id)
        self.db.delete(event)
        self.db.commit()
        logger.info("Удалено мероприятие id=%s", event_id)

    def change_registration(self, event_id: int, delta: int):
        if delta not in (-1, 1):
            raise InvalidRegistrationError("Изменение должно быть равно +1 или -1")
        event = self.get_event(event_id)
        new_count = event.registered_count + delta
        if new_count < 0:
            raise InvalidRegistrationError("Число участников не может быть отрицательным")
        if new_count > event.max_attendees:
            raise EventCapacityError("Достигнут лимит участников")
        event.registered_count = new_count
        self.db.commit()
        self.db.refresh(event)
        logger.info("Изменено число участников мероприятия id=%s: %s",
                    event_id, new_count)
        return event

    def get_statistics(self):
        events = self.list_events()
        return {
            "total": len(events),
            "planned": sum(e.status == "Запланировано" for e in events),
            "in_progress": sum(e.status == "В процессе" for e in events),
            "completed": sum(e.status == "Завершено" for e in events),
            "cancelled": sum(e.status == "Отменено" for e in events),
            "participants": sum(e.registered_count for e in events),
        }
