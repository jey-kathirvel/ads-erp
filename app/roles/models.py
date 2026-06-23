from datetime import datetime

from sqlalchemy import Boolean
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Text

from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from app.models.base import Base

# ----------------------------------------------------
# Roles
# ----------------------------------------------------


class Role(Base):

    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    role_code: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)

    role_name: Mapped[str] = mapped_column(String(100), nullable=False)

    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


# ----------------------------------------------------
# Role Permissions
# ----------------------------------------------------


class RolePermission(Base):

    __tablename__ = "role_permissions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id"), nullable=False)

    module_name: Mapped[str] = mapped_column(String(100), nullable=False)

    can_view: Mapped[bool] = mapped_column(Boolean, default=True)

    can_add: Mapped[bool] = mapped_column(Boolean, default=False)

    can_edit: Mapped[bool] = mapped_column(Boolean, default=False)

    can_delete: Mapped[bool] = mapped_column(Boolean, default=False)
