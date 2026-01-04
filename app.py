"""
TuniMaqam - Modular API for Tunisian Maqamet (ṭbūʿ)

This is the application factory module. All business logic has been
refactored into separate modules following Flask best practices:

    models/          - SQLAlchemy models (Maqam, MaqamContribution, UserStat, ActivityLog)
    resources/       - Flask Blueprints (auth, knowledge, learning, analysis, recommendations)
    services/        - Business logic services (auth_service, user_service, analysis_service)
    config.py        - Configuration settings
    extensions.py    - Flask extensions (SQLAlchemy)
"""

import os
import logging
from logging.handlers import RotatingFileHandler

from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flasgger import Swagger
from dotenv import load_dotenv

# Load .env before importing Config
load_dotenv()

from config import Config
from extensions import db


def create_app(config_class=Config):
    """Application factory pattern - creates and configures the Flask app."""
    app = Flask(__name__)
    app.config.from_object(config_class)
    app.secret_key = app.config["SECRET_KEY"]
    
    # Initialize extensions
    db.init_app(app)
    
    # CORS setup
    cors_origins = app.config.get("CORS_ORIGINS") or "*"
    CORS(app, resources={r"/*": {"origins": cors_origins, "supports_credentials": True}})
    
    # Rate limiting
    limiter = Limiter(
        key_func=get_remote_address,
        app=app,
        default_limits=[app.config.get("RATE_LIMIT_DEFAULT", "200 per hour")],
        storage_uri="memory://",
    )
    if app.config.get("TESTING") or not app.config.get("RATE_LIMIT_ENABLED", True):
        limiter.enabled = False
    
    # Security validation
    if not app.config.get("ALLOW_WEAK_SECRETS"):
        if app.config.get("SECRET_KEY", "").startswith("dev-secret") or \
           app.config.get("JWT_SECRET", "").startswith("jwt-secret"):
            raise RuntimeError(
                "Weak SECRET_KEY/JWT_SECRET not allowed; "
                "set environment secrets or enable ALLOW_WEAK_SECRETS=1 for local dev"
            )
    
    # Swagger documentation
    swagger_template = {
        "swagger": "2.0",
        "info": {
            "title": "TuniMaqam API",
            "description": "Pedagogical maqam intelligence: knowledge, learning, recommendations, analysis",
            "version": "1.0.0"
        },
        "basePath": "/",
        "securityDefinitions": {
            "Bearer": {
                "type": "apiKey",
                "name": "Authorization",
                "in": "header",
                "description": 'JWT Authorization header using the Bearer scheme. Example: "Bearer {token}"'
            }
        },
        "definitions": {
            "Maqam": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer", "description": "Unique ID of the maqam", "example": 1},
                    "name_en": {"type": "string", "description": "Maqam name (English)", "example": "Rast"},
                    "name_ar": {"type": "string", "description": "Maqam name (Arabic)", "example": "راست"},
                    "emotion": {"type": "string", "description": "Associated emotion (English)", "example": "joy"},
                    "emotion_ar": {"type": "string", "description": "Associated emotion (Arabic)", "example": "فرح"},
                    "usage": {"type": "string", "description": "Typical usage (English)", "example": "weddings"},
                    "usage_ar": {"type": "string", "description": "Typical usage (Arabic)", "example": "أعراس"},
                    "ajnas_json": {"type": "string", "description": "Ajnas (JSON-encoded)", "example": '[{"name": {"en": "Rast", "ar": "راست"}}]'},
                    "regions_json": {"type": "string", "description": "Regions (JSON-encoded, English)", "example": '["Tunis", "Sfax"]'},
                    "regions_ar_json": {"type": "string", "description": "Regions (JSON-encoded, Arabic)", "example": '["تونس", "صفاقس"]'},
                    "description_ar": {"type": "string", "description": "Description (Arabic)", "example": "مقام شهير"},
                    "description_en": {"type": "string", "description": "Description (English)", "example": "A famous maqam"},
                    "related_json": {"type": "string", "description": "Related maqamet (JSON-encoded)", "example": '["Sikah", "Bayati"]'},
                    "difficulty_index": {"type": "integer", "description": "Difficulty index (numeric)", "example": 1},
                    "difficulty_label": {"type": "string", "description": "Difficulty label (English)", "example": "beginner"},
                    "difficulty_label_ar": {"type": "string", "description": "Difficulty label (Arabic)", "example": "مبتدئ"},
                    "emotion_weights_json": {"type": "string", "description": "Emotion weights (JSON-encoded)", "example": '{"joy": 1.0, "sadness": 0.0}'},
                    "historical_periods_json": {"type": "string", "description": "Historical periods (JSON-encoded, English)", "example": '["Ottoman"]'},
                    "historical_periods_ar_json": {"type": "string", "description": "Historical periods (JSON-encoded, Arabic)", "example": '["عثماني"]'},
                    "seasonal_usage_json": {"type": "string", "description": "Seasonal usage (JSON-encoded, English)", "example": '["Spring"]'},
                    "seasonal_usage_ar_json": {"type": "string", "description": "Seasonal usage (JSON-encoded, Arabic)", "example": '["الربيع"]'},
                    "rarity_level": {"type": "string", "description": "Rarity level (English)", "example": "common"},
                    "rarity_level_ar": {"type": "string", "description": "Rarity level (Arabic)", "example": "شائع"},
                    "audio_url": {"type": "string", "description": "URL to audio file", "example": "/static/audio/rast.mp3"}
                }
            },
            "MaqamUpdate": {
                "type": "object",
                "properties": {
                    "name_en": {"type": "string", "description": "Maqam name (English)", "example": "Rast"},
                    "name_ar": {"type": "string", "description": "Maqam name (Arabic)", "example": "راست"},
                    "emotion": {"type": "string", "description": "Associated emotion (English)", "example": "joy"},
                    "emotion_ar": {"type": "string", "description": "Associated emotion (Arabic)", "example": "فرح"},
                    "usage": {"type": "string", "description": "Typical usage (English)", "example": "weddings"},
                    "usage_ar": {"type": "string", "description": "Typical usage (Arabic)", "example": "أعراس"},
                    "ajnas_json": {"type": "string", "description": "Ajnas (JSON-encoded)", "example": '[{"name": {"en": "Rast", "ar": "راست"}}]'},
                    "regions_json": {"type": "string", "description": "Regions (JSON-encoded, English)", "example": '["Tunis", "Sfax"]'},
                    "regions_ar_json": {"type": "string", "description": "Regions (JSON-encoded, Arabic)", "example": '["تونس", "صفاقس"]'},
                    "description_ar": {"type": "string", "description": "Description (Arabic)", "example": "مقام شهير"},
                    "description_en": {"type": "string", "description": "Description (English)", "example": "A famous maqam"},
                    "related_json": {"type": "string", "description": "Related maqamet (JSON-encoded)", "example": '["Sikah", "Bayati"]'},
                    "difficulty_index": {"type": "integer", "description": "Difficulty index (numeric)", "example": 1},
                    "difficulty_label": {"type": "string", "description": "Difficulty label (English)", "example": "beginner"},
                    "difficulty_label_ar": {"type": "string", "description": "Difficulty label (Arabic)", "example": "مبتدئ"},
                    "emotion_weights_json": {"type": "string", "description": "Emotion weights (JSON-encoded)", "example": '{"joy": 1.0, "sadness": 0.0}'},
                    "historical_periods_json": {"type": "string", "description": "Historical periods (JSON-encoded, English)", "example": '["Ottoman"]'},
                    "historical_periods_ar_json": {"type": "string", "description": "Historical periods (JSON-encoded, Arabic)", "example": '["عثماني"]'},
                    "seasonal_usage_json": {"type": "string", "description": "Seasonal usage (JSON-encoded, English)", "example": '["Spring"]'},
                    "seasonal_usage_ar_json": {"type": "string", "description": "Seasonal usage (JSON-encoded, Arabic)", "example": '["الربيع"]'},
                    "rarity_level": {"type": "string", "description": "Rarity level (English)", "example": "common"},
                    "rarity_level_ar": {"type": "string", "description": "Rarity level (Arabic)", "example": "شائع"}
                }
            },
            "Recommendation": {
                "type": "object",
                "properties": {
                    "maqam": {"type": "string", "description": "Recommended maqam (English)", "example": "Rast"},
                    "maqam_ar": {"type": "string", "description": "Recommended maqam (Arabic)", "example": "راست"},
                    "emotion": {"type": "string", "description": "Emotion (English)", "example": "joy"},
                    "emotion_ar": {"type": "string", "description": "Emotion (Arabic)", "example": "فرح"},
                    "usage": {"type": "string", "description": "Usage (English)", "example": "weddings"},
                    "usage_ar": {"type": "string", "description": "Usage (Arabic)", "example": "أعراس"},
                    "regions": {"type": "array", "items": {"type": "string"}, "description": "Regions (English)", "example": ["Tunis", "Sfax"]},
                    "regions_ar": {"type": "array", "items": {"type": "string"}, "description": "Regions (Arabic)", "example": ["تونس", "صفاقس"]},
                    "confidence": {"type": "number", "format": "float", "description": "Confidence score", "example": 0.95},
                    "reason": {"type": "string", "description": "Reason for recommendation", "example": "emotion alignment; usage match"},
                    "rarity_level": {"type": "string", "description": "Rarity level", "example": "common"},
                    "difficulty_label": {"type": "string", "description": "Difficulty label", "example": "beginner"},
                    "evidence": {"type": "array", "items": {"type": "string"}, "description": "Evidence for recommendation", "example": ["emotion_weight", "usage_match"]}
                }
            },
            "Flashcard": {
                "type": "object",
                "properties": {
                    "name_en": {"type": "string", "description": "Maqam name (English)", "example": "Rast"},
                    "name_ar": {"type": "string", "description": "Maqam name (Arabic)", "example": "راست"},
                    "emotion_en": {"type": "string", "description": "Emotion (English)", "example": "joy"},
                    "emotion_ar": {"type": "string", "description": "Emotion (Arabic)", "example": "فرح"},
                    "usage_en": {"type": "string", "description": "Usage (English)", "example": "weddings"},
                    "usage_ar": {"type": "string", "description": "Usage (Arabic)", "example": "أعراس"},
                    "regions_en": {"type": "array", "items": {"type": "string"}, "description": "Regions (English)", "example": ["Tunis"]},
                    "regions_ar": {"type": "array", "items": {"type": "string"}, "description": "Regions (Arabic)", "example": ["تونس"]},
                    "back": {"type": "array", "items": {"type": "string"}, "description": "Flashcard back content", "example": ["joy"]},
                    "level": {"type": "string", "description": "Difficulty label", "example": "beginner"}
                }
            },
            "ActivityLog": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer", "description": "Activity ID", "example": 1},
                    "maqam_id": {"type": "integer", "description": "Maqam ID", "example": 1},
                    "activity": {"type": "string", "description": "Activity type", "example": "quiz"},
                    "created_at": {"type": "string", "format": "date-time", "description": "Timestamp", "example": "2026-01-05T12:00:00Z"}
                }
            }
        }
    }
    Swagger(app, template=swagger_template)
    
    # Initialize OAuth for auth blueprint
    from resources.auth import init_oauth
    init_oauth(app)
    
    # Register Blueprints
    from resources.auth import auth_bp
    from resources.knowledge import knowledge_bp
    from resources.learning import learning_bp
    from resources.analysis import analysis_bp
    from resources.recommendations import recommendations_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(knowledge_bp)
    app.register_blueprint(learning_bp)
    app.register_blueprint(analysis_bp)
    app.register_blueprint(recommendations_bp)
    
    # Create database tables
    with app.app_context():
        db.create_all()
    
    # ========== ROOT ROUTES ==========
    
    @app.route("/ping")
    def ping():
        """
        Health check
        ---
        tags:
          - Status
        responses:
          200:
            description: Service is alive
        """
        return jsonify({"status": "ok"}), 200
    
    @app.route("/status", methods=["GET"])
    def status():
        """
        Service status and counts
        ---
        tags:
          - Status
        responses:
          200:
            description: Basic service and dataset status
        """
        from models import Maqam, MaqamContribution
        maqamet_count = Maqam.query.count()
        contributions_count = MaqamContribution.query.count()
        return jsonify({
            "services": ["knowledge", "learning", "recommendation", "analysis"],
            "maqamet_count": maqamet_count,
            "contributions_count": contributions_count
        }), 200
    
    @app.route("/")
    def home():
        return send_from_directory("static", "index.html")
    
    # ========== LOGGING ==========
    
    if not os.path.exists("logs"):
        os.makedirs("logs")
    
    handler = RotatingFileHandler("logs/app.log", maxBytes=1_000_000, backupCount=3)
    handler.setLevel(logging.INFO)
    handler.setFormatter(logging.Formatter("[%(asctime)s] %(levelname)s %(message)s"))
    
    app.logger.addHandler(handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info("TuniMaqam app started")
    
    return app


# Create the application instance
app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
