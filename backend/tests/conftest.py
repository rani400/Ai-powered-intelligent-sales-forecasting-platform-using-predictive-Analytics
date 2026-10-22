"""Shared pytest fixtures for the SalesGenie backend test suite."""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = BACKEND_DIR.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# The database URL must be set before `app.config` is imported so the settings singleton
# picks it up. A throwaway file in the system temp directory is used so that the SQLite
# connection pool can share one database across the test session.
_TEST_DB_PATH = Path(tempfile.gettempdir()) / "salesgenie_test.db"
os.environ["DATABASE_URL"] = f"sqlite:///{_TEST_DB_PATH.as_posix()}"
os.environ["SQLITE_FOREIGN_KEYS"] = "true"
os.environ["LLM_API_KEY"] = ""
os.environ["LLM_BASE_URL"] = "https://api.openai.com/v1"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.database import Base, engine  # noqa: E402
from app.main import app  # noqa: E402

VALID_LEAD = {
    "company_name": "TechCorp Solutions",
    "industry": "Software",
    "contact_name": "Sarah Johnson",
    "email": "sarah@example.com",
    "phone": "9876543210",
    "lead_status": "New",
    "company_size": "51-200",
}

SECOND_LEAD = {
    "company_name": "Innovate Labs",
    "industry": "Technology",
    "contact_name": "Mark Chen",
    "email": "mark@example.com",
    "phone": "9876543211",
    "lead_status": "New",
    "company_size": "11-50",
}


@pytest.fixture(scope="session", autouse=True)
def _session_database() -> None:
    """Create the schema once for the session and drop it at the end."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(autouse=True)
def _reset_database() -> None:
    """Give every test a clean database."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture
def client() -> TestClient:
    """Return a FastAPI test client bound to the application."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def created_lead(client: TestClient) -> dict:
    """Create one lead through the API and return its representation."""
    response = client.post("/api/leads", json=VALID_LEAD)
    assert response.status_code == 201, response.text
    return response.json()
