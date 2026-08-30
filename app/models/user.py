from __future__ import annotations
import enum
from datetime import datetime
from sqlalchemy import String, Enum, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class UserRole(str, enum.Enum):
    citizen = "citizen"
    validator = "validator"
    authority = "authority"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    fcm_token: Mapped[str | None] = mapped_column(String(512), nullable=True)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="userrole"), nullable=False, default=UserRole.citizen
    )
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Explicit foreign_keys to resolve ambiguity (Report has two FKs to users)
    reports: Mapped[list["Report"]] = relationship(  # noqa: F821
        back_populates="reporter",
        foreign_keys="[Report.user_id]",
        lazy="select",
    )
    validated_reports: Mapped[list["Report"]] = relationship(  # noqa: F821
        back_populates="validator",
        foreign_keys="[Report.validated_by_id]",
        lazy="select",
    )
    alerts_sent: Mapped[list["Alert"]] = relationship(  # noqa: F821
        back_populates="authority",
        lazy="select",
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email} role={self.role}>"