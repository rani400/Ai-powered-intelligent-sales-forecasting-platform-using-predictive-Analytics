# Database directory

Reserved for database artefacts that are not managed by the migration runner:

| Path | Purpose |
| --- | --- |
| `database/init/` | SQL scripts executed by the PostgreSQL container on first start (mounted by `docker-compose.yml`). Empty by default - the application manages its own schema through `backend/migrations/`. |
| `database/dumps/` | Manual `pg_dump` snapshots. Git-ignored. |

The authoritative schema for the application lives in `backend/migrations/` and is applied with:

```powershell
python backend/scripts/migrate.py
```

Full schema documentation: [`../docs/ER_DIAGRAM.md`](../docs/ER_DIAGRAM.md).
