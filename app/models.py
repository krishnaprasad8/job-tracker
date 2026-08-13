"""SQLAlchemy models for the job application tracker."""

import enum
from datetime import date, datetime

from sqlalchemy import Date, DateTime, Enum, Integer, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Parent class for all models. SQLAlchemy uses it to track every table."""


class ApplicationStatus(str, enum.Enum):
    # Subclassing str as well as Enum makes members compare equal to their
    # string value, which keeps the API layer simple in step 3.
    APPLIED = "applied"
    INTERVIEW = "interview"
    OFFER = "offer"
    REJECTED = "rejected"


class Application(Base):
    __tablename__ = "applications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    company_name: Mapped[str] = mapped_column(String(200), nullable=False)
    role_title: Mapped[str] = mapped_column(String(200), nullable=False)

    status: Mapped[ApplicationStatus] = mapped_column(
        Enum(
            ApplicationStatus,
            name="application_status",
            # Store the lowercase values ("applied") rather than the member
            # names ("APPLIED"), which is SQLAlchemy's default.
            values_callable=lambda enum_cls: [m.value for m in enum_cls],
        ),
        nullable=False,
        default=ApplicationStatus.APPLIED,
    )

    applied_date: Mapped[date] = mapped_column(Date, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # server_default lets PostgreSQL set the timestamp itself, so rows written
    # by anything other than this app still get correct values.
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        return (
            f"<Application id={self.id} company={self.company_name!r} "
            f"role={self.role_title!r} status={self.status}>"
        )
