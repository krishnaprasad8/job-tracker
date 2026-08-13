"""Tests for the /health endpoint."""

from sqlalchemy.exc import OperationalError

from app import main
from app.database import get_db


class TestHealth:
    def test_reports_ok_when_the_database_answers(self, client):
        response = client.get("/health")

        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    def test_reports_unhealthy_when_the_database_fails(self, client):
        class UnreachableSession:
            def execute(self, *args, **kwargs):
                raise OperationalError(
                    "SELECT 1", {}, Exception("could not connect to server")
                )

        def unreachable_db():
            yield UnreachableSession()

        # The client fixture clears dependency_overrides on teardown, so this
        # replacement does not leak into other tests.
        main.app.dependency_overrides[get_db] = unreachable_db

        response = client.get("/health")

        assert response.status_code == 503
        assert response.json() == {"status": "unhealthy"}

    def test_database_is_reachable_again_afterwards(self, client):
        """Guards against the previous test leaking its broken override."""
        assert client.get("/health").json() == {"status": "ok"}
