"""FastAPI application exposing CRUD endpoints for job applications."""

from fastapi import Depends, FastAPI, HTTPException, Response, status
from sqlalchemy import select, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Application
from app.schemas import ApplicationCreate, ApplicationRead, ApplicationUpdate

app = FastAPI(title="Job Application Tracker")


@app.get("/health")
def health(response: Response, db: Session = Depends(get_db)) -> dict[str, str]:
    """Liveness probe for Nginx, uptime monitoring and orchestrators.

    Queries the database rather than returning a constant, so it reports
    unhealthy when the process is fine but its database is unreachable.
    """
    try:
        db.execute(text("SELECT 1"))
    except SQLAlchemyError:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "unhealthy"}
    return {"status": "ok"}


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
