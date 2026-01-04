import os
import json
from datetime import datetime
from flask import Blueprint, jsonify, request, url_for, current_app
from werkzeug.utils import secure_filename
from sqlalchemy import func

from extensions import db
from models.maqam import Maqam
from models.contribution import MaqamContribution
from models.maqam_audio import MaqamAudio
from services.auth_service import require_jwt

knowledge_bp = Blueprint('knowledge', __name__, url_prefix='/knowledge')


@knowledge_bp.route("/maqam", methods=["GET"])
def list_maqamet():
    """
    List maqamet (optionally by region)
    ---
    tags:
      - Knowledge
    parameters:
      - in: query
        name: region
        type: string
        required: false
    responses:
      200:
        description: List of maqamet
    """
    region = request.args.get("region")
    if not region:
        maqamet = Maqam.query.all()
        return jsonify([m.to_dict_full() for m in maqamet]), 200

    region_l = region.lower()
    result = []
    for m in Maqam.query.all():
        regions = json.loads(m.regions_json) if m.regions_json else []
        if any(str(r).lower() == region_l for r in regions):
            result.append(m.to_dict_full())
    return jsonify(result), 200


@knowledge_bp.route("/maqam/<int:maqam_id>", methods=["GET"])
def get_maqam(maqam_id):
    """
    Get maqam by id
    ---
    tags:
      - Knowledge
    parameters:
      - in: path
        name: maqam_id
        type: integer
        required: true
    responses:
      200:
        description: Maqam details
      404:
        description: Not found
    """
    maqam = db.session.get(Maqam, maqam_id)
    if not maqam:
        return jsonify({"error": "Maqam not found"}), 404
    return jsonify(maqam.to_dict_full()), 200


@knowledge_bp.route("/maqam/by-name/<string:name_en>", methods=["GET"])
def get_maqam_by_name(name_en):
    """
    Get maqam by English name (case-insensitive)
    ---
    tags:
      - Knowledge
    parameters:
      - in: path
        name: name_en
        type: string
        required: true
    responses:
      200:
        description: Maqam details
      404:
        description: Not found
    """
    maqam = Maqam.query.filter(
        func.lower(Maqam.name_en) == func.lower(name_en)
    ).first()
    if not maqam:
        return jsonify({"error": "Maqam not found"}), 404
    return jsonify(maqam.to_dict_full()), 200


@knowledge_bp.route("/maqam/<string:name_en>/related", methods=["GET"])
def get_related_maqamet(name_en):
    """
    Get related maqamet
    ---
    tags:
      - Knowledge
    parameters:
      - in: path
        name: name_en
        type: string
        required: true
    responses:
      200:
        description: Related maqamet
      404:
        description: Not found
    """
    base = Maqam.query.filter(func.lower(Maqam.name_en) == func.lower(name_en)).first()
    if not base:
        return jsonify({"error": "Maqam not found"}), 404

    base_regions = json.loads(base.regions_json) if base.regions_json else []
    base_emotion = base.emotion

    related = []
    for m in Maqam.query.all():
        if m.id == base.id:
            continue
        score = 0
        if base_emotion and m.emotion == base_emotion:
            score += 1
        regions = json.loads(m.regions_json) if m.regions_json else []
        if base_regions and any(r in base_regions for r in regions):
            score += 1
        if score > 0:
            related.append((score, m))

    related.sort(key=lambda t: t[0], reverse=True)
    result = [m.to_dict_full() for score, m in related[:5]]
    return jsonify({"base": base.to_dict_full(), "related": result}), 200


@knowledge_bp.route("/regions", methods=["GET"])
def list_regions():
    """
    List regions with their maqamet
    ---
    tags:
      - Knowledge
    responses:
      200:
        description: Regions and associated maqamet
    """
    regions_map = {}
    for m in Maqam.query.all():
        regions = json.loads(m.regions_json) if m.regions_json else []
        for r in regions:
            regions_map.setdefault(r, [])
            regions_map[r].append(m.to_dict_basic())
    regions_list = [{"region": r, "maqamet": maq_list} for r, maq_list in regions_map.items()]
    return jsonify(regions_list), 200


# ========== CONTRIBUTION ROUTES ==========

