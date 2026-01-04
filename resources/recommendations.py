import json
from flask import Blueprint, jsonify, request

from models.maqam import Maqam
from services.auth_service import require_jwt

recommendations_bp = Blueprint('recommendations', __name__, url_prefix='/recommendations')


@recommendations_bp.route("/maqam", methods=["POST"])
@require_jwt(roles=["admin", "expert", "learner"])
def recommend_maqam():
    """
    Recommend a maqam based on user input.
    """
    # Dummy implementation for now
    return jsonify({"recommendations": ["Maqam Example"]})

    mood = (data.get("mood") or "").lower().strip()
    event = (data.get("event") or "").lower().strip()
    region = (data.get("region") or "").lower().strip()
    time_period = (data.get("time_period") or "").lower().strip()
    season = (data.get("season") or "").lower().strip()
    preserve = bool(data.get("preserve_heritage"))
    simple_for_beginners = bool(data.get("simple_for_beginners"))

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

        candidates.append({
            "maqam": m.name_en,
            "maqam_ar": m.name_ar,
            "emotion": m.emotion,
            "emotion_ar": getattr(m, "emotion_ar", None),
            "usage": m.usage,
            "usage_ar": getattr(m, "usage_ar", None),
            "regions": json.loads(m.regions_json) if m.regions_json else [],
            "regions_ar": json.loads(getattr(m, "regions_ar_json", "[]") or "[]"),
            "confidence": round(score, 2),
            "reason": "; ".join(reason_parts),
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
