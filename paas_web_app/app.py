import os
import threading

from flask import Flask, jsonify, request

try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv():
        return False

from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from paas_web_app.db import create_db_engine, get_database_url, init_db
from paas_web_app.models import Link, LinkCreate, LinkRead

try:
    from flask_cors import CORS
except ImportError:  # pragma: no cover
    CORS = None  # type: ignore[assignment]


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


def _parse_range_param(value: str | None) -> tuple[int, int]:
    if not value:
        return (0, 10)

    raw = value.strip()
    if raw.startswith("[") and raw.endswith("]"):
        raw = raw[1:-1]

    parts = [p.strip() for p in raw.split(",") if p.strip()]
    if len(parts) != 2:
        return (0, 10)

    try:
        start = int(parts[0])
        end = int(parts[1])
    except ValueError:
        return (0, 10)

    if start < 0:
        start = 0
    if end < start:
        end = start

    return (start, end)


def _init_sentry_from_env() -> None:
    sentry_dsn = os.getenv("SENTRY_DSN")
    if not sentry_dsn:
        return

    try:
        import sentry_sdk

        sentry_sdk.init(dsn=sentry_dsn, send_default_pii=True)
    except ImportError:
        return


def _startup_app(app: Flask) -> None:
    _init_sentry_from_env()

    if CORS is not None:
        CORS(
            app,
            resources={r"/api/*": {"origins": ["http://localhost:5173"]}},
            methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            allow_headers=["Content-Type", "Range", "Accept"],
            expose_headers=["Content-Range", "Accept-Ranges"],
        )

    db_url = app.config["DATABASE_URL"] or get_database_url()
    engine = create_db_engine(db_url)
    init_db(engine)
    app.config["ENGINE"] = engine

    effective_base_url = (app.config["BASE_URL"] or _base_url()).rstrip("/")
    app.config["EFFECTIVE_BASE_URL"] = effective_base_url
    app.config["LIFESPAN_STARTED"] = True


def _shutdown_app(app: Flask) -> None:
    engine = app.config.get("ENGINE")
    if engine is not None:
        engine.dispose()
    app.config["ENGINE"] = None
    app.config["EFFECTIVE_BASE_URL"] = None
    app.config["LIFESPAN_STARTED"] = False


def _get_engine(app: Flask):
    engine = app.config.get("ENGINE")
    if engine is None:
        raise RuntimeError("Database engine is not initialized")
    return engine


def _get_effective_base_url(app: Flask) -> str:
    base = app.config.get("EFFECTIVE_BASE_URL")
    if not base:
        raise RuntimeError("Base URL is not initialized")
    return base


def _install_lifespan(app: Flask) -> None:
    app.config["LIFESPAN_STARTED"] = False
    lifespan_lock = threading.Lock()

    def ensure_started() -> None:
        if app.config.get("LIFESPAN_STARTED"):
            return
        with lifespan_lock:
            if not app.config.get("LIFESPAN_STARTED"):
                _startup_app(app)

    @app.before_request
    def _lifespan_before_request():
        ensure_started()

    @app.teardown_appcontext
    def _lifespan_teardown(_exc):
        return None

    app.extensions["lifespan"] = {
        "startup": lambda: _startup_app(app),
        "shutdown": lambda: _shutdown_app(app),
        "ensure_started": ensure_started,
    }


def _register_common_routes(app: Flask) -> None:
    @app.errorhandler(404)
    def not_found(_err):
        return jsonify({"error": "Not found"}), 404

    @app.get("/ping")
    def ping():
        return "pong"


def _register_links_routes(app: Flask) -> None:
    @app.get("/api/links")
    def list_links():
        return _list_links_response(app)

    @app.post("/api/links")
    def create_link():
        return _create_link_response(app)

    @app.get("/api/links/<int:link_id>")
    def get_link(link_id: int):
        return _get_link_response(app, link_id)

    @app.put("/api/links/<int:link_id>")
    def update_link(link_id: int):
        return _update_link_response(app, link_id)

    @app.delete("/api/links/<int:link_id>")
    def delete_link(link_id: int):
        return _delete_link_response(app, link_id)


def _create_link_response(app: Flask):
    engine = _get_engine(app)
    effective_base_url = _get_effective_base_url(app)
    payload = request.get_json(silent=True) or {}
    data = LinkCreate.model_validate(payload)

    with Session(engine) as session:
        link = Link(
            original_url=data.original_url,
            short_name=data.short_name,
        )
        session.add(link)
        try:
            session.commit()
        except IntegrityError:
            session.rollback()
            return jsonify({"error": "short_name already exists"}), 409
        session.refresh(link)
        return jsonify(_to_read(link, effective_base_url).model_dump()), 201


def _get_link_response(app: Flask, link_id: int):
    engine = _get_engine(app)
    effective_base_url = _get_effective_base_url(app)
    with Session(engine) as session:
        link = session.get(Link, link_id)
        if not link:
            return jsonify({"error": "Not found"}), 404
        return jsonify(_to_read(link, effective_base_url).model_dump())


def _update_link_response(app: Flask, link_id: int):
    engine = _get_engine(app)
    effective_base_url = _get_effective_base_url(app)
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


def _delete_link_response(app: Flask, link_id: int):
    engine = _get_engine(app)
    with Session(engine) as session:
        link = session.get(Link, link_id)
        if not link:
            return jsonify({"error": "Not found"}), 404
        session.delete(link)
        session.commit()
        return ("", 204)


def _list_links_response(app: Flask):
    engine = _get_engine(app)
    effective_base_url = _get_effective_base_url(app)

    start, end = _parse_range_param(request.args.get("range"))
    limit = max(0, end - start)

    with Session(engine) as session:
        total = session.exec(select(func.count()).select_from(Link)).one()
        links = session.exec(
            select(Link).order_by(Link.id).offset(start).limit(limit)
        ).all()

        if total == 0 or limit == 0 or len(links) == 0:
            content_range = (
                "links */0" if total == 0 else f"links {start}-{start}/{total}"
            )
            response = jsonify([])
            response.headers["Accept-Ranges"] = "links"
            response.headers["Content-Range"] = content_range
            return response, 200

        end_inclusive = start + len(links) - 1
        response = jsonify(
            [
                _to_read(link_item, effective_base_url).model_dump()
                for link_item in links
            ]
        )
        response.headers["Accept-Ranges"] = "links"
        response.headers["Content-Range"] = (
            f"links {start}-{end_inclusive}/{total}"
        )
        return response, 200


def create_app(*, database_url: str | None = None, base_url: str | None = None):
    load_dotenv()

    app = Flask(__name__)

    app.config["DATABASE_URL"] = database_url
    app.config["BASE_URL"] = base_url
    app.config["ENGINE"] = None
    app.config["EFFECTIVE_BASE_URL"] = None
    _install_lifespan(app)
    _register_common_routes(app)
    _register_links_routes(app)

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