@knowledge_bp.route("/maqam/<int:maqam_id>/contributions", methods=["POST"])
@require_jwt(roles=["admin", "expert", "learner"])
def add_maqam_contribution(maqam_id):
    """
    Add contribution to a maqam
    ---
    tags:
      - Contributions
    security:
      - Bearer: []
    """
    maqam = db.session.get(Maqam, maqam_id)
    if not maqam:
        return jsonify({"error": "Maqam not found"}), 404

    data = request.get_json() or {}
    c_type = data.get("type")
    payload = data.get("payload")
    contributor_id = request.jwt_payload.get("email", "anonymous")

    if not c_type or payload is None:
        return jsonify({"error": "type and payload are required"}), 400

    contrib = MaqamContribution(
        maqam_id=maqam.id,
        type=c_type,
        payload_json=json.dumps(payload),
        status="pending",
        contributor_id=contributor_id,
    )
    db.session.add(contrib)
    db.session.commit()
    return jsonify({"id": contrib.id, "status": contrib.status}), 201


@knowledge_bp.route("/maqam/<int:maqam_id>/contributions", methods=["GET"])
def list_maqam_contributions(maqam_id):
    """
    List contributions for a maqam
    ---
    tags:
      - Contributions
    """
    maqam = db.session.get(Maqam, maqam_id)
    if not maqam:
        return jsonify({"error": "Maqam not found"}), 404

    result = []
    for c in maqam.contributions:
        result.append({
            "id": c.id,
            "type": c.type,
            "status": c.status,
            "payload": json.loads(c.payload_json),
            "contributor_id": c.contributor_id,
            "created_at": c.created_at.isoformat()
        })
    return jsonify(result), 200


@knowledge_bp.route("/maqam", methods=["POST"])
@require_jwt(roles=["admin", "expert", "learner"])
def propose_maqam():
    """
    Propose a new maqam (stored as pending contribution)
    ---
    tags:
      - Contributions
    security:
      - Bearer: []
    """
    data = request.get_json() or {}
    name_en = (data.get("name_en") or "").strip()
    name_ar = (data.get("name_ar") or "").strip()
    if not name_en or not name_ar:
        return jsonify({"error": "name_en and name_ar are required"}), 400

    contributor = request.jwt_payload.get("email", "anonymous")
    contrib = MaqamContribution(
        maqam_id=None,
        maqam_name=name_en,
        type="new_maqam",
        payload_json=json.dumps(data),
        status="pending",
        contributor_id=contributor,
        contributor_score=0,
    )
    db.session.add(contrib)
    db.session.commit()
    return jsonify({"id": contrib.id, "status": contrib.status}), 201


@knowledge_bp.route("/contributions/<int:contrib_id>/review", methods=["POST"])
@require_jwt(roles=["admin"])
def review_contribution(contrib_id):
    """
    Review a contribution (accept/reject)
    ---
    tags:
      - Contributions
    security:
      - Bearer: []
    """
    contrib = db.session.get(MaqamContribution, contrib_id)
    if not contrib:
        return jsonify({"error": "Contribution not found"}), 404

    data = request.get_json() or {}
    new_status = data.get("status")

    if new_status not in ["accepted", "rejected"]:
        return jsonify({"error": "status must be 'accepted' or 'rejected'"}), 400

    contrib.status = new_status
    contrib.reviewed_at = datetime.utcnow()
    if new_status == "accepted":
        contrib.contributor_score = (contrib.contributor_score or 0) + 1
    db.session.commit()
    return jsonify({"id": contrib.id, "status": contrib.status, "contributor_score": contrib.contributor_score}), 200


@knowledge_bp.route("/top-contributors", methods=["GET"])
def top_contributors():
    """
    Get top contributors ranked by total accepted contributions
    ---
    tags:
      - Contributions
    """
    # Aggregate accepted contributions by contributor_id
    results = db.session.query(
        MaqamContribution.contributor_id,
        func.count(MaqamContribution.id).label('total_contributions'),
        func.sum(MaqamContribution.contributor_score).label('total_score')
    ).filter(
        MaqamContribution.status == 'accepted'
    ).group_by(
        MaqamContribution.contributor_id
    ).order_by(
        func.count(MaqamContribution.id).desc()
    ).limit(20).all()
    
    contributors = [{
        "contributor_id": r.contributor_id,
        "total_contributions": r.total_contributions,
        "total_score": r.total_score or 0
    } for r in results]
    
    return jsonify({"contributors": contributors}), 200


@knowledge_bp.route("/maqam/<int:maqam_id>/audio", methods=["POST"])
@require_jwt(roles=["admin", "expert"])
def upload_maqam_audio(maqam_id):
    """
    Upload an audio clip for a maqam (stored as static file)
    ---
    tags:
      - Knowledge
    """
    maqam = db.session.get(Maqam, maqam_id)
    if not maqam:
        return jsonify({"error": "maqam not found"}), 404

    file = request.files.get("audio")
    if not file:
        return jsonify({"error": "audio file is required"}), 400

    filename = secure_filename(file.filename)
    if not filename:
        return jsonify({"error": "invalid filename"}), 400

    save_dir = os.path.join(current_app.root_path, "static", "audio")
    os.makedirs(save_dir, exist_ok=True)
    save_path = os.path.join(save_dir, filename)
    file.save(save_path)

    audio_url = url_for("static", filename=f"audio/{filename}", _external=True)

    maqam.audio_url = audio_url
    db.session.commit()

    return jsonify({"audio_url": audio_url}), 200


