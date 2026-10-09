from flask import g

import app as application


def test_get_db_reuses_connection(test_app):
    with test_app.app_context():
        first = application.get_db()
        second = application.get_db()
        assert first is second


def test_close_db_removes_connection(test_app):
    with test_app.app_context():
        application.get_db()
        assert "db" in g
        application.close_db()
        assert "db" not in g


def test_init_db_creates_expected_tables(test_app):
    with test_app.app_context():
        db = application.get_db()
        rows = db.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
        names = {row["name"] for row in rows}
        assert {"owners", "horses", "jockeys", "competitions", "participations"} <= names
