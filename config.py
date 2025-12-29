import os

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(basedir, "tunimaqam.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SECRET_KEY = os. getenv("SECRET_KEY", "dev-secret-key-change-me")

    JWT_SECRET = os.getenv("JWT_SECRET", "jwt-secret-change-me")
    JWT_ALG = "HS256"
    JWT_EXP_SECONDS = int(os.getenv("JWT_EXP_SECONDS", "3600"))

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
