# SQLite to PostgreSQL Migration

This guide will help you migrate your SQLite database to PostgreSQL.


Lightweight Python script to copy data from a local SQLite file into a PostgreSQL database.

This repository contains `migrate_sqlite_to_postgres.py` and basic instructions to run a one-time migration. This is a generic migration helper — it is not tied to any specific application framework.

**Status:** Ready for manual review and testing. Always run on a copy of your data before using in production.

## Prerequisites

- PostgreSQL installed and running (example for macOS/Homebrew):
  ```bash
  brew install postgresql@15
  brew services start postgresql@15
  ```
- Python 3.8+ and `psycopg2-binary` (`pip install psycopg2-binary`) or install from `requirements.txt` if present.

## Quickstart

1. Create and activate a virtual environment, then install the dependency:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install psycopg2-binary
# or, if a requirements.txt exists:
# pip install -r requirements.txt
```

2. Create a PostgreSQL database and user (example names used in this README):

```sql
CREATE DATABASE dbname;
CREATE USER dbname_user WITH PASSWORD 'change_me';
GRANT ALL PRIVILEGES ON DATABASE dbname TO dbname_user;
```

3. Edit `migrate_sqlite_to_postgres.py` and set the `PG_CONFIG` dictionary to match your Postgres connection:

```python
PG_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'dbname',
    'user': 'dbname_user',
    'password': 'change_me'
}
```

4. Backup your SQLite file and run the migration:

```bash
cp data.db data.db.backup
python migrate_sqlite_to_postgres.py
```

## Verification

Use `psql` to inspect the target database:

```bash
psql -U dbname_user -d dbname_db -c "\dt"
psql -U dbname_user -d dbname_db -c "SELECT COUNT(*) FROM <table_name>;"
```

## After migration

- Update your application's database configuration to point to the new PostgreSQL database.
- If your application is Node-based, install `pg` (`npm install pg` or `yarn add pg`). If Python-based, ensure `psycopg2-binary` is installed.
- Recreate any missing indexes, foreign keys or sequences as needed — this script copies tables and rows but may not recreate all DB-level objects.

## Troubleshooting

- Connection errors: ensure Postgres is running and the user/password are correct.
- Permission issues: grant privileges on tables and sequences if necessary.

## Backup

Always keep a backup of the original SQLite file:

```bash
cp data.db data.db.backup
```

## Security

- Do not commit real credentials. Use environment variables or a secrets manager for production deployments.

## Contributing

Bug reports and PRs welcome. Open an issue if you need help.

## License

This project is provided under the MIT License. Add a `LICENSE` file to apply.
