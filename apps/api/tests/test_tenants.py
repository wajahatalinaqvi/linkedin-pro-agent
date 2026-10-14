"""HTTP-level isolation tests: users cannot access another workspace or draft."""
from __future__ import annotations
import os
os.environ.setdefault("JWT_SECRET","dev-test-token-not-for-production-123456789000")
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient
from app.database import Base, get_db
from app.main import app
from app import models  # noqa: F401

def test_workspace_isolation():
    engine = create_engine("sqlite+pysqlite://", connect_args={"check_same_thread":False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    def override_db():
        with Session(engine) as db:
            yield db
    app.dependency_overrides[get_db] = override_db
    try:
        with TestClient(app) as client:
            alice = client.post("/api/v1/auth/register",json={
                "email":"alice@example.com","password":"alice-strong-password","workspace_name":"Alice Studio"
            })
            bob = client.post("/api/v1/auth/register",json={
                "email":"bob@example.com","password":"bob-strong-password","workspace_name":"Bob Studio"
            })
            assert alice.status_code == 201
            assert bob.status_code == 201
            ah = {"Authorization":"Bearer "+alice.json()["access_token"]}
            bh = {"Authorization":"Bearer "+bob.json()["access_token"]}
            aid = client.get("/api/v1/auth/me",headers=ah).json()["workspaces"][0]["id"]
            bid = client.get("/api/v1/auth/me",headers=bh).json()["workspaces"][0]["id"]
            assert aid != bid
            draft = client.post(f"/api/v1/workspaces/{aid}/drafts",headers=ah,json={
                "title":"Shopify update","caption":"New APIs are available","source_url":"https://shopify.dev/changelog/"
            })
            assert draft.status_code == 201, draft.text
            did = draft.json()["id"]
            assert len(client.get(f"/api/v1/workspaces/{aid}/drafts",headers=ah).json()) == 1
            assert client.get(f"/api/v1/workspaces/{aid}/drafts",headers=bh).status_code == 404
            assert client.post(f"/api/v1/workspaces/{aid}/drafts",headers=bh,json={
                "title":"Intrusion","caption":"Do not allow","source_url":"https://example.com"
            }).status_code == 404
            assert client.get(f"/api/v1/workspaces/{aid}/drafts/{did}",headers=bh).status_code == 404
            assert client.get(f"/api/v1/workspaces/{bid}/drafts",headers=bh).json() == []
            assert client.get(f"/api/v1/auth/me").status_code == 401
            assert client.post("/api/v1/auth/login",json={"email":"alice@example.com","password":"wrong"}).status_code == 401
            assert client.post("/api/v1/auth/register",json={
                "email":"alice@example.com","password":"alice-strong-password","workspace_name":"Duplicate"
            }).status_code == 409
    finally:
        app.dependency_overrides.clear()
        engine.dispose()
