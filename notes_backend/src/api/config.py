import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    """Runtime settings loaded from environment variables."""

    postgres_url: str
    postgres_user: str
    postgres_password: str
    postgres_db: str
    postgres_port: str

    jwt_secret: str
    access_token_exp_minutes: int
    frontend_origin: str


# PUBLIC_INTERFACE
def get_settings() -> Settings:
    """Load settings from environment variables.

    Required env vars (notes_database container provides these names):
      - POSTGRES_URL, POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB, POSTGRES_PORT

    Backend-specific required env vars:
      - JWT_SECRET: used to sign JWT access tokens
      - ACCESS_TOKEN_EXP_MINUTES: int, token lifetime
      - FRONTEND_ORIGIN: for CORS (e.g. https://...:3000)
    """
    def req(name: str) -> str:
        value = os.getenv(name)
        if not value:
            raise RuntimeError(f"Missing required environment variable: {name}")
        return value

    return Settings(
        postgres_url=req("POSTGRES_URL"),
        postgres_user=req("POSTGRES_USER"),
        postgres_password=req("POSTGRES_PASSWORD"),
        postgres_db=req("POSTGRES_DB"),
        postgres_port=req("POSTGRES_PORT"),
        jwt_secret=req("JWT_SECRET"),
        access_token_exp_minutes=int(os.getenv("ACCESS_TOKEN_EXP_MINUTES", "120")),
        frontend_origin=os.getenv("FRONTEND_ORIGIN", "*"),
    )
