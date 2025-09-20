import pytest

from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool
from testcontainers.postgres import PostgresContainer
from testcontainers.redis import RedisContainer
from testcontainers.core.container import DockerContainer


@pytest.fixture(scope="session")
def postgres_container():
    with PostgresContainer("postgres:16-alpine") as container:
        yield container


@pytest.fixture(scope="session")
def redis_container():
    with RedisContainer("redis:alpine") as container:
        yield container


@pytest.fixture(scope="session")
def maildev_container():
    with DockerContainer("maildev/maildev").with_exposed_ports(1025, 1080) as container:
        yield container


@pytest.fixture(scope="session")
def test_client(
    postgres_container: PostgresContainer,
    redis_container: RedisContainer,
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
    settings.redis_url = f"redis://{redis_container.get_container_host_ip()}:{redis_container.get_exposed_port(6379)}/0"
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

    with TestClient(main.app) as client:
        yield client
