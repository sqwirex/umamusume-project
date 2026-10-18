"""Apply numbered SQLite migrations only if they produce the TEST schema.

Run in a container with the database directory writable and this directory
mounted read-only. The schema.sql file is exported from the TEST database.
"""

import argparse
from datetime import datetime, timezone
from pathlib import Path
import re
import sqlite3


def schema_objects(db):
    rows = db.execute(
        "SELECT type, name, tbl_name, sql FROM sqlite_master "
        "WHERE sql IS NOT NULL AND name NOT LIKE 'sqlite_%' "
        "ORDER BY type, name"
    )
    return {
        (kind, name, table): re.sub(r"\s+", " ", sql).strip().rstrip(";").casefold()
        for kind, name, table, sql in rows
    }


def migration_files(directory):
    result = []
    for path in directory.glob("[0-9]*.sql"):
        match = re.fullmatch(r"(\d+)_[a-z0-9_]+\.sql", path.name)
        if not match:
            raise ValueError(f"Unexpected migration filename: {path.name}")
        result.append((int(match.group(1)), path))
    result.sort()
    numbers = [number for number, _ in result]
    if numbers != list(range(1, len(numbers) + 1)):
        raise ValueError(f"Migration numbers must be consecutive: {numbers}")
    return result


def apply(db, migrations, target, expected, source_name):
    version = db.execute("PRAGMA user_version").fetchone()[0]
    if version > target:
        raise ValueError(f"Database version {version} exceeds available version {target}")

    # Migration 001 was applied manually on TEST and STAGE in the first phase.
    if version == 0:
        columns = {row[1] for row in db.execute("PRAGMA table_info(horses)")}
        if "breed" in columns:
            version = 1
            print("Migration 001 already applied manually; recording baseline")

    db.execute("BEGIN IMMEDIATE")
    try:
        for number, path in migrations:
            if number <= version:
                continue
            script = path.read_text(encoding="utf-8")
            if not sqlite3.complete_statement(script):
                raise ValueError(f"Incomplete SQL: {path.name}")
            print(f"Applying {path.name}")
            db.execute(script)
            version = number
        db.execute(f"PRAGMA user_version = {version}")
        verify(db, expected, source_name)
        db.commit()
    except Exception:
        db.rollback()
        raise


def verify(db, expected, source_name):
    actual = schema_objects(db)
    if actual != expected:
        missing = sorted(set(expected) - set(actual))
        extra = sorted(set(actual) - set(expected))
        altered = sorted(key for key in expected.keys() & actual.keys()
                         if expected[key] != actual[key])
        raise ValueError(
            f"Schema differs from {source_name}: missing={missing}, extra={extra}, altered={altered}"
        )
    integrity = db.execute("PRAGMA integrity_check").fetchone()[0]
    if integrity != "ok":
        raise ValueError(f"SQLite integrity check failed: {integrity}")
    foreign_key_errors = db.execute("PRAGMA foreign_key_check").fetchall()
    if foreign_key_errors:
        raise ValueError(f"Foreign key errors: {foreign_key_errors[:5]}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", required=True, type=Path)
    parser.add_argument("--schema", required=True, type=Path)
    parser.add_argument("--migrations", type=Path)
    parser.add_argument("--backup-dir", type=Path)
    parser.add_argument("--check-only", action="store_true")
    parser.add_argument("--source-name", default="TEST")
    parser.add_argument("--target-name", default="STAGE")
    args = parser.parse_args()
    if not args.database.is_file():
        parser.error(f"Existing database not found: {args.database}")

    with sqlite3.connect(":memory:") as reference:
        reference.executescript("\n".join(line for line in args.schema.read_text(encoding="utf-8").splitlines() if not line.lstrip().lower().startswith("create table sqlite_sequence")))
        expected = schema_objects(reference)
    if args.check_only:
        with sqlite3.connect(f"file:{args.database}?mode=ro", uri=True) as live:
            verify(live, expected, args.source_name)
        print(f"{args.target_name} schema equals exported {args.source_name} schema")
        return
    if args.migrations is None or args.backup_dir is None:
        parser.error("--migrations and --backup-dir are required for deployment")
    migrations = migration_files(args.migrations)
    if not migrations:
        parser.error("No migrations found")
    target = migrations[-1][0]

    with sqlite3.connect(args.database, timeout=30) as live:
        live.execute("PRAGMA foreign_keys = ON")
        if schema_objects(live) == expected:
            print(f"{args.target_name} schema already matches {args.source_name}; migration target: {target}")
            return

        with sqlite3.connect(":memory:") as rehearsal:
            live.backup(rehearsal)
            rehearsal.execute("PRAGMA foreign_keys = ON")
            apply(rehearsal, migrations, target, expected, args.source_name)
        print(f"Dry run succeeded; resulting schema equals {args.source_name}")

        args.backup_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        backup = args.backup_dir / f"{args.database.stem}-before-v{target}-{stamp}.db"
        if backup.exists():
            raise FileExistsError(backup)
        with sqlite3.connect(backup) as saved:
            live.backup(saved)
            verify(saved, schema_objects(live), args.target_name)
        print(f"Backup created: {backup}")

        apply(live, migrations, target, expected, args.source_name)
        print(f"{args.target_name} schema equals {args.source_name}; SQLite version: {target}")


if __name__ == "__main__":
    main()
