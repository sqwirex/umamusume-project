import app as application


def test_create_owner(client, test_app):
    response = client.post(
        "/owners",
        data={
            "name": "Test Owner",
            "address": "Tokyo",
            "phone": "+81 00 0000 0000",
        },
    )

    assert response.status_code == 302

    with test_app.app_context():
        row = application.get_db().execute(
            "SELECT name, address, phone FROM owners WHERE name = ?",
            ("Test Owner",),
        ).fetchone()

    assert row is not None
    assert row["address"] == "Tokyo"
    assert row["phone"] == "+81 00 0000 0000"


def test_create_horse(client, test_app):
    response = client.post(
        "/horses",
        data={
            "name": "Test Horse",
            "gender": "Жеребец",
            "age": "4",
            "owner_id": "1",
        },
    )

    assert response.status_code == 302

    with test_app.app_context():
        row = application.get_db().execute(
            "SELECT name, gender, age, owner_id FROM horses WHERE name = ?",
            ("Test Horse",),
        ).fetchone()

    assert row is not None
    assert row["age"] == 4
    assert row["owner_id"] == 1


def test_create_jockey(client, test_app):
    response = client.post(
        "/jockeys",
        data={
            "name": "Test Jockey",
            "address": "Kyoto",
            "age": "27",
            "rating": "9.25",
        },
    )

    assert response.status_code == 302

    with test_app.app_context():
        row = application.get_db().execute(
            "SELECT name, age, rating FROM jockeys WHERE name = ?",
            ("Test Jockey",),
        ).fetchone()

    assert row is not None
    assert row["age"] == 27
    assert row["rating"] == 9.25


def test_create_competition(client, test_app):
    response = client.post(
        "/competitions",
        data={
            "name": "Test Cup",
            "race_date": "2026-11-01",
            "race_time": "15:00",
            "hippodrome": "Tokyo Racecourse",
            "status": "Запланировано",
        },
    )

    assert response.status_code == 302

    with test_app.app_context():
        row = application.get_db().execute(
            "SELECT name, race_date, race_time, hippodrome FROM competitions WHERE name = ?",
            ("Test Cup",),
        ).fetchone()

    assert row is not None
    assert row["race_date"] == "2026-11-01"
    assert row["race_time"] == "15:00"


def test_create_result(client, test_app):
    response = client.post(
        "/results",
        data={
            "competition_id": "1",
            "horse_id": "1",
            "jockey_id": "1",
            "place": "3",
            "result_time": "01:50.123",
            "result_status": "Финишировал",
        },
    )

    assert response.status_code == 302

    with test_app.app_context():
        row = application.get_db().execute(
            """
            SELECT competition_id, horse_id, jockey_id, place, result_time
            FROM participations
            WHERE competition_id = 1 AND horse_id = 1
            """
        ).fetchone()

    assert row is not None
    assert row["jockey_id"] == 1
    assert row["place"] == 3
    assert row["result_time"] == "01:50.123"


def test_results_page_shows_participants(client):
    response = client.get("/results")

    assert response.status_code == 200
    assert "Tokai Teio".encode() in response.data
    assert "Takashi Hayato".encode() in response.data
