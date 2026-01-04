from datetime import datetime, timezone
from extensions import db


class MaqamContribution(db.Model):
    __tablename__ = "maqam_contribution"

    id = db.Column(db.Integer, primary_key=True)
    maqam_id = db.Column(db.Integer, db.ForeignKey("maqam.id"), nullable=True)
    maqam_name = db.Column(db.String(100), nullable=True)
    type = db.Column(db.String(50), nullable=False)
    payload_json = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default="pending")
    contributor_id = db.Column(db.String(255), nullable=True)
    contributor_score = db.Column(db.Integer, default=0)
    reviewed_by = db.Column(db.String(255), nullable=True)
    review_notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    reviewed_at = db.Column(db.DateTime, nullable=True)
