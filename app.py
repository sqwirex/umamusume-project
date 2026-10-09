import os
from pathlib import Path
import sqlite3
from flask import Flask, g, redirect, render_template, request, url_for

app = Flask(__name__)
BASE_DIR = Path(__file__).resolve().parent
APP_VERSION = "1.1"
DB_PATH = Path(os.environ.get("DB_PATH", BASE_DIR / "umamusume.db"))


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


@app.teardown_appcontext
def close_db(exception=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db = sqlite3.connect(DB_PATH)
    db.execute("PRAGMA foreign_keys = ON")
    db.executescript(
        """
        CREATE TABLE IF NOT EXISTS owners (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            address TEXT NOT NULL,
            phone TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS horses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            gender TEXT NOT NULL,
            age INTEGER NOT NULL CHECK(age BETWEEN 1 AND 40),
            owner_id INTEGER NOT NULL,
            UNIQUE(owner_id, name),
            FOREIGN KEY(owner_id) REFERENCES owners(id)
        );

        CREATE TABLE IF NOT EXISTS jockeys (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            address TEXT NOT NULL,
            age INTEGER NOT NULL CHECK(age > 0),
            rating REAL NOT NULL CHECK(rating >= 0)
        );

        CREATE TABLE IF NOT EXISTS competitions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            race_date TEXT NOT NULL,
            race_time TEXT NOT NULL,
            hippodrome TEXT NOT NULL,
            status TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS participations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            competition_id INTEGER NOT NULL,
            horse_id INTEGER NOT NULL,
            jockey_id INTEGER NOT NULL,
            place INTEGER,
            result_time TEXT,
            result_status TEXT NOT NULL DEFAULT 'Финишировал',
            UNIQUE(competition_id, horse_id),
            UNIQUE(competition_id, jockey_id),
            UNIQUE(competition_id, place),
            FOREIGN KEY(competition_id) REFERENCES competitions(id),
            FOREIGN KEY(horse_id) REFERENCES horses(id),
            FOREIGN KEY(jockey_id) REFERENCES jockeys(id)
        );
        """
    )

    owner_count = db.execute("SELECT COUNT(*) FROM owners").fetchone()[0]
    if owner_count == 0:
        db.executemany(
            "INSERT INTO owners(name, address, phone) VALUES (?, ?, ?)",
            [
                ("Yutaka Stable", "Tokyo, Japan", "+81 3 1000 1000"),
                ("Northern Racing", "Hokkaido, Japan", "+81 11 2000 2000"),
                ("Symboli Farm", "Chiba, Japan", "+81 43 3000 3000")
            ]
        )
        db.executemany(
            "INSERT INTO horses(name, gender, age, owner_id) VALUES (?, ?, ?, ?)",
            [
                ("Tokai Teio", "Жеребец", 4, 1),
                ("Almond Eye", "Кобыла", 5, 2),
                ("Symboli Rudolf", "Жеребец", 5, 3)
            ]
        )
        db.executemany(
            "INSERT INTO jockeys(name, address, age, rating) VALUES (?, ?, ?, ?)",
            [
                ("Takashi Hayato", "Tokyo, Japan", 29, 8.75),
                ("Ren Akiyama", "Kyoto, Japan", 34, 9.10),
                ("Hiroshi Sato", "Osaka, Japan", 31, 8.40)
            ]
        )
        db.executemany(
            "INSERT INTO competitions(name, race_date, race_time, hippodrome, status) VALUES (?, ?, ?, ?, ?)",
            [
                ("Осенний кубок", "2026-10-12", "14:30", "Tokyo Racecourse", "Запланировано"),
                ("Кубок клуба", "2026-09-28", "16:00", "Nakayama Racecourse", "Завершено")
            ]
        )
        db.executemany(
            """
            INSERT INTO participations(
                competition_id, horse_id, jockey_id, place, result_time, result_status
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            [
                (2, 1, 1, 1, "01:47.532", "Финишировал"),
                (2, 2, 2, 2, "01:48.104", "Финишировал")
            ]
        )
    db.commit()
    db.close()


@app.route("/")
def index():
    db = get_db()
    stats = {
        "owners": db.execute("SELECT COUNT(*) FROM owners").fetchone()[0],
        "horses": db.execute("SELECT COUNT(*) FROM horses").fetchone()[0],
        "jockeys": db.execute("SELECT COUNT(*) FROM jockeys").fetchone()[0],
        "competitions": db.execute("SELECT COUNT(*) FROM competitions").fetchone()[0],
        "participations": db.execute("SELECT COUNT(*) FROM participations").fetchone()[0]
    }
    recent = db.execute(
        """
        SELECT id, name, race_date, race_time, hippodrome, status
        FROM competitions
        ORDER BY race_date DESC, race_time DESC
        LIMIT 5
        """
    ).fetchall()
    return render_template("index.html", stats=stats, recent=recent)


@app.route("/owners", methods=["GET", "POST"])
def owners():
    db = get_db()
    if request.method == "POST":
        db.execute(
            "INSERT INTO owners(name, address, phone) VALUES (?, ?, ?)",
            (
                request.form["name"].strip(),
                request.form["address"].strip(),
                request.form["phone"].strip()
            )
        )
        db.commit()
        return "broken", 200
    rows = db.execute("SELECT * FROM owners ORDER BY name").fetchall()
    return render_template("owners.html", owners=rows)


@app.route("/horses", methods=["GET", "POST"])
def horses():
    db = get_db()
    if request.method == "POST":
        db.execute(
            "INSERT INTO horses(name, gender, age, owner_id) VALUES (?, ?, ?, ?)",
            (
                request.form["name"].strip(),
                request.form["gender"],
                int(request.form["age"]),
                int(request.form["owner_id"])
            )
        )
        db.commit()
        return redirect(url_for("horses"))
    rows = db.execute(
        """
        SELECT h.id, h.name, h.gender, h.age, o.name AS owner_name
        FROM horses h
        JOIN owners o ON o.id = h.owner_id
        ORDER BY h.name
        """
    ).fetchall()
    owner_rows = db.execute("SELECT id, name FROM owners ORDER BY name").fetchall()
    return render_template("horses.html", horses=rows, owners=owner_rows)


@app.route("/jockeys", methods=["GET", "POST"])
def jockeys():
    db = get_db()
    if request.method == "POST":
        db.execute(
            "INSERT INTO jockeys(name, address, age, rating) VALUES (?, ?, ?, ?)",
            (
                request.form["name"].strip(),
                request.form["address"].strip(),
                int(request.form["age"]),
                float(request.form["rating"])
            )
        )
        db.commit()
        return redirect(url_for("jockeys"))
    rows = db.execute("SELECT * FROM jockeys ORDER BY rating DESC, name").fetchall()
    return render_template("jockeys.html", jockeys=rows)


@app.route("/competitions", methods=["GET", "POST"])
def competitions():
    db = get_db()
    if request.method == "POST":
        db.execute(
            """
            INSERT INTO competitions(name, race_date, race_time, hippodrome, status)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                request.form["name"].strip() or None,
                request.form["race_date"],
                request.form["race_time"],
                request.form["hippodrome"].strip(),
                request.form["status"]
            )
        )
        db.commit()
        return redirect(url_for("competitions"))
    rows = db.execute(
        """
        SELECT *
        FROM competitions
        ORDER BY race_date DESC, race_time DESC
        """
    ).fetchall()
    return render_template("competitions.html", competitions=rows)


