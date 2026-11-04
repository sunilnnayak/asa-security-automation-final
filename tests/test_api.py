import os
import sys

os.environ.setdefault("SECRET_KEY", "test-only-secret-key-change-me-1234567890")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))

from database import Base, get_db  # noqa: E402
from main import app  # noqa: E402

TEST_DB_URL = "sqlite:///./test_vulntracker.db"
engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app, raise_server_exceptions=False)


@pytest.fixture(autouse=True)
def reset_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def register_and_login(username="alice", email="alice@example.com", password="password123"):
    client.post("/auth/register", json={"username": username, "email": email, "password": password})
    resp = client.post("/auth/login", json={"username": username, "password": password})
    return resp.json()["access_token"]


def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_register_user():
    resp = client.post("/auth/register", json={
        "username": "bob",
        "email": "bob@example.com",
        "password": "secret",
    })
    assert resp.status_code == 201
    assert resp.json()["username"] == "bob"


def test_register_duplicate_username():
    payload = {"username": "bob", "email": "bob@example.com", "password": "secret"}
    client.post("/auth/register", json=payload)
    resp = client.post("/auth/register", json={**payload, "email": "bob2@example.com"})
    assert resp.status_code == 400


def test_login_success():
    client.post("/auth/register", json={"username": "alice", "email": "alice@example.com", "password": "pw"})
    resp = client.post("/auth/login", json={"username": "alice", "password": "pw"})
    assert resp.status_code == 200
    assert "access_token" in resp.json()


def test_login_wrong_password():
    client.post("/auth/register", json={"username": "alice", "email": "alice@example.com", "password": "pw"})
    resp = client.post("/auth/login", json={"username": "alice", "password": "wrong"})
    assert resp.status_code == 401


def test_create_scan():
    token = register_and_login()
    resp = client.post("/scans", json={
        "title": "Reflected XSS in search",
        "description": "User input is echoed without sanitisation",
        "severity": "high",
        "affected_component": "GET /search",
    }, headers=auth_headers(token))
    assert resp.status_code == 201
    assert resp.json()["title"] == "Reflected XSS in search"


def test_list_scans():
    token = register_and_login()
    client.post("/scans", json={
        "title": "Test finding",
        "severity": "low",
        "affected_component": "misc",
    }, headers=auth_headers(token))
    resp = client.get("/scans", headers=auth_headers(token))
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_search_scans():
    # TODO: add assertions for search results
    token = register_and_login()
    client.post("/scans", json={
        "title": "SQL Injection via login",
        "severity": "critical",
        "affected_component": "POST /auth/login",
    }, headers=auth_headers(token))
    resp = client.get("/scans/search?q=SQL", headers=auth_headers(token))
    assert resp.status_code == 200


def test_update_scan_status():
    token = register_and_login()
    scan_id = client.post("/scans", json={
        "title": "Open redirect",
        "severity": "medium",
        "affected_component": "redirect handler",
    }, headers=auth_headers(token)).json()["id"]

    resp = client.patch(f"/scans/{scan_id}", json={"status": "in_progress"}, headers=auth_headers(token))
    assert resp.status_code == 200
    assert resp.json()["status"] == "in_progress"


def test_delete_scan():
    token = register_and_login()
    scan_id = client.post("/scans", json={
        "title": "Stale finding",
        "severity": "low",
        "affected_component": "misc",
    }, headers=auth_headers(token)).json()["id"]

    resp = client.delete(f"/scans/{scan_id}", headers=auth_headers(token))
    assert resp.status_code == 204


def test_shared_report_link_is_public_and_expires_after_24_hours():
    token = register_and_login()
    scan_id = client.post("/scans", json={
        "title": "External audit finding",
        "severity": "high",
        "affected_component": "GET /reports",
    }, headers=auth_headers(token)).json()["id"]

    created = client.post(f"/scans/{scan_id}/share", json={}, headers=auth_headers(token))
    assert created.status_code == 201
    import models
    from datetime import datetime, timedelta
    db = TestingSessionLocal()
    try:
        share_record = db.query(models.SharedReport).one()
        remaining = share_record.expires_at - datetime.utcnow()
        assert timedelta(hours=23, minutes=59) < remaining <= timedelta(hours=24)
    finally:
        db.close()
    share_url = created.json()["share_url"]
    share_token = share_url.rsplit("/", 1)[-1]

    shared = client.get(f"/share/{share_token}")
    assert shared.status_code == 200
    assert shared.json()["title"] == "External audit finding"
    assert "owner_id" not in shared.json()


