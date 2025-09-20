# Contacts API (FastAPI)

A production-ready REST API for managing personal contacts, built with FastAPI and SQLAlchemy. It includes authentication with JWT (access/refresh), email verification, rate limiting, CORS, user avatars via Cloudinary, Docker/Compose, configuration via pydantic-settings, and Sphinx documentation with GitHub Pages publishing.

## Features

- CRUD for contacts with search and upcoming birthdays
- Authentication and authorization with JWT (access and refresh tokens)
- Email verification using fastapi-mail (MailDev for local)
- Per-user data isolation (users can access only their own contacts)
- Rate limiting (SlowAPI) on `/api/users/me`
- CORS enabled
- Avatar upload to Cloudinary
- Async SQLAlchemy 2.0 + Alembic migrations
- Config via environment variables using pydantic-settings
- Dockerfile and docker-compose for easy deployment
- Sphinx documentation and GitHub Pages CI

## Tech Stack

- FastAPI, Pydantic
- SQLAlchemy (async) + asyncpg + Alembic
- JWT via python-jose
- fastapi-mail, Cloudinary SDK
- slowapi (rate limiting)
- pydantic-settings
- Docker, Docker Compose
- Sphinx for docs

## Quick Start (Docker Compose)

1. Copy env config and set at least the secret key:
   - cp .env.example .env
   - Edit .env and set SECRET_KEY to a strong random value
2. Start services:
   - docker compose up -d --build
3. API: http://localhost:8000
4. Swagger UI: http://localhost:8000/docs
5. MailDev UI: http://localhost:1080 (view verification emails)

The API container runs migrations automatically and starts the server.

## Local Development

Requirements: Python 3.12, Poetry.

1. Install dependencies:
   - poetry install
2. Configure environment:
   - cp .env.example .env
   - Set SECRET_KEY in .env
3. Apply migrations:
   - poetry run alembic upgrade head
4. Run the API (choose one):
   - poetry run fastapi run
   - poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

Tip: You can still use Docker for Postgres and MailDev while running the API locally:
- docker compose up -d db maildev

## Authentication Flow

- Register: POST /auth/register (JSON {email, password})
- Verify email:
  - After registration, check MailDev at http://localhost:1080
  - Follow the verification link from the email (GET /auth/verify?token=...)
  - Or request a new verification email: POST /auth/request-verification?email=...
- Login (OAuth2 password flow): POST /auth/login (Content-Type: application/x-www-form-urlencoded)
  - form fields: username (email), password
  - returns { access_token, refresh_token, token_type }
- Use the access token:
  - Authorization: Bearer <access_token>
- Refresh token: POST /auth/refresh with JSON { "refresh_token": "<token>" }

Example login request (form):
- curl -X POST "http://localhost:8000/auth/login" -H "Content-Type: application/x-www-form-urlencoded" -d "username=user@example.com&password=yourpassword"

## Contacts API

Base path: /api/contacts
- POST /api/contacts — create contact
- GET /api/contacts — list contacts (filters: first_name, last_name, email, limit, offset)
- GET /api/contacts/upcoming_birthdays — contacts with birthdays in next N days (days, limit, offset)
- GET /api/contacts/{contact_id} — get contact
- PUT /api/contacts/{contact_id} — update contact
- DELETE /api/contacts/{contact_id} — delete contact

All contacts routes require authentication.

## Users API

Base path: /api/users
- GET /api/users/me — current user info (rate limited, default 5/min)
- PUT /api/users/me/avatar — upload avatar (multipart form: file) to Cloudinary

Configure CLOUDINARY_URL in .env to enable avatar uploads.

## Configuration

All configuration is managed via environment variables (pydantic-settings). See .env.example for the full list:
- DATABASE_URL, SECRET_KEY, JWT_ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES, REFRESH_TOKEN_EXPIRE_DAYS
- PUBLIC_BASE_URL
- MAIL_* (MailDev defaults work out of the box)
- CLOUDINARY_URL (optional, required for avatars)

## Database & Migrations

- Apply latest migrations:
  - poetry run alembic upgrade head
- Create a new migration:
  - poetry run alembic revision --autogenerate -m "your message"
- Downgrade:
  - poetry run alembic downgrade -1

## Documentation

- Build Sphinx docs locally:
  - poetry run sphinx-build -b html docs docs/_build/html
- Open docs/_build/html/index.html in your browser.
- GitHub Actions builds and deploys docs to GitHub Pages on push to main/master.

## Project Structure (key files)

- app/ — FastAPI application (routers, models, repositories, config)
- migrations/ — Alembic migration scripts
- docs/ — Sphinx documentation
- Dockerfile, compose.yaml — containerization
- pyproject.toml — dependencies and build config

## Security Notes

- Never commit real secrets to the repo; use .env
- Use a strong SECRET_KEY in production
- Configure CORS properly in production (not "*")

## License

MIT — feel free to use and adapt.
