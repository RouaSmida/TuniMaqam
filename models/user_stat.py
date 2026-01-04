from datetime import datetime, timezone
from extensions import db


class UserStat(db.Model):
    __tablename__ = "user_stat"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(255), unique=True, nullable=False)
    best_score = db.Column(db.Float, default=0.0)
    quizzes = db.Column(db.Integer, default=0)
    activities = db.Column(db.Integer, default=0)
    level = db.Column(db.String(20), default="beginner")
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
