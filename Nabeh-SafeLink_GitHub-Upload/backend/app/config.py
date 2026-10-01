import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_PUBLISHABLE_KEY: str = os.getenv("SUPABASE_PUBLISHABLE_KEY", "")
    SUPABASE_SECRET_KEY: str = os.getenv("SUPABASE_SECRET_KEY", "")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    EMAILJS_HOOK_SECRET: str = os.getenv("EMAILJS_HOOK_SECRET", "")
    APP_NAME: str = os.getenv("APP_NAME", "Nabeh SafeLink")
    APP_VERSION: str = os.getenv("APP_VERSION", "1.0.0")
    CORS_ALLOWED_ORIGINS: tuple = tuple(
        origin.strip().rstrip("/")
        for origin in os.getenv("NABEH_CORS_ALLOWED_ORIGINS", "http://localhost:3000").split(",")
        if origin.strip()
    )


settings = Settings()
