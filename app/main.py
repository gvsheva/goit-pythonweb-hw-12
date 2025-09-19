from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from app.auth import get_current_user
from app.limiter import limiter, rate_limit_exceeded_handler

from app.routers.contacts import router as contacts_router
from app.routers.auth import router as auth_router
from app.routers.users import router as users_router

app = FastAPI(
    title="Contacts API",
    version="0.2.0",
    description="REST API for managing contacts with authentication and user features.",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(users_router, dependencies=[Depends(get_current_user)])
app.include_router(contacts_router, dependencies=[Depends(get_current_user)])
