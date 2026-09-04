# Job Application Tracker

[![Tests](https://github.com/krishnaprasad8/job-tracker/actions/workflows/test.yml/badge.svg)](https://github.com/krishnaprasad8/job-tracker/actions/workflows/test.yml)

A REST API for tracking job applications through their lifecycle — applied,
interview, offer, rejected. FastAPI and PostgreSQL, containerised with Docker
Compose, schema managed by Alembic migrations, and tested against a real
database on every pull request.

Replaces the spreadsheet I was keeping by hand.

## Stack

- **Python 3.12** / **FastAPI** — API and automatic OpenAPI docs
- **PostgreSQL 17** — storage, with a database-level enum for status
- **SQLAlchemy 2.0** — ORM, using the modern `Mapped` / `mapped_column` style
- **Pydantic v2** — request/response validation
- **Docker Compose** — app and database as containers
- **Alembic** — versioned schema migrations, applied on container start
- **pytest** — 23 tests against a real Postgres
- **GitHub Actions** — tests and migration drift check on every pull request
- **Prometheus / Grafana** — `/metrics` endpoint with dashboards defined as code

## Quick start

Requires Docker.

```bash
git clone https://github.com/krishnaprasad8/job-tracker.git
cd job-tracker
cp .env.example .env
docker compose up --build
```

Then open **http://localhost:8000/docs** for the interactive API docs.

Database migrations run automatically before the app starts, so a fresh
database builds its own schema. Data persists in a named Docker volume, so
`docker compose down` and back up keeps your records.

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
./venv/bin/uvicorn app.main:app --reload
```

## API

| Method | Endpoint | Description |
| --- | --- | --- |
| `GET` | `/health` | Liveness check. `200` if the database responds, `503` if not. |
| `GET` | `/metrics` | Prometheus metrics. Excluded from the OpenAPI schema. |
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

These also run automatically on every pull request via GitHub Actions, against
a PostgreSQL 17 service container. The workflow additionally runs `alembic
check`, which fails the build if `app/models.py` and the migration files have
drifted apart.

28 tests covering all five CRUD endpoints, the health check and metrics: response
codes, status defaulting, the optional `notes` field, sort order,
partial-update semantics, timestamp behaviour, and validation failures (`404`
on unknown ids, `422` on an invalid status, a missing `applied_date` or an
empty company name). The health check is tested both ways — healthy, and with
the database dependency replaced by one that fails.

Tests run against a real PostgreSQL database rather than SQLite — `status` is a
native Postgres enum, so SQLite would not exercise the same constraints. A
`job_tracker_test` database is created automatically on first run and truncated
between tests.

## Database migrations

Schema changes are managed with Alembic. Migration files live in
`alembic/versions/` and are applied automatically by `entrypoint.sh` when the
container starts, so deploying never needs a separate migration step.

To change the schema: edit `app/models.py`, then generate and apply a migration.

```bash
./venv/bin/alembic revision --autogenerate -m "add salary column"
./venv/bin/alembic upgrade head
```

Always read the generated file before applying it. Autogenerate does not handle
everything — the initial migration needed a manual `DROP TYPE` in `downgrade()`
because Alembic leaves Postgres enum types behind when dropping a table, which
makes a subsequent upgrade fail.

Other useful commands:

```bash
./venv/bin/alembic current       # which version this database is at
./venv/bin/alembic history       # all migrations
./venv/bin/alembic downgrade -1  # undo the last one
```

## Metrics and dashboards

The app exposes Prometheus metrics at `/metrics` — request counts, latency
histograms and response sizes, labelled by endpoint, method and status class.
Paths use the route template (`/applications/{application_id}`) rather than the
literal URL, so the number of series stays bounded.

Prometheus and Grafana run as Compose services behind a profile, so they are
opt-in and the deployed server never runs them:

```bash
docker compose --profile observability up -d
```

- Grafana: **http://localhost:3000** — no login, dashboard under *Job Tracker*
- Prometheus: **http://localhost:9090**

The datasource and the dashboard are provisioned from files in
`observability/`, not configured through the UI, so they are reviewable in
version control and survive the containers being destroyed.

Four panels: request rate by endpoint, 95th percentile latency by endpoint,
responses by status class, and 5xx error rate.

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
app/
  models.py     SQLAlchemy model and status enum
  schemas.py    Pydantic schemas for requests and responses
  database.py   Engine, session factory, per-request session dependency
  main.py       FastAPI app, health check and the five endpoints
tests/
  conftest.py           test database and client fixtures
  test_applications.py  CRUD endpoint tests
  test_health.py        health check tests
  test_metrics.py       metrics endpoint tests
infra/                  Terraform + cloud-init for the Hetzner server
observability/          Prometheus config, Grafana datasource and dashboards
```

## Scope

A complete, locally-runnable API. There is no hosted instance — it runs on your
machine with `docker compose up`.

**Built:**

- CRUD API over PostgreSQL, with status enforced as a database-level enum
- Containerised with Docker Compose; data persists in a named volume
- Schema owned by Alembic migrations, applied automatically on container start
- Health check endpoint that runs a real query against the database
- 28 tests against a real Postgres, run on every pull request by GitHub Actions
- Branch protection on `main` requiring those checks to pass before merge
- **Observability** — Prometheus metrics endpoint, with Prometheus and Grafana
  as an opt-in Compose profile and dashboards defined as code
- **Infrastructure as code** — `infra/` provisions a Hetzner server and
  firewall with Terraform, and cloud-init installs Docker, starts the stack and
  configures Nginx on first boot. `terraform apply` to a live API in about 90
  seconds, `terraform destroy` back to nothing

**Run on demand.** There is no permanently hosted instance. The server is
created when needed and destroyed afterwards, so it costs nothing at rest —
a deliberate choice for a personal project, at the price of a new IP address
on each rebuild. See [`infra/README.md`](infra/README.md).

**Deliberately out of scope:**

- **HTTPS.** Certbot needs a domain pointed at a stable address, which the
  on-demand setup does not provide. Demos run over plain HTTP.
- **Authentication.** There is no login, and applications are not scoped to a
  user, so anyone with API access can read and modify every record. Acceptable
  for single-user use; would need solving before hosting permanently.
- **Frontend.** The API is used through the generated docs at `/docs`.

**Known limitation:** tests build their schema with `create_all` rather than by
running migrations, so model/migration drift would not fail the suite on its
own. CI runs `alembic check` alongside the tests to catch exactly that.
