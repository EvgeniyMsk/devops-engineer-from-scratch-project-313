import os

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

    sentry_dsn = os.getenv("SENTRY_DSN")
    if sentry_dsn:
        try:
            import sentry_sdk

            sentry_sdk.init(dsn=sentry_dsn, send_default_pii=True)
        except ImportError:
            pass

    app = Flask(__name__)

    db_url = database_url or get_database_url()
    engine = create_db_engine(db_url)
    init_db(engine)

    effective_base_url = (base_url or _base_url()).rstrip("/")

    @app.errorhandler(404)
    def not_found(_err):
        return jsonify({"error": "Not found"}), 404

    @app.get("/ping")
    def ping():
        return "pong"

    @app.get("/api/links")
    def list_links():
        with Session(engine) as session:
            links = session.exec(select(Link).order_by(Link.id)).all()
            return jsonify([_to_read(l, effective_base_url).model_dump() for l in links])

    @app.post("/api/links")
    def create_link():
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
        with Session(engine) as session:
            link = session.get(Link, link_id)
            if not link:
                return jsonify({"error": "Not found"}), 404
            return jsonify(_to_read(link, effective_base_url).model_dump())

    @app.put("/api/links/<int:link_id>")
    def update_link(link_id: int):
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
    port_raw = os.getenv("PORT", "8080")
    try:
        port = int(port_raw)
    except ValueError:
        port = 8080

    app.run(host="0.0.0.0", port=port)
