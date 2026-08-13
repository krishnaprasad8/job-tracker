"""Tests for the /applications endpoints."""

VALID = {
    "company_name": "Example Ltd",
    "role_title": "Platform Engineer",
    "applied_date": "2026-08-10",
}


def _create(client, **overrides):
    response = client.post("/applications", json={**VALID, **overrides})
    assert response.status_code == 201
    return response.json()


class TestCreate:
    def test_returns_201_and_the_created_application(self, client):
        body = _create(client)

        assert body["company_name"] == "Example Ltd"
        assert body["role_title"] == "Platform Engineer"
        assert body["applied_date"] == "2026-08-10"

    def test_status_defaults_to_applied(self, client):
        assert _create(client)["status"] == "applied"

    def test_notes_are_optional(self, client):
        assert _create(client)["notes"] is None

    def test_notes_are_stored_when_given(self, client):
        assert _create(client, notes="Referred by a friend")["notes"] == (
            "Referred by a friend"
        )

    def test_id_and_timestamps_are_assigned_by_the_database(self, client):
        body = _create(client)

        assert body["id"] > 0
        assert body["created_at"] == body["updated_at"]

    def test_rejects_invalid_status(self, client):
        response = client.post("/applications", json={**VALID, "status": "aplied"})
        assert response.status_code == 422

    def test_rejects_missing_applied_date(self, client):
        response = client.post(
            "/applications",
            json={"company_name": "Example Ltd", "role_title": "Engineer"},
        )
        assert response.status_code == 422

    def test_rejects_empty_company_name(self, client):
        response = client.post("/applications", json={**VALID, "company_name": ""})
        assert response.status_code == 422


class TestList:
    def test_is_empty_to_begin_with(self, client):
        response = client.get("/applications")

        assert response.status_code == 200
        assert response.json() == []

    def test_returns_every_application(self, client):
        _create(client, company_name="First")
        _create(client, company_name="Second")

        assert len(client.get("/applications").json()) == 2

    def test_is_sorted_by_applied_date_newest_first(self, client):
        _create(client, company_name="Older", applied_date="2026-08-01")
        _create(client, company_name="Newer", applied_date="2026-08-20")

        names = [a["company_name"] for a in client.get("/applications").json()]
        assert names == ["Newer", "Older"]


class TestGetOne:
    def test_returns_the_requested_application(self, client):
        created = _create(client)

        response = client.get(f"/applications/{created['id']}")

        assert response.status_code == 200
        assert response.json() == created

    def test_unknown_id_returns_404(self, client):
        response = client.get("/applications/999")

        assert response.status_code == 404
        assert response.json()["detail"] == "Application 999 not found"


class TestUpdate:
    def test_changes_only_the_fields_that_were_sent(self, client):
        created = _create(client, notes="Original note")

        response = client.patch(
            f"/applications/{created['id']}", json={"status": "interview"}
        )

        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "interview"
        assert body["company_name"] == created["company_name"]
        assert body["role_title"] == created["role_title"]
        assert body["notes"] == "Original note"
        assert body["applied_date"] == created["applied_date"]

    def test_moves_updated_at_but_not_created_at(self, client):
        created = _create(client)

        body = client.patch(
            f"/applications/{created['id']}", json={"status": "offer"}
        ).json()

        assert body["created_at"] == created["created_at"]
        assert body["updated_at"] > created["updated_at"]

    def test_empty_payload_changes_nothing(self, client):
        created = _create(client)

        body = client.patch(f"/applications/{created['id']}", json={}).json()

        assert body["company_name"] == created["company_name"]
        assert body["status"] == created["status"]

    def test_rejects_invalid_status(self, client):
        created = _create(client)

        response = client.patch(
            f"/applications/{created['id']}", json={"status": "not-a-status"}
        )

        assert response.status_code == 422

    def test_unknown_id_returns_404(self, client):
        response = client.patch("/applications/999", json={"status": "offer"})
        assert response.status_code == 404


class TestDelete:
    def test_returns_204_and_removes_the_application(self, client):
        created = _create(client)

        response = client.delete(f"/applications/{created['id']}")

        assert response.status_code == 204
        assert client.get(f"/applications/{created['id']}").status_code == 404
        assert client.get("/applications").json() == []

    def test_unknown_id_returns_404(self, client):
        response = client.delete("/applications/999")
        assert response.status_code == 404
