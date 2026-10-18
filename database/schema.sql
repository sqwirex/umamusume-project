CREATE TABLE owners (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            address TEXT NOT NULL,
            phone TEXT NOT NULL
        );
CREATE TABLE sqlite_sequence(name,seq);
CREATE TABLE horses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            gender TEXT NOT NULL,
            age INTEGER NOT NULL CHECK(age BETWEEN 1 AND 40),
            owner_id INTEGER NOT NULL, breed TEXT,
            UNIQUE(owner_id, name),
            FOREIGN KEY(owner_id) REFERENCES owners(id)
        );
CREATE TABLE jockeys (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            address TEXT NOT NULL,
            age INTEGER NOT NULL CHECK(age > 0),
            rating REAL NOT NULL CHECK(rating >= 0)
        );
CREATE TABLE competitions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            race_date TEXT NOT NULL,
            race_time TEXT NOT NULL,
            hippodrome TEXT NOT NULL,
            status TEXT NOT NULL
        );
CREATE TABLE participations (
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
