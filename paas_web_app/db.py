import os

from sqlmodel import Session, SQLModel, create_engine


def get_database_url() -> str:
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        raise RuntimeError('DATABASE_URL is required')
    return database_url


def create_db_engine(database_url: str):
    # Force psycopg (v3) driver for SQLAlchemy.
    # If URL doesn't specify a driver, SQLAlchemy defaults to psycopg2.
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql+psycopg://", 1)
    elif database_url.startswith("postgresql://"):
        database_url = database_url.replace(
            "postgresql://",
            "postgresql+psycopg://",
            1,
        )

    connect_args = None
    if database_url.startswith("sqlite:"):
        connect_args = {"check_same_thread": False}

    return create_engine(
        database_url,
        pool_pre_ping=True,
        connect_args=connect_args or {},
    )


def init_db(engine) -> None:
    SQLModel.metadata.create_all(engine)


def session_factory(engine):
    def _factory():
        return Session(engine)

    return _factory

