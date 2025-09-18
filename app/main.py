from __future__ import annotations

from fastapi import FastAPI

from app.routers.contacts import router as contacts_router

app = FastAPI(
    title="Contacts API",
    version="0.1.0",
    description="REST API for managing contacts",
)

app.include_router(contacts_router)
