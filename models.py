from datetime import datetime
from extensions import db
class Maqam(db.Model):
    __tablename__ = "maqam"

    id = db.Column(db.Integer, primary_key=True)

    # Names
    name_ar = db.Column(db.String(100), nullable=False)
    name_en = db.Column(db.String(100), nullable=False)

    # Emotion (EN for logic, AR for display)
    emotion = db.Column(db.String(50), nullable=True)
    emotion_ar = db.Column(db.String(50), nullable=True)

    # Usage (comma-separated for now)
    usage = db.Column(db.String(255), nullable=True)
    usage_ar = db.Column(db.String(255), nullable=True)

    # Ajnas + regions as JSON text
    ajnas_json = db.Column(db.Text, nullable=True)
    regions_json = db.Column(db.Text, nullable=True)
    regions_ar_json = db.Column(db.Text, nullable=True)

    # Descriptions
    description_ar = db.Column(db.Text, nullable=True)
    description_en = db.Column(db.Text, nullable=True)

    # Related maqam ids (JSON list)
    related_json = db.Column(db.Text, nullable=True)

    # Difficulty
    difficulty_index = db.Column(db.Float, nullable=True)
    difficulty_label = db.Column(db.String(20), nullable=True)
    difficulty_label_ar = db.Column(db.String(20), nullable=True)

    # Emotions & context
    emotion_weights_json = db.Column(db.Text, nullable=True)

    # Historical / seasonal context (EN + AR)
    historical_periods_json = db.Column(db.Text, nullable=True)
    historical_periods_ar_json = db.Column(db.Text, nullable=True)
    seasonal_usage_json = db.Column(db.Text, nullable=True)
    seasonal_usage_ar_json = db.Column(db.Text, nullable=True)

    # Rarity / heritage
    rarity_level = db.Column(db.String(20), nullable=True)
    rarity_level_ar = db.Column(db.String(20), nullable=True)

    # NEW: audio URL
    audio_url = db.Column(db.String(512), nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict_basic(self):
        import json
        def _loads(s):
            return json.loads(s) if s else None

        return {
            "id": self.id,
            "name": {
                "ar": self.name_ar,
                "en": self.name_en,
            },
            "emotion": {
                "en": self.emotion,
                "ar": self.emotion_ar,
            },
            "usage": {
                "en": (self.usage or "").split(",") if self.usage else [],
                "ar": (self.usage_ar or "").split(",") if self.usage_ar else [],
            },
            "regions": {
                "en": _loads(self.regions_json) or [],
                "ar": _loads(self.regions_ar_json) or [],
            },
            "rarity_level": {
                "en": self.rarity_level,
                "ar": self.rarity_level_ar,
            },
            "difficulty_label": {
                "en": self.difficulty_label,
                "ar": self.difficulty_label_ar,
            },
        }

    def to_dict_full(self):
        import json
        def _loads(s):
            return json.loads(s) if s else None

        return {
            **self.to_dict_basic(),
            "ajnas": _loads(self.ajnas_json),
            "descriptions": {
                "ar": self.description_ar,
                "en": self.description_en,
            },
            "related": _loads(self.related_json),
            "emotion_weights": _loads(self.emotion_weights_json),
            "historical_periods": {
                "en": _loads(self.historical_periods_json) or [],
                "ar": _loads(self.historical_periods_ar_json) or [],
            },
            "seasonal_usage": {
                "en": _loads(self.seasonal_usage_json) or [],
                "ar": _loads(self.seasonal_usage_ar_json) or [],
            },
            "audio_url": self.audio_url,  # include in full dict
        }

class MaqamContribution(db.Model):
    __tablename__ = "maqam_contribution"

    id = db.Column(db.Integer, primary_key=True)
    maqam_id = db.Column(db.Integer, db.ForeignKey("maqam.id"), nullable=True)
    maqam_name = db.Column(db.String(100), nullable=True)  # for new maqam proposals

    type = db.Column(db.String(50), nullable=False)
    payload_json = db.Column(db.Text, nullable=False)

    status = db.Column(db.String(20), nullable=False, default="pending")
    contributor_id = db.Column(db.String(100), nullable=True)
    contributor_score = db.Column(db.Integer, nullable=True, default=0)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    reviewed_at = db.Column(db.DateTime, nullable=True)

    maqam = db.relationship("Maqam", backref="contributions", lazy=True)