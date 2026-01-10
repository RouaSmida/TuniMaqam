import json
from flask import Blueprint, jsonify, request
from marshmallow import ValidationError

from models.maqam import Maqam
from services.auth_service import require_jwt
from schemas import recommendation_request_schema

recommendations_bp = Blueprint('recommendations', __name__, url_prefix='/recommendations')


@recommendations_bp.route("/maqam", methods=["POST"])
@require_jwt(roles=["admin", "expert", "learner"])
def recommend_maqam():
    """
    Recommend maqamet for a scenario
    ---
    tags:
      - Recommendations
    security:
      - Bearer: []
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            mood: {type: string}
            event: {type: string}
            region: {type: string}
            time_period: {type: string}
            season: {type: string}
            preserve_heritage: {type: boolean}
            simple_for_beginners: {type: boolean}
    responses:
      200:
        description: Top 3 recommendations
      401:
        description: Unauthorized
    """
    data = request.get_json() or {}
    
    # Validate input using Marshmallow schema
    try:
        validated = recommendation_request_schema.load(data)
    except ValidationError as err:
        return jsonify({"error": "Validation failed", "details": err.messages}), 400

    mood = (validated.get("mood") or "").lower().strip()
    event = (validated.get("event") or "").lower().strip()
    region = (validated.get("region") or "").lower().strip()
    time_period = (validated.get("time_period") or "").lower().strip()
    season = (validated.get("season") or "").lower().strip()
    preserve = validated.get("preserve_heritage", False)
    simple_for_beginners = validated.get("simple_for_beginners", False)

    if not any([mood, event, region, time_period, season, preserve, simple_for_beginners]):
        return jsonify({"recommendations": []}), 200

    def emotion_score(request_mood, maqam):
        if not request_mood:
            return 0.0, []
        weights = getattr(maqam, "emotion_weights_json", None)
        if weights:
            try:
                w = json.loads(weights)
                val = w.get(request_mood, 0.0)
                return min(val, 1.0), ["emotion_weight"]
            except Exception:
                pass
        if maqam.emotion and request_mood in maqam.emotion.lower():
            return 0.3, ["emotion_match"]
        return 0.0, []

    candidates = []
    for m in Maqam.query.all():
        score = 0.0
        evidence = []
        reason_parts = []

        name_en = m.name_en or m.name_ar or f"Maqam {m.id}"

        s, ev = emotion_score(mood, m)
        score += s
        evidence += ev
        if ev:
            reason_parts.append("emotion alignment")

        usages = [(u or "").strip().lower() for u in (m.usage or "").split(",") if u.strip()]
        if event and any(event in u for u in usages):
            score += 0.25
            evidence.append("usage_match")
            reason_parts.append("usage match")

        regions = []
        try:
            regions = [r.lower() for r in json.loads(m.regions_json)] if m.regions_json else []
        except Exception:
            pass
        if region and any(region == r for r in regions):
            score += 0.2
            evidence.append("region_match")
            reason_parts.append("region match")

        historical = []
        if getattr(m, "historical_periods_json", None):
            try:
                historical = [h.lower() for h in json.loads(m.historical_periods_json)]
            except Exception:
                pass
        if time_period and any(time_period == h for h in historical):
            score += 0.1
            evidence.append("time_period_match")
            reason_parts.append("period match")

        seasonal = []
        if getattr(m, "seasonal_usage_json", None):
            try:
                seasonal = [s.lower() for s in json.loads(m.seasonal_usage_json)]
            except Exception:
                pass
        if season and any(season == s for s in seasonal):
            score += 0.1
            evidence.append("season_match")
            reason_parts.append("season match")

        if preserve and m.rarity_level in ["at_risk", "locally_rare"]:
            score += 0.2
            evidence.append("heritage_boost")
            reason_parts.append("heritage boost")

        if simple_for_beginners:
            if m.difficulty_label and m.difficulty_label.lower() == "beginner":
                score += 0.15
                evidence.append("beginner_path")
                reason_parts.append("beginner-friendly")
            else:
                score -= 0.05
        else:
            if m.difficulty_label and m.difficulty_label.lower() in ["intermediate", "advanced"]:
                score += 0.05
                evidence.append("advanced_ok")

        score = max(0.0, min(score, 1.0))

        if score <= 0 or not evidence:
            continue

        if not reason_parts:
            reason_parts.append("context match")

        confidence = round(score, 2)

        candidates.append({
            "maqam": name_en,
            "maqam_ar": m.name_ar,
            "emotion": m.emotion,
            "emotion_ar": getattr(m, "emotion_ar", None),
            "usage": m.usage,
            "usage_ar": getattr(m, "usage_ar", None),
            "regions": json.loads(m.regions_json) if m.regions_json else [],
            "regions_ar": json.loads(getattr(m, "regions_ar_json", "[]") or "[]"),
            "confidence": confidence,
            "reason": "; ".join(reason_parts) or "Based on your inputs",
            "rarity_level": m.rarity_level,
            "difficulty_label": m.difficulty_label,
            "evidence": evidence,
        })

    candidates.sort(key=lambda c: c["confidence"], reverse=True)

    top = candidates[:3]
    if preserve:
        heritage = [c for c in candidates if c.get("rarity_level") in ["at_risk", "locally_rare"]]
        if heritage:
            merged = heritage[:1] + candidates
            seen = set()
            deduped = []
            for c in merged:
                if c["maqam"] in seen:
                    continue
                seen.add(c["maqam"])
                deduped.append(c)
                if len(deduped) == 3:
                    break
            top = deduped

    return jsonify({"recommendations": top[:3]}), 200
