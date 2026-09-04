"""Tests for the /metrics endpoint."""

import re


def _requests_total(metrics_body: str, handler: str) -> float:
    """Sum http_requests_total across all statuses for one handler."""
    pattern = re.compile(
        r'^http_requests_total\{[^}]*handler="' + re.escape(handler) + r'"[^}]*\}\s+([\d.e+]+)$',
        re.MULTILINE,
    )
    return sum(float(m) for m in pattern.findall(metrics_body))


class TestMetrics:
    def test_returns_prometheus_text_format(self, client):
        response = client.get("/metrics")

        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/plain")

    def test_exposes_request_counter_and_latency_histogram(self, client):
        client.get("/health")

        body = client.get("/metrics").text

        assert "http_requests_total" in body
        assert "http_request_duration_seconds_bucket" in body

    def test_labels_requests_by_handler(self, client):
        client.get("/health")

        assert 'handler="/health"' in client.get("/metrics").text

    def test_counter_increases_with_traffic(self, client):
        before = _requests_total(client.get("/metrics").text, "/health")

        for _ in range(3):
            client.get("/health")

        after = _requests_total(client.get("/metrics").text, "/health")
        assert after == before + 3

    def test_is_hidden_from_the_openapi_schema(self, client):
        """It's an operational endpoint, not part of the public API."""
        assert "/metrics" not in client.get("/openapi.json").json()["paths"]
