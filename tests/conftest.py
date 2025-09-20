import os

import pytest
import pytest_asyncio
from faker import Faker
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import StaticPool

from app.models import Base

@pytest.fixture(scope="session")
def fake():
    faker = Faker()
    faker.seed_instance(12345)
    return faker


@pytest_asyncio.fixture(scope="session")
async def engine():
    url = os.getenv("TEST_DATABASE_URL", "sqlite+aiosqlite:///:memory:")
    engine = create_async_engine(
        url,
        echo=False,
        future=True,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )

    # Створюємо схему один раз на сесію
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    try:
        yield engine
    finally:
        await engine.dispose()


@pytest_asyncio.fixture
async def session(engine: AsyncEngine):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    SessionLocal = async_sessionmaker(
        bind=engine, expire_on_commit=False, autoflush=False, autocommit=False
    )
    async with SessionLocal() as s:
        yield s