@knowledge_bp.route("/maqam/<int:maqam_id>", methods=["PUT"])
@require_jwt(roles=["admin", "expert"])
def update_maqam(maqam_id):
    """
    Update an existing maqam
    ---
    tags:
      - Knowledge
    parameters:
      - in: path
        name: maqam_id
        type: integer
        required: true
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            properties:
              name_en:
                type: string
              name_ar:
                type: string
              emotion:
                type: string
              emotion_ar:
                type: string
              usage:
                type: string
              usage_ar:
                type: string
              ajnas_json:
                type: string
              regions_json:
                type: string
              regions_ar_json:
                type: string
              description_ar:
                type: string
              description_en:
                type: string
              related_json:
                type: string
              difficulty_index:
                type: integer
              difficulty_label:
                type: string
              difficulty_label_ar:
                type: string
              emotion_weights_json:
                type: string
              historical_periods_json:
                type: string
              historical_periods_ar_json:
                type: string
              seasonal_usage_json:
                type: string
              seasonal_usage_ar_json:
                type: string
              rarity_level:
                type: string
              rarity_level_ar:
                type: string
    responses:
      200:
        description: Maqam updated
      404:
        description: Not found
    """
    maqam = db.session.get(Maqam, maqam_id)
    if not maqam:
        return jsonify({"error": "Maqam not found"}), 404
    data = request.get_json() or {}
    # Update fields (add more as needed)
    for field in [
        "name_en", "name_ar", "emotion", "emotion_ar", "usage", "usage_ar",
        "ajnas_json", "regions_json", "regions_ar_json", "description_ar", "description_en",
        "related_json", "difficulty_index", "difficulty_label", "difficulty_label_ar",
        "emotion_weights_json", "historical_periods_json", "historical_periods_ar_json",
        "seasonal_usage_json", "seasonal_usage_ar_json", "rarity_level", "rarity_level_ar"
    ]:
        if field in data:
            setattr(maqam, field, data[field])
    db.session.commit()
    return jsonify(maqam.to_dict_full()), 200


@knowledge_bp.route("/maqam/<int:maqam_id>", methods=["DELETE"])
@require_jwt(roles=["admin", "expert"])
def delete_maqam(maqam_id):
    """
    Delete a maqam by id
    ---
    tags:
      - Knowledge
    parameters:
      - in: path
        name: maqam_id
        type: integer
        required: true
    responses:
      200:
        description: Maqam deleted
      404:
        description: Not found
    """
    maqam = db.session.get(Maqam, maqam_id)
    if not maqam:
        return jsonify({"error": "Maqam not found"}), 404
    # Delete all associated audios
    for audio in maqam.audios:
        db.session.delete(audio)
    db.session.delete(maqam)
    db.session.commit()
    return jsonify({"result": "deleted"}), 200


@knowledge_bp.route("/maqam/audio/<int:audio_id>", methods=["PUT"])
@require_jwt(roles=["admin", "expert"])
def update_maqam_audio(audio_id):
    """
    Update an existing maqam audio
    ---
    tags:
      - Knowledge
    parameters:
      - in: path
        name: audio_id
        type: integer
        required: true
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            properties:
              url:
                type: string
    responses:
      200:
        description: Audio updated
      404:
        description: Not found
    """
    audio = db.session.get(MaqamAudio, audio_id)
    if not audio:
        return jsonify({"error": "Audio not found"}), 404
    data = request.get_json() or {}
    if "url" in data:
        audio.url = data["url"]
        db.session.commit()
        return jsonify({"id": audio.id, "url": audio.url}), 200
    return jsonify({"error": "No url provided"}), 400


@knowledge_bp.route("/maqam/audio/<int:audio_id>", methods=["DELETE"])
@require_jwt(roles=["admin", "expert"])
def delete_maqam_audio(audio_id):
    """
    Delete a maqam audio by id
    ---
    tags:
      - Knowledge
    parameters:
      - in: path
        name: audio_id
        type: integer
        required: true
    responses:
      200:
        description: Audio deleted
      404:
        description: Not found
    """
    audio = db.session.get(MaqamAudio, audio_id)
    if not audio:
        return jsonify({"error": "Audio not found"}), 404
    db.session.delete(audio)
    db.session.commit()
    return jsonify({"result": "deleted"}), 200