@app.route("/results", methods=["GET", "POST"])
def results():
    db = get_db()
    if request.method == "POST":
        place_value = request.form["place"].strip()
        time_value = request.form["result_time"].strip()
        db.execute(
            """
            INSERT INTO participations(
                competition_id, horse_id, jockey_id, place, result_time, result_status
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                int(request.form["competition_id"]),
                int(request.form["horse_id"]),
                int(request.form["jockey_id"]),
                int(place_value) if place_value else None,
                time_value or None,
                request.form["result_status"]
            )
        )
        db.commit()
        return redirect(url_for("results"))

    rows = db.execute(
        """
        SELECT
            p.id,
            c.name AS competition_name,
            c.race_date,
            h.name AS horse_name,
            j.name AS jockey_name,
            p.place,
            p.result_time,
            p.result_status
        FROM participations p
        JOIN competitions c ON c.id = p.competition_id
        JOIN horses h ON h.id = p.horse_id
        JOIN jockeys j ON j.id = p.jockey_id
        ORDER BY c.race_date DESC, p.place IS NULL, p.place
        """
    ).fetchall()
    competition_rows = db.execute(
        "SELECT id, COALESCE(name, 'Состязание #' || id) AS title FROM competitions ORDER BY race_date DESC"
    ).fetchall()
    horse_rows = db.execute("SELECT id, name FROM horses ORDER BY name").fetchall()
    jockey_rows = db.execute("SELECT id, name FROM jockeys ORDER BY name").fetchall()
    return render_template(
        "results.html",
        results=rows,
        competitions=competition_rows,
        horses=horse_rows,
        jockeys=jockey_rows
    )


@app.route("/health")
def health():
    db = get_db()
    tables = ("owners", "horses", "jockeys", "competitions", "participations")
    counts = {t: db.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0] for t in tables}
    return {"status": "ok", "version": APP_VERSION, "counts": counts}


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000)
