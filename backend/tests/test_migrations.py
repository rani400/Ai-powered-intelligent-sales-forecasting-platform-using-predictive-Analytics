"""Tests that the migration runner is repeatable and the schema matches the models."""

from __future__ import annotations

import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from sqlalchemy import inspect  # noqa: E402

from app.database import Base, engine  # noqa: E402


def test_tc90_migration_scripts_are_versioned_and_ordered() -> None:
    """TC-90: every migration script has a numbered, unique, ordered filename."""
    scripts = sorted((BACKEND_DIR / "migrations").glob("*.sql"))
    assert scripts, "no migration scripts found"
    names = [script.name for script in scripts]
    assert names == sorted(names)
    assert len(names) == len(set(names))
    for index, name in enumerate(names, start=1):
        assert name.startswith(f"{index:03d}_"), f"{name} is out of sequence"


def test_tc91_migration_runner_is_idempotent() -> None:
    """TC-91: running the migration runner twice does not apply a script twice."""
    sys.path.insert(0, str(BACKEND_DIR / "scripts"))
    try:
        import migrate  # type: ignore[import-not-found]
    finally:
        sys.path.remove(str(BACKEND_DIR / "scripts"))

    migrate.apply_migrations()
    after_first = migrate.applied_versions()
    migrate.apply_migrations()
    after_second = migrate.applied_versions()

    assert after_first == after_second
    assert len(after_first) == len(list((BACKEND_DIR / "migrations").glob("*.sql")))


def test_tc92_schema_matches_the_orm_models() -> None:
    """TC-92: the created schema exposes every table defined by the ORM models."""
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())
    expected = set(Base.metadata.tables)
    missing = expected - tables
    assert not missing, f"missing tables: {sorted(missing)}"


def test_tc93_foreign_keys_are_enforced() -> None:
    """TC-93: an orphan child row cannot be created (foreign keys are enforced)."""
    from sqlalchemy import text
    from sqlalchemy.exc import IntegrityError

    with engine.begin() as connection:
        try:
            connection.execute(
                text(
                    "INSERT INTO lead_scores "
                    "(lead_id, score, band, factors, methodology) "
                    "VALUES (999999, 10.0, 'Low', '[]', 'rule_based_v1')"
                )
            )
        except IntegrityError:
            return
        raise AssertionError("an orphan lead_scores row was accepted")
