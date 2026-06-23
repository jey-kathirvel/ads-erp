from datetime import datetime

from sqlalchemy import DateTime
from sqlalchemy import String
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from app.models.base import Base


class Unit(Base):

    __tablename__ = "units"

    id: Mapped[int] = mapped_column(primary_key=True)

    unit_code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)

    unit_name: Mapped[str] = mapped_column(String(100), nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
