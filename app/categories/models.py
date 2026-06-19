from sqlalchemy import Boolean
from sqlalchemy import String
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from app.models.base import Base


class Category(Base):

    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(primary_key=True)

    category_code: Mapped[str] = mapped_column(
        String(20),
        unique=True,
        nullable=False
    )

    category_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    description: Mapped[str | None] = mapped_column(nullable=True)

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True
    )
