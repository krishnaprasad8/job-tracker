"""Pydantic schemas describing what goes in and out over HTTP."""

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from models import ApplicationStatus


class ApplicationCreate(BaseModel):
    company_name: str = Field(min_length=1, max_length=200)
    role_title: str = Field(min_length=1, max_length=200)
    applied_date: date
    status: ApplicationStatus = ApplicationStatus.APPLIED
    notes: str | None = None


class ApplicationUpdate(BaseModel):
    """Every field optional — PATCH sends only what changed."""

    company_name: str | None = Field(default=None, min_length=1, max_length=200)
    role_title: str | None = Field(default=None, min_length=1, max_length=200)
    applied_date: date | None = None
    status: ApplicationStatus | None = None
    notes: str | None = None


class ApplicationRead(BaseModel):
    # from_attributes lets FastAPI build this straight from a SQLAlchemy object
    # instead of requiring a dict.
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_name: str
    role_title: str
    status: ApplicationStatus
    applied_date: date
    notes: str | None
    created_at: datetime
    updated_at: datetime
