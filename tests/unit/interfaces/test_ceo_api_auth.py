import asyncio

import pytest
from fastapi import HTTPException

from enterprise_os.interfaces.api import ceo_api


def test_allows_requests_when_no_token_configured(monkeypatch):
    """Unset ENTERPRISE_OS_API_TOKEN is the documented local single-owner
    default -- no auth required."""
    monkeypatch.setattr(ceo_api, "API_TOKEN", None)
    asyncio.run(ceo_api.require_api_token(authorization=None))  # must not raise


def test_rejects_missing_header_when_token_configured(monkeypatch):
    monkeypatch.setattr(ceo_api, "API_TOKEN", "s3cret")
    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(ceo_api.require_api_token(authorization=None))
    assert exc_info.value.status_code == 401


def test_rejects_wrong_token(monkeypatch):
    monkeypatch.setattr(ceo_api, "API_TOKEN", "s3cret")
    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(ceo_api.require_api_token(authorization="Bearer wrong-token"))
    assert exc_info.value.status_code == 401


def test_rejects_header_missing_bearer_prefix(monkeypatch):
    monkeypatch.setattr(ceo_api, "API_TOKEN", "s3cret")
    with pytest.raises(HTTPException):
        asyncio.run(ceo_api.require_api_token(authorization="s3cret"))


def test_accepts_correct_bearer_token(monkeypatch):
    monkeypatch.setattr(ceo_api, "API_TOKEN", "s3cret")
    asyncio.run(ceo_api.require_api_token(authorization="Bearer s3cret"))  # must not raise


def test_goal_and_approval_endpoints_are_gated_by_the_dependency():
    """Confirms the dependency is actually wired onto the governance-sensitive
    routes, not just defined and unused."""
    gated_routes = {"/ceo/goal", "/approvals", "/approvals/{approval_id}"}
    routes_with_dependency = {
        route.path
        for route in ceo_api.app.routes
        if getattr(route, "path", None) in gated_routes
        and any(
            getattr(dep.dependency, "__name__", None) == "require_api_token"
            for dep in getattr(route, "dependencies", [])
        )
    }
    assert routes_with_dependency == gated_routes
