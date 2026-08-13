"""FastAPI application exposing CRUD endpoints for job applications."""

from fastapi import Depends, FastAPI, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Application
from app.schemas import ApplicationCreate, ApplicationRead, ApplicationUpdate

app = FastAPI(title="Job Application Tracker")


def _get_or_404(db: Session, application_id: int) -> Application:
    application = db.get(Application, application_id)
    if application is None:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, f"Application {application_id} not found"
        )
    return application


@app.post(
    "/applications",
    response_model=ApplicationRead,
    status_code=status.HTTP_201_CREATED,
)
def create_application(
    payload: ApplicationCreate, db: Session = Depends(get_db)
) -> Application:
    application = Application(**payload.model_dump())
    db.add(application)
    db.commit()
    # refresh pulls back the values Postgres filled in: id and both timestamps.
    db.refresh(application)
    return application


@app.get("/applications", response_model=list[ApplicationRead])
def list_applications(db: Session = Depends(get_db)) -> list[Application]:
    stmt = select(Application).order_by(
        Application.applied_date.desc(), Application.id.desc()
    )
    return list(db.scalars(stmt))


@app.get("/applications/{application_id}", response_model=ApplicationRead)
def get_application(
    application_id: int, db: Session = Depends(get_db)
) -> Application:
    return _get_or_404(db, application_id)


@app.patch("/applications/{application_id}", response_model=ApplicationRead)
def update_application(
    application_id: int,
    payload: ApplicationUpdate,
    db: Session = Depends(get_db),
) -> Application:
    application = _get_or_404(db, application_id)
    # exclude_unset means fields the caller didn't send are left untouched,
    # which is what makes this a PATCH rather than a full replace.
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(application, field, value)
    db.commit()
    db.refresh(application)
    return application


@app.delete(
    "/applications/{application_id}", status_code=status.HTTP_204_NO_CONTENT
)
def delete_application(
    application_id: int, db: Session = Depends(get_db)
) -> None:
    application = _get_or_404(db, application_id)
    db.delete(application)
    db.commit()
