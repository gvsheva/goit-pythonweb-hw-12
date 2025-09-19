from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Database
    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/contacts",
        alias="DATABASE_URL",
    )

    # JWT / Auth
    secret_key: str = Field(..., alias="SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(
        default=30, alias="ACCESS_TOKEN_EXPIRE_MINUTES"
    )
    refresh_token_expire_days: int = Field(default=7, alias="REFRESH_TOKEN_EXPIRE_DAYS")

    # Cloudinary
    cloudinary_url: str | None = Field(default=None, alias="CLOUDINARY_URL")

    # Mail
    mail_server: str = Field(default="localhost", alias="MAIL_SERVER")
    mail_port: int = Field(default=1025, alias="MAIL_PORT")
    mail_username: str | None = Field(default=None, alias="MAIL_USERNAME")
    mail_password: str | None = Field(default=None, alias="MAIL_PASSWORD")
    mail_from: str = Field(default="no-reply@example.com", alias="MAIL_FROM")
    mail_starttls: bool = Field(default=False, alias="MAIL_STARTTLS")
    mail_ssl_tls: bool = Field(default=False, alias="MAIL_SSL_TLS")
    # If not set, will default to True when username is provided
    mail_use_credentials: bool | None = Field(
        default=None, alias="MAIL_USE_CREDENTIALS"
    )

    # Public base URL (for links in emails)
    public_base_url: str = Field(
        default="http://localhost:8000", alias="PUBLIC_BASE_URL"
    )


settings = Settings()
