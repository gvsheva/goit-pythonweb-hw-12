from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from .config import get_database_url

DATABASE_URL = get_database_url()

engine = create_async_engine(DATABASE_URL, echo=False, future=True)

AsyncSessionLocal = async_sessionmaker(
    bind=engine, expire_on_commit=False, autoflush=False, autocommit=False
)


async def get_session():
    async with AsyncSessionLocal() as session:
        yield session