def test_shared_report_requires_optional_password_when_configured():
    token = register_and_login()
    scan_id = client.post("/scans", json={
        "title": "Password protected report",
        "severity": "medium",
        "affected_component": "API",
    }, headers=auth_headers(token)).json()["id"]

    created = client.post(
        f"/scans/{scan_id}/share",
        json={"password": "StrongPassword!123"},
        headers=auth_headers(token),
    )
    share_token = created.json()["share_url"].rsplit("/", 1)[-1]

    assert client.get(f"/share/{share_token}").status_code == 401
    assert client.get(f"/share/{share_token}?password=wrong-password").status_code == 401
    assert client.get(f"/share/{share_token}?password=StrongPassword%21123").status_code == 200


def test_user_cannot_share_or_read_another_users_scan():
    owner_token = register_and_login("owner", "owner@example.com")
    scan_id = client.post("/scans", json={
        "title": "Private scan",
        "severity": "high",
        "affected_component": "API",
    }, headers=auth_headers(owner_token)).json()["id"]

    other_token = register_and_login("other", "other@example.com")
    assert client.get(f"/scans/{scan_id}", headers=auth_headers(other_token)).status_code == 404
    assert client.post(
        f"/scans/{scan_id}/share", json={}, headers=auth_headers(other_token)
    ).status_code == 404


def test_search_is_scoped_to_current_user():
    alice = register_and_login("alice2", "alice2@example.com")
    bob = register_and_login("bob2", "bob2@example.com")
    client.post("/scans", json={
        "title": "Secret SQL report",
        "severity": "high",
        "affected_component": "database",
    }, headers=auth_headers(alice))
    result = client.get("/scans/search?q=SQL", headers=auth_headers(bob))
    assert result.status_code == 200
    assert result.json()["count"] == 0


def test_shared_report_link_expires():
    from datetime import datetime, timedelta
    import models

    token = register_and_login("expiryuser", "expiry@example.com")
    scan_id = client.post("/scans", json={
        "title": "Expiring report",
        "severity": "low",
        "affected_component": "API",
    }, headers=auth_headers(token)).json()["id"]
    created = client.post(f"/scans/{scan_id}/share", json={}, headers=auth_headers(token))
    share_token = created.json()["share_url"].rsplit("/", 1)[-1]

    db = TestingSessionLocal()
    try:
        share = db.query(models.SharedReport).first()
        share.expires_at = datetime.utcnow() - timedelta(seconds=1)
        db.commit()
    finally:
        db.close()

    assert client.get(f"/share/{share_token}").status_code == 404


def test_shared_token_is_not_stored_in_plaintext_and_url_uses_configured_host():
    import hashlib
    import models

    token = register_and_login("hashuser", "hash@example.com")
    scan_id = client.post("/scans", json={
        "title": "Token storage test",
        "severity": "low",
        "affected_component": "API",
    }, headers=auth_headers(token)).json()["id"]
    created = client.post(
        f"/scans/{scan_id}/share", json={}, headers={**auth_headers(token), "Host": "attacker.example"}
    )
    assert created.status_code == 201
    share_token = created.json()["share_url"].rsplit("/", 1)[-1]
    assert created.json()["share_url"].startswith("http://localhost:8000/share/")

    db = TestingSessionLocal()
    try:
        share = db.query(models.SharedReport).one()
        assert share.token_hash == hashlib.sha256(share_token.encode("utf-8")).hexdigest()
        assert share.token_hash != share_token
    finally:
        db.close()


def test_shared_link_rejects_invalid_token():
    assert client.get("/share/not-a-valid-token").status_code == 404


def test_shared_password_rejects_more_than_bcrypt_byte_limit():
    token = register_and_login("longpw", "longpw@example.com")
    scan_id = client.post("/scans", json={
        "title": "Long password",
        "severity": "low",
        "affected_component": "API",
    }, headers=auth_headers(token)).json()["id"]
    response = client.post(
        f"/scans/{scan_id}/share",
        json={"password": "A" * 73},
        headers=auth_headers(token),
    )
    assert response.status_code == 422


def test_search_sql_metacharacters_are_treated_as_data_and_scoped():
    token = register_and_login("sqluser", "sqluser@example.com")
    client.post("/scans", json={
        "title": "Private finding",
        "severity": "high",
        "affected_component": "database",
    }, headers=auth_headers(token))
    response = client.get("/scans/search", params={"q": "%' OR 1=1 --"}, headers=auth_headers(token))
    assert response.status_code == 200
    assert response.json()["count"] == 0
