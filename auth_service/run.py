import os
from hashlib import sha256

import pymysql
from dotenv import load_dotenv
from flask import Flask, Response, current_app, jsonify, request
from flask.views import MethodView
from flask_smorest import Api, Blueprint, abort
from marshmallow import Schema, fields

import dbq as queries


def hash_password(password: str) -> str:
    return sha256(password.encode("utf-8")).hexdigest()


def create_db_connection():
    load_dotenv()
    try:
        port = int(os.getenv("MYSQL_PORT", "3306"))
    except ValueError:
        port = 3306

    try:
        return pymysql.connect(
            host=os.getenv("MYSQL_HOST", "localhost"),
            user=os.getenv("MYSQL_USER", "root"),
            password=os.getenv("MYSQL_PSWD", ""),
            database=os.getenv("MYSQL_DATABASE", "auth"),
            port=port,
            cursorclass=pymysql.cursors.DictCursor,
        )
    except Exception as exc:
        print(f"[!] Failed to connect to database: {exc}")
        return None


class LoginRequestSchema(Schema):
    email = fields.Email(required=True)
    password = fields.String(required=True, load_only=True)


class SessionLoginRequestSchema(Schema):
    sessionID = fields.String(required=True)


class RegisterRequestSchema(Schema):
    name = fields.String(required=True)
    surname = fields.String(required=True)
    email = fields.Email(required=True)
    password = fields.String(required=True, load_only=True)


class AccountResponseSchema(Schema):
    name = fields.String(required=True)
    surname = fields.String(required=True)
    email = fields.Email(required=True)
    sessionID = fields.String(allow_none=True)


class ApiErrorSchema(Schema):
    code = fields.Integer(required=True)
    status = fields.String(required=True)
    message = fields.String(required=True)


class MessageSchema(Schema):
    message = fields.String(required=True)
    sessionID = fields.String(allow_none=True)


blp = Blueprint("auth", __name__, description="Authentication operations")


def require_database():
    db = current_app.config.get("DB_CONN")
    if db is None:
        abort(503, message="Database unavailable")
    return db


@blp.route("/login")
class LoginResource(MethodView):
    @blp.arguments(LoginRequestSchema)
    @blp.response(200, AccountResponseSchema)
    @blp.alt_response(400, schema=ApiErrorSchema, description="Invalid credentials")
    @blp.alt_response(503, schema=ApiErrorSchema, description="Database unavailable")
    def post(self, payload):
        db = require_database()
        account = queries.account_login(
            db,
            email=payload["email"],
            password_hash=hash_password(payload["password"]),
        )
        if not account:
            abort(400, message="wrong credentials")
        return account


@blp.route("/session-login")
class SessionLoginResource(MethodView):
    @blp.arguments(SessionLoginRequestSchema)
    @blp.response(200, AccountResponseSchema)
    @blp.alt_response(401, schema=ApiErrorSchema, description="Invalid session")
    @blp.alt_response(503, schema=ApiErrorSchema, description="Database unavailable")
    def post(self, payload):
        db = require_database()
        session = queries.fetch_session_data(db, payload["sessionID"])
        if not session:
            abort(401, message="invalid session")
        return session


@blp.route("/register")
class RegisterResource(MethodView):
    @blp.arguments(RegisterRequestSchema)
    @blp.response(201, MessageSchema)
    @blp.alt_response(400, schema=ApiErrorSchema, description="Invalid registration data")
    @blp.alt_response(503, schema=ApiErrorSchema, description="Database unavailable")
    def post(self, payload):
        db = require_database()
        password_hash = hash_password(payload["password"])
        user_id = queries.insert_user(
            db,
            name=payload["name"],
            surname=payload["surname"],
            email=payload["email"],
            password_hash=password_hash,
        )
        if not user_id:
            abort(400, message="bad data")

        session_id = queries.insert_session(db, user_id, email=payload["email"])
        return {"message": "successful registration", "sessionID": session_id}, 201


@blp.route("/.well-known/jwks.json")
class JwksResource(MethodView):
    @blp.response(503, MessageSchema)
    def get(self):
        return {"message": "Not implemented"}, 503


@blp.route("/refresh-jwt")
class RefreshJwtResource(MethodView):
    @blp.response(503, MessageSchema)
    def post(self):
        return {"message": "Not implemented"}, 503


def create_app(testing: bool = False, db_connection=None) -> Flask:
    app = Flask(__name__)
    app.config.update(
        API_TITLE="Auth Service API",
        API_VERSION="1.0.0",
        OPENAPI_VERSION="3.0.3",
        OPENAPI_URL_PREFIX="/",
        OPENAPI_JSON_PATH="openapi.json",
        OPENAPI_SWAGGER_UI_PATH="/swagger-ui",
        OPENAPI_SWAGGER_UI_URL="https://cdn.jsdelivr.net/npm/swagger-ui-dist/",
        TESTING=testing,
    )

    app.config["DB_CONN"] = db_connection if db_connection is not None else create_db_connection()

    @app.before_request
    def handle_preflight():
        if request.method == "OPTIONS":
            res = Response()
            res.headers["X-Content-Type-Options"] = "*"
            return res
        return None

    api = Api(app)
    api.register_blueprint(blp)

    @app.get("/health")
    def health():
        return jsonify({"status": "ok"}), 200

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)



