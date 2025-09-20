"""FastAPI application setup with CORS, auth protection, and rate limiter."""
from contextlib import asynccontextmanager
import redis.asyncio as redis
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend
from fastapi_cache.backends.redis import RedisBackend
from slowapi.errors import RateLimitExceeded

from app.config import settings
from app.limiter import limiter, rate_limit_exceeded_handler
from app.routers.auth import router as auth_router
from app.routers.contacts import router as contacts_router
from app.routers.users import router as users_router

app = FastAPI(
    title="Contacts API",
    version="0.3.0",
    description="REST API for managing contacts with authentication and user features.",
)


@asynccontextmanager
async def lifespan(_: FastAPI):
    if settings.redis_url:
        r = redis.from_url(
            settings.redis_url,
        )
        backend = RedisBackend(r)
    else:
        backend = InMemoryBackend()
    FastAPICache.init(backend, prefix="contacts-cache")
    yield


app = FastAPI(lifespan=lifespan)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["health"])
async def healthcheck():
    return {"status": "ok"}


app.include_router(auth_router)
app.include_router(users_router)
app.include_router(contacts_router)
