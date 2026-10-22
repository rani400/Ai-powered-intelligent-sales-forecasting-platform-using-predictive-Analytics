# PostgreSQL init scripts

Any `.sql` file placed in this directory is executed by the PostgreSQL container when the
database is first created (the directory is mounted at `/docker-entrypoint-initdb.d` by
`docker-compose.yml`).

**Nothing is required here.** The application manages its own schema through
`backend/migrations/`, applied with:

```powershell
python backend\scripts\migrate.py
```

Use this directory only for environment-level setup, for example creating an extra database or
granting a role:

```sql
-- example only
-- CREATE DATABASE salesgenie_analytics;
```

Note: init scripts run **only** when the data volume is empty. To re-run them, remove the
volume first: `docker compose down -v`.
