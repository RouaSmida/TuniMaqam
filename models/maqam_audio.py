from extensions import db


class MaqamAudio(db.Model):
    __tablename__ = "maqam_audio"

    id = db.Column(db.Integer, primary_key=True)
    maqam_id = db.Column(db.Integer, db.ForeignKey("maqam.id"), nullable=False)
    url = db.Column(db.String(512), nullable=False)
