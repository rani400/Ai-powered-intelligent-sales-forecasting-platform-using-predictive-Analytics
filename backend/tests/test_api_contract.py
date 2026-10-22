"""Tests that the implemented API matches the published contract in docs/API_CONTRACTS.md."""

from __future__ import annotations

from fastapi.testclient import TestClient

DOCUMENTED_ENDPOINTS = {
    ("get", "/"): "Service banner",
    ("get", "/health"): "Service health",
    ("post", "/api/leads"): "Create a lead",
    ("get", "/api/leads"): "Retrieve leads",
    ("get", "/api/leads/{lead_id}"): "Retrieve one lead",
    ("put", "/api/leads/{lead_id}"): "Update a lead",
    ("delete", "/api/leads/{lead_id}"): "Delete a lead",
    ("post", "/api/leads/import"): "Import CSV leads",
    ("get", "/api/leads/{lead_id}/insights"): "Retrieve lead intelligence",
    ("get", "/api/leads/stats"): "Operational counters",
    ("post", "/api/outreach/generate"): "Generate an outreach draft",
    ("get", "/api/outreach"): "List outreach drafts",
    ("get", "/api/leads/{lead_id}/outreach"): "Drafts for one lead",
}


def test_tc94_openapi_exposes_every_documented_endpoint(client: TestClient) -> None:
    """TC-94: every endpoint in the contract is present in the OpenAPI schema."""
    schema = client.get("/openapi.json").json()
    for method, path in DOCUMENTED_ENDPOINTS:
        assert path in schema["paths"], f"{path} is missing from the OpenAPI schema"
        assert method in schema["paths"][path], f"{method.upper()} {path} is missing"


def test_tc95_openapi_has_no_undocumented_endpoints(client: TestClient) -> None:
    """TC-95: the implementation does not expose endpoints that the contract omits."""
    schema = client.get("/openapi.json").json()
    implemented = {
        (method, path)
        for path, operations in schema["paths"].items()
        for method in operations
        if method in {"get", "post", "put", "delete", "patch"}
    }
    undocumented = implemented - set(DOCUMENTED_ENDPOINTS)
    assert not undocumented, f"undocumented endpoints: {sorted(undocumented)}"


def test_tc96_every_endpoint_has_a_summary(client: TestClient) -> None:
    """TC-96: every operation carries a human-readable summary for the docs page."""
    schema = client.get("/openapi.json").json()
    for path, operations in schema["paths"].items():
        for method, operation in operations.items():
            if method not in {"get", "post", "put", "delete", "patch"}:
                continue
            assert operation.get("summary"), f"{method.upper()} {path} has no summary"
            assert operation.get("tags"), f"{method.upper()} {path} has no tag"
