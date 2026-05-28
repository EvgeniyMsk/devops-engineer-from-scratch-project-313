import os
import threading

from flask import Flask, jsonify, request

try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv():
        return False

from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from paas_web_app.db import create_db_engine, get_database_url, init_db
from paas_web_app.models import Link, LinkCreate, LinkRead


def _base_url() -> str:
    return os.getenv("BASE_URL", "http://localhost:8080").rstrip("/")


def _short_url(base_url: str, short_name: str) -> str:
    return f"{base_url}/r/{short_name}"


def _to_read(link: Link, base_url: str) -> LinkRead:
    return LinkRead(
        id=link.id,
        original_url=link.original_url,
        short_name=link.short_name,
        short_url=_short_url(base_url, link.short_name),
    )


def create_app(*, database_url: str | None = None, base_url: str | None = None):
    load_dotenv()

    app = Flask(__name__)

    app.config["DATABASE_URL"] = database_url
    app.config["BASE_URL"] = base_url
    app.config["ENGINE"] = None
    app.config["EFFECTIVE_BASE_URL"] = None
    app.config["LIFESPAN_STARTED"] = False
    _lifespan_lock = threading.Lock()

    def _get_engine():
        engine = app.config.get("ENGINE")
        if engine is None:
            raise RuntimeError("Database engine is not initialized")
        return engine

    def _get_effective_base_url() -> str:
        base = app.config.get("EFFECTIVE_BASE_URL")
        if not base:
            raise RuntimeError("Base URL is not initialized")
        return base

    def _startup():
        sentry_dsn = os.getenv("SENTRY_DSN")
        if sentry_dsn:
            try:
                import sentry_sdk

                sentry_sdk.init(dsn=sentry_dsn, send_default_pii=True)
            except ImportError:
                pass

        db_url = app.config["DATABASE_URL"] or get_database_url()
        engine = create_db_engine(db_url)
        init_db(engine)
        app.config["ENGINE"] = engine

        effective_base_url = (app.config["BASE_URL"] or _base_url()).rstrip("/")
        app.config["EFFECTIVE_BASE_URL"] = effective_base_url
        app.config["LIFESPAN_STARTED"] = True

    def _shutdown():
        engine = app.config.get("ENGINE")
        if engine is not None:
            engine.dispose()
        app.config["ENGINE"] = None
        app.config["EFFECTIVE_BASE_URL"] = None
        app.config["LIFESPAN_STARTED"] = False

    def _ensure_started():
        if app.config.get("LIFESPAN_STARTED"):
            return
        with _lifespan_lock:
            if not app.config.get("LIFESPAN_STARTED"):
                _startup()

    @app.before_request
    def _lifespan_before_request():
        _ensure_started()

    @app.teardown_appcontext
    def _lifespan_teardown(_exc):
        return None

    app.extensions["lifespan"] = {
        "startup": _startup,
        "shutdown": _shutdown,
        "ensure_started": _ensure_started,
    }

    @app.errorhandler(404)
    def not_found(_err):
        return jsonify({"error": "Not found"}), 404

    @app.get("/ping")
    def ping():
        return "pong"

    @app.get("/api/links")
    def list_links():
        engine = _get_engine()
        effective_base_url = _get_effective_base_url()
        with Session(engine) as session:
            links = session.exec(select(Link).order_by(Link.id)).all()
            return jsonify([_to_read(l, effective_base_url).model_dump() for l in links])

    @app.post("/api/links")
    def create_link():
        engine = _get_engine()
        effective_base_url = _get_effective_base_url()
        payload = request.get_json(silent=True) or {}
        data = LinkCreate.model_validate(payload)

        with Session(engine) as session:
            link = Link(original_url=data.original_url, short_name=data.short_name)
            session.add(link)
            try:
                session.commit()
            except IntegrityError:
                session.rollback()
                return jsonify({"error": "short_name already exists"}), 409
            session.refresh(link)
            return jsonify(_to_read(link, effective_base_url).model_dump()), 201

    @app.get("/api/links/<int:link_id>")
    def get_link(link_id: int):
        engine = _get_engine()
        effective_base_url = _get_effective_base_url()
        with Session(engine) as session:
            link = session.get(Link, link_id)
            if not link:
                return jsonify({"error": "Not found"}), 404
            return jsonify(_to_read(link, effective_base_url).model_dump())

    @app.put("/api/links/<int:link_id>")
    def update_link(link_id: int):
        engine = _get_engine()
        effective_base_url = _get_effective_base_url()
        payload = request.get_json(silent=True) or {}
        data = LinkCreate.model_validate(payload)

        with Session(engine) as session:
            link = session.get(Link, link_id)
            if not link:
                return jsonify({"error": "Not found"}), 404

            link.original_url = data.original_url
            link.short_name = data.short_name
            session.add(link)
            try:
                session.commit()
            except IntegrityError:
                session.rollback()
                return jsonify({"error": "short_name already exists"}), 409
            session.refresh(link)
            return jsonify(_to_read(link, effective_base_url).model_dump())

    @app.delete("/api/links/<int:link_id>")
    def delete_link(link_id: int):
        engine = _get_engine()
        with Session(engine) as session:
            link = session.get(Link, link_id)
            if not link:
                return jsonify({"error": "Not found"}), 404
            session.delete(link)
            session.commit()
            return ("", 204)

    return app


def run():
    app = create_app()
    app.extensions["lifespan"]["startup"]()
    port_raw = os.getenv("PORT", "8080")
    try:
        port = int(port_raw)
    except ValueError:
        port = 8080

    try:
        app.run(host="0.0.0.0", port=port)
    finally:
        app.extensions["lifespan"]["shutdown"]()
