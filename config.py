import os

from dotenv import load_dotenv


load_dotenv()


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-only-secret")
    N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL", "").strip()
    N8N_TIMEOUT_SECONDS = float(os.getenv("N8N_TIMEOUT_SECONDS", "120"))
    MAX_MESSAGE_LENGTH = int(os.getenv("MAX_MESSAGE_LENGTH", "500"))
    FLASK_DEBUG = os.getenv("FLASK_DEBUG", "0") == "1"
    N8N_INTERNAL_SECRET = os.getenv("N8N_INTERNAL_SECRET", "").strip()
    N8N_INTERNAL_SECRET_HEADER = os.getenv("N8N_INTERNAL_SECRET_HEADER", "X-Webhook-Secret").strip() or "X-Webhook-Secret"
    AZURE_TENANT_ID = os.getenv("AZURE_TENANT_ID", "").strip()
    AZURE_CLIENT_ID = os.getenv("AZURE_CLIENT_ID", "").strip()
    AZURE_CLIENT_SECRET = os.getenv("AZURE_CLIENT_SECRET", "").strip()
    AZURE_REDIRECT_URI = os.getenv("AZURE_REDIRECT_URI", "http://127.0.0.1:5000/auth/callback").strip()
    AZURE_POST_LOGOUT_REDIRECT_URI = os.getenv("AZURE_POST_LOGOUT_REDIRECT_URI", "http://127.0.0.1:5000/").strip()
    AZURE_SCOPES = tuple(
        scope
        for scope in os.getenv("AZURE_SCOPES", "openid profile email").split()
        if scope.strip()
    )
    SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "0") == "1"
    SESSION_COOKIE_SAMESITE = os.getenv("SESSION_COOKIE_SAMESITE", "Lax")
