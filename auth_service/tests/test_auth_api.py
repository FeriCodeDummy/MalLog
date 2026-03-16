from hashlib import sha256

from auth_service import run


def test_openapi_spec_is_available():
    app = run.create_app(testing=True, db_connection=object())
    client = app.test_client()

    response = client.get("/openapi.json")

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["openapi"].startswith("3.")
    assert "/login" in payload["paths"]


def test_swagger_ui_is_available():
    app = run.create_app(testing=True, db_connection=object())
    client = app.test_client()


    response = client.get("/swagger-ui", follow_redirects=True)

    assert response.status_code == 200


def test_login_success_hashes_password(monkeypatch):
    captured = {}

    def fake_account_login(db, email, password_hash):
        captured["db"] = db
        captured["email"] = email
        captured["password_hash"] = password_hash
        return {
            "name": "Jane",
            "surname": "Doe",
            "email": "jane@example.com",
            "sessionID": "sid-123",
        }

    monkeypatch.setattr(run.queries, "account_login", fake_account_login)

    fake_db = object()
    app = run.create_app(testing=True, db_connection=fake_db)
    client = app.test_client()
    response = client.post(
        "/login",
        json={"email": "jane@example.com", "password": "top-secret"},
    )

    assert response.status_code == 200
    assert response.get_json()["sessionID"] == "sid-123"
    assert captured["db"] is fake_db
    assert captured["email"] == "jane@example.com"
    assert captured["password_hash"] == sha256("top-secret".encode("utf-8")).hexdigest()


def test_login_wrong_credentials(monkeypatch):
    monkeypatch.setattr(run.queries, "account_login", lambda *args, **kwargs: None)

    app = run.create_app(testing=True, db_connection=object())
    client = app.test_client()
    response = client.post(
        "/login",
        json={"email": "jane@example.com", "password": "wrong"},
    )

    assert response.status_code == 400
    assert "wrong credentials" in response.get_json()["message"]


def test_register_success(monkeypatch):
    monkeypatch.setattr(run.queries, "insert_user", lambda *args, **kwargs: 77)
    monkeypatch.setattr(run.queries, "insert_session", lambda *args, **kwargs: "sid-777")

    app = run.create_app(testing=True, db_connection=object())
    client = app.test_client()
    response = client.post(
        "/register",
        json={
            "name": "Ana",
            "surname": "Smith",
            "email": "ana@example.com",
            "password": "safe-pass",
        },
    )

    assert response.status_code == 201
    assert response.get_json()["message"] == "successful registration"
    assert response.get_json()["sessionID"] == "sid-777"


def test_session_login_invalid_session(monkeypatch):
    monkeypatch.setattr(run.queries, "fetch_session_data", lambda *args, **kwargs: None)

    app = run.create_app(testing=True, db_connection=object())
    client = app.test_client()
    response = client.post("/session-login", json={"sessionID": "missing"})

    assert response.status_code == 401
    assert "invalid session" in response.get_json()["message"]


def test_register_validation_error():
    app = run.create_app(testing=True, db_connection=object())
    client = app.test_client()
    response = client.post(
        "/register",
        json={"name": "OnlyName"},
    )

    assert response.status_code == 422


def test_returns_503_when_database_is_not_available():
    app = run.create_app(testing=True, db_connection=None)
    app.config["DB_CONN"] = None
    client = app.test_client()

    response = client.post(
        "/login",
        json={"email": "jane@example.com", "password": "secret"},
    )

    assert response.status_code == 503
