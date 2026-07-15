from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Incident(Base):
    __tablename__ = "sre_incidents"

    id: Mapped[int] = mapped_column(primary_key=True)
    case_no: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    subject: Mapped[str] = mapped_column(String(220), index=True)
    description: Mapped[str | None] = mapped_column(Text)
    category: Mapped[str] = mapped_column(String(60), index=True)
    priority: Mapped[str] = mapped_column(String(20), default="Medium", index=True)
    status: Mapped[str] = mapped_column(String(30), default="Open", index=True)
    room_no: Mapped[str | None] = mapped_column(String(30), index=True)
    hotel_area: Mapped[str | None] = mapped_column(String(100))
    guest_name: Mapped[str | None] = mapped_column(String(150))
    guest_mobile: Mapped[str | None] = mapped_column(String(30))
    created_by: Mapped[int | None] = mapped_column(Integer)
    created_by_name: Mapped[str | None] = mapped_column(String(150))
    assigned_to: Mapped[int | None] = mapped_column(Integer)
    assigned_to_name: Mapped[str | None] = mapped_column(String(150))
    closed_by: Mapped[int | None] = mapped_column(Integer)
    assigned_at: Mapped[datetime | None] = mapped_column(DateTime)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    attachments = relationship("IncidentAttachment", cascade="all, delete-orphan", back_populates="incident")
    comments = relationship("IncidentComment", cascade="all, delete-orphan", back_populates="incident")
    history = relationship("IncidentHistory", cascade="all, delete-orphan", back_populates="incident")


class IncidentAttachment(Base):
    __tablename__ = "sre_incident_attachments"
    id: Mapped[int] = mapped_column(primary_key=True)
    incident_id: Mapped[int] = mapped_column(ForeignKey("sre_incidents.id", ondelete="CASCADE"), index=True)
    file_name: Mapped[str] = mapped_column(String(255))
    original_name: Mapped[str] = mapped_column(String(255))
    file_size: Mapped[int] = mapped_column(Integer, default=0)
    mime_type: Mapped[str | None] = mapped_column(String(100))
    uploaded_by: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    incident = relationship("Incident", back_populates="attachments")


class IncidentComment(Base):
    __tablename__ = "sre_incident_comments"
    id: Mapped[int] = mapped_column(primary_key=True)
    incident_id: Mapped[int] = mapped_column(ForeignKey("sre_incidents.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[int | None] = mapped_column(Integer)
    user_name: Mapped[str] = mapped_column(String(150))
    comment: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    incident = relationship("Incident", back_populates="comments")


class IncidentHistory(Base):
    __tablename__ = "sre_incident_history"
    id: Mapped[int] = mapped_column(primary_key=True)
    incident_id: Mapped[int] = mapped_column(ForeignKey("sre_incidents.id", ondelete="CASCADE"), index=True)
    old_status: Mapped[str | None] = mapped_column(String(30))
    new_status: Mapped[str] = mapped_column(String(30))
    changed_by: Mapped[int | None] = mapped_column(Integer)
    changed_by_name: Mapped[str | None] = mapped_column(String(150))
    remarks: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    incident = relationship("Incident", back_populates="history")
