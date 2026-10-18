# Database changes

`migrations/001_horse_breed.sql` adds an optional breed to existing SQLite databases.
The `CREATE TABLE IF NOT EXISTS` in `app.py` only initializes new databases;
it does not update a table that already exists. Apply this migration before
starting version 1.2 against an existing database.

Export the real schema from the TEST database into `database/schema.sql` with
the native `sqlite3` CLI after applying the migration. Commit the exported
schema along with the application and migration changes. Do not commit the
`.db` file, which contains environment-specific data.
