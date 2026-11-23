from datetime import datetime, timedelta
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.database import Base
from app.schemas import EventCreate
from app.services import EventService
from app.exceptions import (
    EventNotFoundError, EventCapacityError, InvalidRegistrationError
)

@pytest.fixture
def db():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)
    session = TestingSession()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)

def sample_event(**kwargs):
    data = {
        "title": "Тестовая конференция",
        "description": "Описание",
        "location": "Москва",
        "event_date": datetime.now() + timedelta(days=2),
        "status": "Запланировано",
        "max_attendees": 10,
    }
    data.update(kwargs)
    return EventCreate(**data)

def test_create_and_list_event(db):
    service = EventService(db)
    created = service.create_event(sample_event())
    assert created.id is not None
    assert len(service.list_events()) == 1

def test_registration_changes_count(db):
    service = EventService(db)
    event = service.create_event(sample_event())
    updated = service.change_registration(event.id, 1)
    assert updated.registered_count == 1
    updated = service.change_registration(event.id, -1)
    assert updated.registered_count == 0

def test_capacity_limit(db):
    service = EventService(db)
    event = service.create_event(sample_event(max_attendees=1))
    service.change_registration(event.id, 1)
    with pytest.raises(EventCapacityError):
        service.change_registration(event.id, 1)

def test_registration_cannot_be_negative(db):
    service = EventService(db)
    event = service.create_event(sample_event())
    with pytest.raises(InvalidRegistrationError):
        service.change_registration(event.id, -1)

def test_missing_event(db):
    with pytest.raises(EventNotFoundError):
        EventService(db).get_event(999)

def test_statistics(db):
    service = EventService(db)
    service.create_event(sample_event())
    stats = service.get_statistics()
    assert stats["total"] == 1
    assert stats["planned"] == 1
