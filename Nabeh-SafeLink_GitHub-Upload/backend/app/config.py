import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_PUBLISHABLE_KEY: str = os.getenv("SUPABASE_PUBLISHABLE_KEY", "")
    SUPABASE_SECRET_KEY: str = os.getenv("SUPABASE_SECRET_KEY", "")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    AUTH_JWT_SECRET: str = os.getenv("AUTH_JWT_SECRET", "")
    AUTH_OTP_PEPPER: str = os.getenv("AUTH_OTP_PEPPER", "")
    AUTH_ACCESS_TOKEN_MINUTES: int = int(os.getenv("AUTH_ACCESS_TOKEN_MINUTES", "60"))
    AUTH_OTP_MINUTES: int = int(os.getenv("AUTH_OTP_MINUTES", "10"))
    AUTH_OTP_MAX_ATTEMPTS: int = int(os.getenv("AUTH_OTP_MAX_ATTEMPTS", "5"))
    ADMIN_JWT_SECRET: str = os.getenv("ADMIN_JWT_SECRET", "")
    ADMIN_JWT_ISSUER: str = os.getenv("ADMIN_JWT_ISSUER", "nabeh-admin")
    ADMIN_JWT_AUDIENCE: str = os.getenv("ADMIN_JWT_AUDIENCE", "nabeh-admin-api")
    ADMIN_TOTP_ENCRYPTION_KEY: str = os.getenv("ADMIN_TOTP_ENCRYPTION_KEY", "")
    ADMIN_BOOTSTRAP_TOKEN: str = os.getenv("ADMIN_BOOTSTRAP_TOKEN", "")
    ADMIN_TOTP_ISSUER: str = os.getenv("ADMIN_TOTP_ISSUER", "Nabeh Admin")
    ADMIN_ACCESS_TOKEN_MINUTES: int = int(os.getenv("ADMIN_ACCESS_TOKEN_MINUTES", "30"))
    ADMIN_REFRESH_TOKEN_DAYS: int = int(os.getenv("ADMIN_REFRESH_TOKEN_DAYS", "7"))
    ADMIN_LOGIN_RATE_LIMIT: int = int(os.getenv("ADMIN_LOGIN_RATE_LIMIT", "5"))
    ADMIN_IP_SALT: str = os.getenv("ADMIN_IP_SALT", "")
    VISITOR_HASH_SALT: str = os.getenv("VISITOR_HASH_SALT", "")
    SCAN_AI_TIMEOUT_SECONDS: float = float(os.getenv("SCAN_AI_TIMEOUT_SECONDS", "18"))
    SCAN_TOTAL_TIMEOUT_SECONDS: float = max(1.0, float(os.getenv("SCAN_TOTAL_TIMEOUT_SECONDS", "30")))
    NABEH_TRUST_PROXY_HEADERS: bool = os.getenv("NABEH_TRUST_PROXY_HEADERS", "false").lower() in {"1", "true", "yes"}
    APP_NAME: str = os.getenv("APP_NAME", "Nabeh SafeLink")
    APP_VERSION: str = os.getenv("APP_VERSION", "1.0.0")
    CORS_ALLOWED_ORIGINS: tuple = tuple(
        origin.strip().rstrip("/")
        for origin in os.getenv("NABEH_CORS_ALLOWED_ORIGINS", "http://localhost:5173,http://localhost:5174").split(",")
        if origin.strip()
    )


settings = Settings()
