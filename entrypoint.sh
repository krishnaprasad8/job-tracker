#!/bin/sh
set -e

# Bring the database up to the latest migration before the app starts. If this
# fails the container stops rather than serving against a stale schema.
alembic upgrade head

exec "$@"
