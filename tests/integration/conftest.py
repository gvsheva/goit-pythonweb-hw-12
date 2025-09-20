import pytest

from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool
from testcontainers.postgres import PostgresContainer
from testcontainers.core.container import DockerContainer


@pytest.fixture(scope="session")
def postgres_container():
    with PostgresContainer("postgres:16-alpine") as container:
        yield container


@pytest.fixture(scope="session")
def maildev_container():
    with DockerContainer("maildev/maildev").with_exposed_ports(1025, 1080) as container:
        yield container


@pytest.fixture(scope="session")
def test_client(
    postgres_container: PostgresContainer,
    maildev_container: DockerContainer,
):
    import os
    from pathlib import Path
    from alembic.config import Config as AlembicConfig
    from alembic import command as alembic_command
    from app.config import settings
    from app import db
    from app import main

    settings.database_url = postgres_container.get_connection_url(driver="asyncpg")
    settings.mail_use_credentials = False
    settings.mail_server = maildev_container.get_container_host_ip()
    settings.mail_port = maildev_container.get_exposed_port(1025)
    settings.secret_key = "my-secret-key"

    os.environ["DATABASE_URL"] = settings.database_url
    alembic_ini = Path(__file__).resolve().parents[2] / "alembic.ini"
    alembic_config = AlembicConfig(str(alembic_ini))
    alembic_config.set_main_option("sqlalchemy.url", settings.database_url)
    alembic_command.upgrade(alembic_config, "head")

    db.engine = create_async_engine(settings.database_url, echo=False, future=True, poolclass=NullPool)
    db.AsyncSessionLocal = async_sessionmaker(
        bind=db.engine, expire_on_commit=False, autoflush=False, autocommit=False
    )

    return TestClient(main.app)
