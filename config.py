import os

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL") or ("sqlite:///" + os.path.join(basedir, "tunimaqam.db"))
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SECRET_KEY = os. getenv("SECRET_KEY", "dev-secret-key-change-me")

    JWT_SECRET = os.getenv("JWT_SECRET", "jwt-secret-change-me")
    JWT_ALG = "HS256"
    JWT_EXP_SECONDS = int(os.getenv("JWT_EXP_SECONDS", "3600"))

    # Security tolerances
    ALLOW_WEAK_SECRETS = os.getenv("ALLOW_WEAK_SECRETS", "1") == "1"

    # CORS basic allowlist (comma-separated origins), empty means allow all
    CORS_ORIGINS = [o.strip() for o in os.getenv("CORS_ORIGINS", "").split(",") if o.strip()]

    # Rate limiting
    RATE_LIMIT_ENABLED = os.getenv("RATE_LIMIT_ENABLED", "1") == "1"
    RATE_LIMIT_DEFAULT = os.getenv("RATE_LIMIT_DEFAULT", "200 per hour")

    GOOGLE_CLIENT_ID = os. getenv("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
    OAUTH_REDIRECT_URI = os. getenv("OAUTH_REDIRECT_URI", "http://localhost:8000/auth/google/callback")

    # Role-based access
    AUTH_ADMIN_EMAILS = [e.strip() for e in os.getenv("AUTH_ADMIN_EMAILS", "").split(",") if e.strip()]
    AUTH_EXPERT_EMAILS = [e.strip() for e in os.getenv("AUTH_EXPERT_EMAILS", "").split(",") if e.strip()]
    AUTH_ALLOWED_EMAILS = [e.strip() for e in os.getenv("AUTH_ALLOWED_EMAILS", "").split(",") if e.strip()]
    AUTH_DEFAULT_ROLE = os.getenv("AUTH_DEFAULT_ROLE", "learner")
    
    ASSEMBLYAI_API_KEY = os.getenv("ASSEMBLYAI_API_KEY", "")
    ASSEMBLYAI_API_URL = os.getenv("ASSEMBLYAI_API_URL", "https://api.assemblyai.com/v2")

    # Demo access (for local front-end games without Google OAuth)
    ENABLE_DEMO_TOKEN = os.getenv("ENABLE_DEMO_TOKEN", "1") == "1"
    DEMO_TOKEN_EMAIL = os.getenv("DEMO_TOKEN_EMAIL", "demo@local")
    DEMO_TOKEN_ROLE = os.getenv("DEMO_TOKEN_ROLE", "learner")
