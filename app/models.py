from datetime import datetime
from sqlalchemy import String, Text, DateTime, Integer, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column
from .database import Base

class Event(Base):
    __tablename__ = "events"
    __table_args__ = (
        CheckConstraint("max_attendees > 0", name="positive_max_attendees"),
        CheckConstraint("registered_count >= 0", name="nonnegative_registered_count"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    location: Mapped[str] = mapped_column(String(200), nullable=False)
    event_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="Запланировано")
    max_attendees: Mapped[int] = mapped_column(Integer, default=100)
    registered_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
