# Job Application Tracker

A REST API for tracking job applications through their lifecycle — applied,
interview, offer, rejected. Built with FastAPI and PostgreSQL, running in
Docker.

Replaces the spreadsheet I was keeping by hand.

## Stack

- **Python 3.12** / **FastAPI** — API and automatic OpenAPI docs
- **PostgreSQL 17** — storage, with a database-level enum for status
- **SQLAlchemy 2.0** — ORM, using the modern `Mapped` / `mapped_column` style
- **Pydantic v2** — request/response validation
- **Docker Compose** — app and database as containers

## Quick start

Requires Docker.

```bash
git clone https://github.com/krishnaprasad8/job-tracker.git
cd job-tracker
cp .env.example .env
docker compose up --build
```

Then open **http://localhost:8000/docs** for the interactive API docs.

The database schema is created automatically on first start. Data persists in a
named Docker volume, so `docker compose down` and back up keeps your records.

To stop:

```bash
docker compose down      # keeps data
docker compose down -v   # also deletes the volume and all data
```

## Running without Docker

Requires Python 3.12 and a local PostgreSQL 17.

```bash
python3.12 -m venv venv
./venv/bin/pip install -r requirements.txt
createdb job_tracker
cp .env.example .env        # then set DATABASE_URL to your local database
./venv/bin/uvicorn main:app --reload
```

## API

| Method | Endpoint | Description |
| --- | --- | --- |
| `POST` | `/applications` | Create an application. Returns `201`. |
| `GET` | `/applications` | List all, newest `applied_date` first. |
| `GET` | `/applications/{id}` | Fetch one. `404` if not found. |
| `PATCH` | `/applications/{id}` | Partial update — send only changed fields. |
| `DELETE` | `/applications/{id}` | Delete. Returns `204`. |

Example:

```bash
curl -X POST localhost:8000/applications \
  -H 'Content-Type: application/json' \
  -d '{
        "company_name": "Example Ltd",
        "role_title": "Platform Engineer",
        "applied_date": "2026-08-13",
        "notes": "Applied via careers page"
      }'
```

Update is a genuine PATCH — `{"status": "interview"}` changes the status and
leaves every other field untouched.

## Running the tests

```bash
./venv/bin/pip install -r requirements-dev.txt
./venv/bin/pytest
```

20 tests covering all five endpoints: response codes, status defaulting, the
optional `notes` field, sort order, partial-update semantics, timestamp
behaviour, and validation failures (`404` on unknown ids, `422` on an invalid
status, a missing `applied_date` or an empty company name).

Tests run against a real PostgreSQL database rather than SQLite — `status` is a
native Postgres enum, so SQLite would not exercise the same constraints. A
`job_tracker_test` database is created automatically on first run and truncated
between tests.

## Data model

Single `applications` table:

| Field | Type | Notes |
| --- | --- | --- |
| `id` | integer | Primary key, assigned by Postgres |
| `company_name` | varchar(200) | Required |
| `role_title` | varchar(200) | Required |
| `status` | enum | `applied` / `interview` / `offer` / `rejected`, defaults to `applied` |
| `applied_date` | date | Required |
| `notes` | text | Optional, the only nullable field |
| `created_at` | timestamptz | Set by Postgres on insert |
| `updated_at` | timestamptz | Refreshed by Postgres on every update |

`status` is a real PostgreSQL enum type, so invalid values are rejected by the
database, not just by the application.

## Project structure

```
models.py     SQLAlchemy model and status enum
schemas.py    Pydantic schemas for requests and responses
database.py   Engine, session factory, per-request session dependency
main.py       FastAPI app and the five endpoints
```

## Status and roadmap

Working: full CRUD against PostgreSQL, containerised, data persisting across
container rebuilds.

- [x] SQLAlchemy models
- [x] PostgreSQL connection
- [x] CRUD endpoints
- [x] Docker and Docker Compose
- [x] Automated tests
- [ ] VPS deployment behind Nginx
- [ ] Alembic migrations
- [ ] Authentication and per-user applications
- [ ] Web frontend

**Deliberately not built yet:** there is no authentication, and applications
are not scoped to a user — anyone with access to the API can read and modify
every record. That is fine for local single-user use, and is the next thing to
address before the app is shared.

Tables are currently created with `create_all` on startup, which creates
missing tables but cannot alter existing ones. Alembic is planned before any
real data is deployed.
