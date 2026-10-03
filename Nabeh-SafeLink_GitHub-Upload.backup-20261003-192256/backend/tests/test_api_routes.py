"""
Integration Tests for FastAPI Routes
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.scans import routes as scans_routes

client = TestClient(app)


def test_health_endpoint():
    res_health = client.get("/health")
    assert res_health.status_code == 200
    assert res_health.json()["status"] == "healthy"


def test_create_scan_empty_input():
    res = client.post("/api/v1/scans/", json={"input_type": "URL", "input_value": "   "})
    assert res.status_code == 400
    assert res.json()["detail"] == "المدخل مطلوب"


def test_create_guest_scan_explicit_endpoint():
    res = client.post("/api/v1/scans/guest", json={"input_type": "URL", "input_value": "https://www.google.com"})
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["data"]["is_guest"] is True
    assert data["data"]["scan_id"] is None
    assert res.headers.get("cache-control") == "no-store, private"


def test_authenticated_scan_endpoint_rejects_guest():
    res = client.post("/api/v1/scans/", json={"input_type": "URL", "input_value": "https://www.google.com"})
    assert res.status_code == 401


def test_get_scans_unauthenticated():
    res = client.get("/api/v1/scans/")
    assert res.status_code == 401


def test_get_scans_rejects_invalid_bearer_token(monkeypatch):
    monkeypatch.setattr(scans_routes.supabase.auth, "get_user", lambda token: None)
    res = client.get("/api/v1/scans/", headers={"Authorization": "Bearer definitely-invalid"})
    assert res.status_code == 401


def test_create_scan_rejects_malformed_authorization():
    res = client.post(
        "/api/v1/scans/",
        headers={"Authorization": "Bearer token extra"},
        json={"input_type": "URL", "input_value": "https://example.test"},
    )
    assert res.status_code == 401


def test_statistics_rejects_guest_access():
    res = client.get("/api/v1/statistics/me")
    assert res.status_code == 401

