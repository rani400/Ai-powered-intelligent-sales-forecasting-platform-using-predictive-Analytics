"""Versioned database migration runner.

Applies the SQL scripts in ``backend/migrations`` in filename order and records each applied
version in a ``schema_migrations`` table, so migrations are repeatable and a script is never
applied twice.

Usage (from the project root):

    python backend/scripts/migrate.py            # apply pending migrations
    python backend/scripts/migrate.py --status   # show applied / pending versions
    python backend/scripts/migrate.py --reset    # drop everything and re-apply
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = BACKEND_DIR.parent
MIGRATIONS_DIR = BACKEND_DIR / "migrations"

sys.path.insert(0, str(BACKEND_DIR))

from sqlalchemy import text  # noqa: E402

from app.config import settings  # noqa: E402
from app.database import Base, engine  # noqa: E402


def _placeholders(is_sqlite: bool) -> dict[str, str]:
    """Return the engine-specific replacements for the SQL template placeholders."""
    if is_sqlite:
        return {
            "{{PK}}": "INTEGER PRIMARY KEY AUTOINCREMENT",
            "{{FK_TYPE}}": "INTEGER",
            "{{TS}}": "DATETIME DEFAULT CURRENT_TIMESTAMP",
        }
    return {
        "{{PK}}": "SERIAL PRIMARY KEY",
        "{{FK_TYPE}}": "INTEGER",
        "{{TS}}": "TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP",
    }


def _render(sql: str, is_sqlite: bool) -> str:
    """Expand the template placeholders in a migration script."""
    for key, value in _placeholders(is_sqlite).items():
        sql = sql.replace(key, value)
    return sql


def _ensure_migration_table() -> None:
    """Create the bookkeeping table that records applied migrations."""
    with engine.begin() as connection:
        connection.execute(
            text(
                "CREATE TABLE IF NOT EXISTS schema_migrations ("
                "version VARCHAR(255) PRIMARY KEY, applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"
            )
        )


def applied_versions() -> set[str]:
    """Return the set of already-applied migration versions."""
    _ensure_migration_table()
    with engine.connect() as connection:
        rows = connection.execute(text("SELECT version FROM schema_migrations")).all()
    return {row[0] for row in rows}


def migration_files() -> list[Path]:
    """Return the migration scripts in application order."""
    return sorted(MIGRATIONS_DIR.glob("*.sql"))


def status() -> int:
    """Print the applied and pending migration versions."""
    applied = applied_versions()
    for path in migration_files():
        marker = "applied" if path.name in applied else "pending"
        print(f"[{marker:>7}] {path.name}")
    return 0


def apply_migrations(reset: bool = False) -> int:
    """Apply every pending migration script."""
    if reset:
        print("Resetting database: dropping all tables ...")
        Base.metadata.drop_all(bind=engine)
        with engine.begin() as connection:
            connection.execute(text("DROP TABLE IF EXISTS schema_migrations"))
        _ensure_migration_table()

    applied = applied_versions()
    pending = [path for path in migration_files() if path.name not in applied]

    if not pending:
        print("Database is already up to date.")
        return 0

    for path in pending:
        sql = _render(path.read_text(encoding="utf-8"), settings.is_sqlite)
        statements = [stmt.strip() for stmt in sql.split(";") if stmt.strip()]
        with engine.begin() as connection:
            for statement in statements:
                connection.execute(text(statement))
            connection.execute(
                text("INSERT INTO schema_migrations (version) VALUES (:version)"),
                {"version": path.name},
            )
        print(f"Applied {path.name} ({len(statements)} statements)")

    print(f"Applied {len(pending)} migration(s).")
    return 0


def main(argv: list[str] | None = None) -> int:
    """Command-line entry point."""
    parser = argparse.ArgumentParser(description="SalesGenie AI database migration runner")
    parser.add_argument("--status", action="store_true", help="show applied and pending migrations")
    parser.add_argument("--reset", action="store_true", help="drop all tables before applying")
    args = parser.parse_args(argv)

    print(f"Database: {engine.url.render_as_string(hide_password=True)}")

    if args.status:
        return status()
    return apply_migrations(reset=args.reset)


if __name__ == "__main__":
    raise SystemExit(main())
