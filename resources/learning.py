import json
import random
from flask import Blueprint, jsonify, request

from extensions import db
from models.maqam import Maqam
from models.user_stat import UserStat
from models.activity_log import ActivityLog
from services.auth_service import require_jwt
from services.user_service import get_or_create_user_stat, record_activity, update_quiz_stats

learning_bp = Blueprint('learning', __name__, url_prefix='/learning')

# In-memory quiz storage
QUIZZES = {}
QUIZ_COUNTER = 1


def build_mcq_choices(correct, pool, k=3):
    pool = [p for p in pool if p and p != correct]
    pool = list(dict.fromkeys(pool))
    distractors = random.sample(pool, k=min(k, len(pool)))
    choices = [correct] + distractors
    choices = list(dict.fromkeys(choices))
    random.shuffle(choices)
    return choices


def make_question_bank(maqamet):
    questions = []
    for m in maqamet:
        # Emotion open
        if m.emotion:
            questions.append({
                "type": "open",
                "prompt": f"What is the main emotion of {m.name_en}?",
                "answer": m.emotion,
                "maqam_id": m.id
            })
        # Region MCQ
        regions = json.loads(m.regions_json) if m.regions_json else []
        if regions:
            choices = build_mcq_choices(regions[0], [r for mm in maqamet for r in (json.loads(mm.regions_json) if mm.regions_json else [])])
            questions.append({
                "type": "mcq",
                "prompt": f"In which region is {m.name_en} mainly used?",
                "choices": choices,
                "answer": regions[0],
                "maqam_id": m.id
            })
        # Usage MCQ
        usages = [u.strip() for u in (m.usage or "").split(",") if u.strip()]
        if usages:
            pool_usage = []
            for mm in maqamet:
                pool_usage += [u.strip() for u in (mm.usage or "").split(",") if u.strip()]
            choices = build_mcq_choices(usages[0], pool_usage)
            questions.append({
                "type": "mcq",
                "prompt": f"Select a typical usage of {m.name_en}.",
                "choices": choices,
                "answer": usages[0],
                "maqam_id": m.id
            })
        # Ajnas MCQ
        try:
            ajnas = json.loads(m.ajnas_json) if m.ajnas_json else []
            names = []
            for a in ajnas:
                nm = a.get("name")
                if isinstance(nm, dict):
                    nm = nm.get("en") or nm.get("ar")
                if isinstance(nm, str):
                    names.append(nm)
            if names:
                pool_ajnas = []
                for mm in maqamet:
                    ajn = json.loads(mm.ajnas_json) if mm.ajnas_json else []
                    for a in ajn:
                        nm2 = a.get("name")
                        if isinstance(nm2, dict):
                            nm2 = nm2.get("en") or nm2.get("ar")
                        if isinstance(nm2, str):
                            pool_ajnas.append(nm2)
                choices = build_mcq_choices(names[0], pool_ajnas)
                questions.append({
                    "type": "mcq",
                    "prompt": f"Which jins (ajnas) is part of {m.name_en}?",
                    "choices": choices,
                    "answer": names[0],
                    "maqam_id": m.id
                })
        except Exception:
            pass
    random.shuffle(questions)
    return questions


@learning_bp.route("/flashcards", methods=["GET"])
def learning_flashcards():
    """
    Get flashcards by topic
    ---
    tags:
      - Learning
    parameters:
      - in: query
        name: topic
        schema:
          type: string
        required: false
        description: Flashcard topic (emotion, region, usage, ajnas)
      - in: query
        name: level
        schema:
          type: string
        required: false
        description: Difficulty level
    responses:
      200:
        description: List of flashcards
    """
    topic = request.args.get("topic", "emotion")
    level = request.args.get("level", "beginner")
    cards = []
    maqamet = Maqam.query.all()
    for m in maqamet:
        if topic == "emotion":
            cards.append({
                "name_en": m.name_en,
                "name_ar": m.name_ar,
                "emotion_en": m.emotion,
                "emotion_ar": getattr(m, "emotion_ar", None),
                "regions_en": json.loads(m.regions_json) if m.regions_json else [],
                "regions_ar": json.loads(getattr(m, "regions_ar_json", "[]") or "[]"),
                "back": [m.emotion] if m.emotion else [],
                "level": m.difficulty_label,
            })
        elif topic == "region":
            regions_en = json.loads(m.regions_json) if m.regions_json else []
            regions_ar = json.loads(getattr(m, "regions_ar_json", "[]") or "[]")
            cards.append({
                "name_en": m.name_en,
                "name_ar": m.name_ar,
                "emotion_en": m.emotion,
                "emotion_ar": getattr(m, "emotion_ar", None),
                "usage_en": m.usage,
                "usage_ar": getattr(m, "usage_ar", None),
                "regions_en": regions_en,
                "regions_ar": regions_ar,
                "back": regions_en,
                "level": m.difficulty_label,
            })
        elif topic == "usage":
            usages_en = [u.strip() for u in (m.usage or "").split(",") if u.strip()]
            if hasattr(m, "usage_ar_json") and m.usage_ar_json:
                try:
                    usages_ar_list = json.loads(m.usage_ar_json)
                    usages_ar = [u.strip() for u in usages_ar_list if str(u).strip()] if isinstance(usages_ar_list, list) else []
                except Exception:
                    usages_ar = []
            else:
                raw_ar = getattr(m, "usage_ar", None)
                usages_ar = [raw_ar.strip()] if raw_ar else []
            cards.append({
                "name_en": m.name_en,
                "name_ar": m.name_ar,
                "emotion_en": m.emotion,
                "emotion_ar": getattr(m, "emotion_ar", None),
                "usage_en": ", ".join(usages_en),
                "usage_ar_list": usages_ar,
                "regions_en": json.loads(m.regions_json) if m.regions_json else [],
                "regions_ar": json.loads(getattr(m, "regions_ar_json", "[]") or "[]"),
                "back": usages_en,
                "level": m.difficulty_label,
            })
        elif topic == "ajnas":
            # Ajnas flashcards: show maqam name, reveal first and second jins
            ajnas_data = []
            first_jins_en = ""
            first_jins_ar = ""
            second_jins_en = ""
            second_jins_ar = ""
            
            if m.ajnas_json:
                try:
                    ajnas = json.loads(m.ajnas_json)
                    for i, a in enumerate(ajnas[:2]):  # First two ajnas
                        nm = a.get("name", {})
                        if isinstance(nm, dict):
                            en_name = nm.get("en", "")
                            ar_name = nm.get("ar", "")
                        else:
                            en_name = str(nm) if nm else ""
                            ar_name = ""
                        
                        if i == 0:
                            first_jins_en = en_name
                            first_jins_ar = ar_name
                        elif i == 1:
                            second_jins_en = en_name
                            second_jins_ar = ar_name
                except Exception:
                    pass
            
            cards.append({
                "name_en": m.name_en,
                "name_ar": m.name_ar,
                "first_jins_en": first_jins_en,
                "first_jins_ar": first_jins_ar,
                "second_jins_en": second_jins_en,
                "second_jins_ar": second_jins_ar,
                "back": f"{first_jins_en}" + (f" / {second_jins_en}" if second_jins_en else ""),
                "level": m.difficulty_label,
            })
        else:
            return jsonify({"error": "invalid topic"}), 400
    return jsonify({"topic": topic, "level": level, "count": len(cards), "cards": cards}), 200


@learning_bp.route("/plan", methods=["GET"])
@require_jwt(roles=["admin", "expert", "learner"])
def learning_plan():
    """
    Get learning plan ordered by difficulty
    ---
    tags:
      - Learning
    security:
      - Bearer: []
    parameters:
      - in: query
        name: level
        schema:
          type: string
        required: false
        description: Difficulty level
    responses:
      200:
        description: Learning plan
    """
    level = request.args.get("level", "beginner")
    order = {"beginner": 1, "intermediate": 2, "advanced": 3}
    maqamet = Maqam.query.all()
    if not maqamet:
        return jsonify({"level": level, "count": 0, "items": []}), 200
    maqamet.sort(key=lambda m: order.get(getattr(m, "difficulty_label", "advanced"), 3))
    if level in order:
        filtered = [m for m in maqamet if getattr(m, "difficulty_label", None) == level]
        if filtered:
            maqamet = filtered
    plan = []
    for m in maqamet:
        plan.append({
            "maqam_id": m.id,
            "name_en": m.name_en,
            "difficulty_label": getattr(m, "difficulty_label", None),
            "suggested_activities": [
                "flashcards_emotion", "flashcards_region", "quiz_emotion",
                "mcq", "matching", "audio_recognition", "clue_game",
                "order_jins", "odd_one_out"
            ]
        })
    return jsonify({"level": level, "count": len(plan), "items": plan}), 200


@learning_bp.route("/quiz/start", methods=["POST"])
@require_jwt(roles=["admin", "expert", "learner"])
def start_quiz():
    """
    Start a mixed quiz (20 questions, mixed types)
    ---
    tags:
      - Learning
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            properties:
              lang:
                type: string
    responses:
      200:
        description: Quiz started
    """
    global QUIZ_COUNTER, QUIZZES

    data = request.get_json() or {}
    lang = data.get("lang", "en")
    maqamet = Maqam.query.all()
    if not maqamet:
        return jsonify({"error": "no maqamet in database"}), 500

    bank = make_question_bank(maqamet)
    if not bank:
        return jsonify({"error": "no questions available"}), 500

    selected = bank[:20] if len(bank) >= 20 else bank
    for idx, q in enumerate(selected):
        q["index"] = idx

    quiz_id = QUIZ_COUNTER
    QUIZ_COUNTER += 1
    QUIZZES[quiz_id] = {
        "id": quiz_id,
        "lang": lang,
        "questions": selected,
    }
    return jsonify({
        "quiz_id": quiz_id,
        "count": len(selected),
        "questions": selected,
    }), 200


@learning_bp.route("/quiz/<int:quiz_id>/answer", methods=["POST"])
@require_jwt(roles=["admin", "expert", "learner"])
def learning_quiz_answer(quiz_id):
    """
    Submit quiz answers
    ---
    tags:
      - Learning
    parameters:
      - in: path
        name: quiz_id
        schema:
          type: integer
        required: true
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            properties:
              answers:
                type: array
                items:
                  type: string
    responses:
      200:
        description: Quiz results
    """
    quiz = QUIZZES.get(quiz_id)
    if not quiz:
        return jsonify({"error": "quiz not found"}), 404
    data = request.get_json() or {}
    answers = data.get("answers")
    user_id = request.jwt_payload.get("email", "anonymous")
    if not isinstance(answers, list):
        return jsonify({"error": "answers list is required"}), 400
    questions = quiz["questions"]
    total = len(questions)
    correct_count = 0
    detailed = []
    for idx, q in enumerate(questions):
        user_answer = answers[idx] if idx < len(answers) else None
        correct_answer = q["answer"]
        is_correct = False
        if q["type"] == "open":
            is_correct = str(user_answer or "").strip().lower() == str(correct_answer or "").strip().lower()
        else:
            is_correct = user_answer == correct_answer
        if is_correct:
            correct_count += 1
        m = db.session.get(Maqam, q.get("maqam_id")) if q.get("maqam_id") else None
        detailed.append({
            "question": q["prompt"],
            "question_type": q["type"],
            "choices": q.get("choices"),
            "user_answer": user_answer,
            "correct_answer": correct_answer,
            "is_correct": is_correct,
            "explanation": {
                "maqam_en": m.name_en if m else None,
                "emotion_en": m.emotion if m else None,
                "regions": json.loads(m.regions_json) if m and m.regions_json else [],
                "usage": m.usage if m else None,
            }
        })
    score = correct_count / total if total else 0
    update_quiz_stats(user_id, score)

    return jsonify({
        "quiz_id": quiz_id,
        "score": score,
        "correct": correct_count,
        "total": total,
        "details": detailed,
    }), 200


@learning_bp.route("/quiz/mcq/start", methods=["POST"])
@require_jwt(roles=["admin", "expert", "learner"])
def start_mcq_quiz():
    """
    Start a speed MCQ quiz
    ---
    tags:
      - Learning
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            properties:
              topic:
                type: string
    responses:
      200:
        description: MCQ quiz
    """
    data = request.get_json() or {}
    topic = data.get("topic", "emotion")
    maqamet = Maqam.query.all()
    random.shuffle(maqamet)
    questions = []
    for m in maqamet:
        if len(questions) >= 7:
            break
        choices = []
        correct = None
        if topic == "emotion":
            correct = m.emotion
            pool = [x.emotion for x in maqamet if x.emotion and x.id != m.id]
        elif topic == "region":
            regions = json.loads(m.regions_json) if m.regions_json else []
            correct = regions[0] if regions else None
            pool = []
            for x in maqamet:
                pool += json.loads(x.regions_json) if x.regions_json else []
        else:
            usages = [u.strip() for u in (m.usage or "").split(",") if u.strip()]
            correct = usages[0] if usages else None
            pool = []
            for x in maqamet:
                pool += [u.strip() for u in (x.usage or "").split(",") if u.strip()]
        pool = [p for p in pool if p]
        choices = build_mcq_choices(correct, pool)
        if correct and len(choices) >= 2:
            questions.append({
                "maqam_id": m.id,
                "question": f"What is the {topic} of {m.name_en}?",
                "choices": choices,
                "answer": correct,
            })
    return jsonify({"count": len(questions), "questions": questions}), 200


@learning_bp.route("/matching", methods=["GET"])
@require_jwt(roles=["admin", "expert", "learner"])
def learning_matching_game():
    """
    Get matching game pairs
    ---
    tags:
      - Learning
    parameters:
      - in: query
        name: topic
        schema:
          type: string
        required: false
        description: Matching topic (emotion, region, usage)
    responses:
      200:
        description: Matching game data
    """
    topic = request.args.get("topic", "emotion")
    maqamet = Maqam.query.all()
    left = []
    right = []
    pairs = []
    sample = random.sample(maqamet, min(7, len(maqamet)))
    for m in sample:
        left.append({"id": m.id, "name": m.name_en})
        if topic == "emotion":
            val = m.emotion
        elif topic == "region":
            val = (json.loads(m.regions_json) if m.regions_json else [None])[0]
        else:
            val = (m.usage or "").split(",")[0] if m.usage else None
        val = val or "Unknown"
        right.append(val)
        pairs.append({"maqam_id": m.id, "value": val})
    right_shuffled = random.sample(right, len(right)) if right else []
    return jsonify({"left": left, "right": right_shuffled, "solution": pairs}), 200


@learning_bp.route("/audio-recognition", methods=["GET"])
@require_jwt(roles=["admin", "expert", "learner"])
def audio_recognition_game():
    """
    Get audio recognition game
    ---
    tags:
      - Learning
    responses:
      200:
        description: Audio recognition game
    """
    maqamet = [m for m in Maqam.query.all() if m.audio_url]
    if not maqamet:
        return jsonify({"error": "no audio available"}), 400
    choices = random.sample(maqamet, min(4, len(maqamet)))
    target = random.choice(choices)
    return jsonify({
        "audio_url": target.audio_url,
        "choices": [{"id": m.id, "name": m.name_en} for m in choices],
        "answer_id": target.id
    }), 200


@learning_bp.route("/audio-recognition/all", methods=["GET"])
@require_jwt(roles=["admin", "expert", "learner"])
def audio_recognition_playlist():
    """
    Get all audio tracks for recognition game
    ---
    tags:
      - Learning
    responses:
      200:
        description: Audio recognition playlist
    """
    maqamet = [m for m in Maqam.query.all() if m.audio_url]
    if not maqamet:
        return jsonify({"error": "no audio available"}), 400
    random.shuffle(maqamet)
    return jsonify({
        "tracks": [{"id": m.id, "name": m.name_en, "audio_url": m.audio_url} for m in maqamet]
    }), 200


@learning_bp.route("/clue-game", methods=["GET"])
@require_jwt(roles=["admin", "expert", "learner"])
def clue_game():
    """
    Get a clue puzzle for a maqam
    ---
    tags:
      - Learning
    responses:
      200:
        description: Clue puzzle
    """
    maqamet = Maqam.query.all()
    if not maqamet:
        return jsonify({"error": "no maqamet"}), 400
    m = random.choice(maqamet)
    clues = []
    if m.emotion: clues.append(f"Emotion: {m.emotion}")
    if m.usage: clues.append(f"Usage: {m.usage}")
    if m.difficulty_label: clues.append(f"Level: {m.difficulty_label}")
    regions_disp = ", ".join(json.loads(m.regions_json)) if m.regions_json else ""
    if regions_disp: clues.append(f"Region(s): {regions_disp}")
    if hasattr(m, "ajnas_json") and m.ajnas_json:
        try:
            ajnas = json.loads(m.ajnas_json)
            ajnas_names = []
            for a in ajnas:
                nm = a.get("name")
                if isinstance(nm, dict):
                    nm = nm.get("en") or nm.get("ar")
                if nm:
                    ajnas_names.append(nm)
            if ajnas_names:
                clues.append(f"Ajnas: {', '.join(ajnas_names)}")
        except Exception:
            pass
    random.shuffle(clues)
    return jsonify({"clues": clues, "answer": m.name_en, "maqam_id": m.id}), 200


@learning_bp.route("/clue-game/all", methods=["GET"])
@require_jwt(roles=["admin", "expert", "learner"])
def clue_game_all():
    """
    Get all maqamet as clue puzzles for a complete game session
    ---
    tags:
      - Learning
    responses:
      200:
        description: All clue puzzles
    """
    maqamet = Maqam.query.all()
    if not maqamet:
        return jsonify({"error": "no maqamet"}), 400
    random.shuffle(maqamet)
    puzzles = []
    for m in maqamet:
        clues = []
        if m.emotion: clues.append(f"Emotion: {m.emotion}")
        if m.usage: clues.append(f"Usage: {m.usage}")
        if m.difficulty_label: clues.append(f"Level: {m.difficulty_label}")
        regions_disp = ", ".join(json.loads(m.regions_json)) if m.regions_json else ""
        if regions_disp: clues.append(f"Region(s): {regions_disp}")
        if hasattr(m, "ajnas_json") and m.ajnas_json:
            try:
                ajnas = json.loads(m.ajnas_json)
                ajnas_names = []
                for a in ajnas:
                    nm = a.get("name")
                    if isinstance(nm, dict):
                        nm = nm.get("en") or nm.get("ar")
                    if nm:
                        ajnas_names.append(nm)
                if ajnas_names:
                    clues.append(f"Ajnas: {', '.join(ajnas_names)}")
            except Exception:
                pass
        random.shuffle(clues)
        puzzles.append({"clues": clues, "answer": m.name_en, "maqam_id": m.id})
    return jsonify({"puzzles": puzzles, "total": len(puzzles)}), 200


@learning_bp.route("/order-notes", methods=["GET"])
@require_jwt(roles=["admin", "expert", "learner"])
def order_notes_game():
    """
    Get a sequencer puzzle for a maqam
    ---
    tags:
      - Learning
    parameters:
      - in: query
        name: maqam_id
        schema:
          type: integer
        required: false
        description: Maqam ID
    responses:
      200:
        description: Sequencer puzzle
    """
    maqam_id = request.args.get("maqam_id")
    maqamet = Maqam.query.all()
    m = None
    if maqam_id:
        m = db.session.get(Maqam, int(maqam_id))
    if not m and maqamet:
        m = random.choice(maqamet)
    if not m:
        return jsonify({"error": "no maqamet"}), 400
    try:
        ajnas = json.loads(m.ajnas_json) if hasattr(m, "ajnas_json") and m.ajnas_json else []
        notes = []
        for a in ajnas:
            if isinstance(a.get("notes"), dict):
                notes += a.get("notes", {}).get("en", [])
            elif isinstance(a.get("notes"), list):
                notes += a.get("notes", [])
        notes = [n for n in notes if n]
        if not notes:
            return jsonify({"error": "no notes"}), 400
        correct_order = notes
        return jsonify({"maqam_id": m.id, "name": m.name_en, "notes": notes, "solution": correct_order}), 200
    except Exception:
        return jsonify({"error": "no notes"}), 400


@learning_bp.route("/order-notes/all", methods=["GET"])
@require_jwt(roles=["admin", "expert", "learner"])
def order_notes_all():
    """
    Get all maqamet as sequencer puzzles for a complete game session
    ---
    tags:
      - Learning
    responses:
      200:
        description: All sequencer puzzles
    """
    maqamet = Maqam.query.all()
    if not maqamet:
        return jsonify({"error": "no maqamet"}), 400
    random.shuffle(maqamet)
    puzzles = []
    for m in maqamet:
        try:
            ajnas = json.loads(m.ajnas_json) if hasattr(m, "ajnas_json") and m.ajnas_json else []
            notes = []
            for a in ajnas:
                if isinstance(a.get("notes"), dict):
                    notes += a.get("notes", {}).get("en", [])
                elif isinstance(a.get("notes"), list):
                    notes += a.get("notes", [])
            notes = [n for n in notes if n]
            if notes:
                puzzles.append({"maqam_id": m.id, "name": m.name_en, "notes": notes, "solution": notes})
        except Exception:
            pass
    return jsonify({"puzzles": puzzles, "total": len(puzzles)}), 200


@learning_bp.route("/odd-one-out", methods=["GET"])
@require_jwt(roles=["admin", "expert", "learner"])
def odd_one_out_game():
    """
    Get odd-one-out puzzle
    ---
    tags:
      - Learning
    parameters:
      - in: query
        name: topic
        schema:
          type: string
        required: false
        description: Odd-one-out topic
    responses:
      200:
        description: Odd-one-out puzzle
    """
    topic = request.args.get("topic", "emotion")
    maqamet = Maqam.query.all()
    if len(maqamet) < 4:
        return jsonify({"error": "not enough maqamet"}), 400
    base = random.choice(maqamet)
    picks = []
    odd_one_id = None
    if topic == "emotion":
        group = [m for m in maqamet if m.emotion == base.emotion]
        rest = [m for m in maqamet if m.emotion != base.emotion]
        if len(group) >= 3 and rest:
            picks = random.sample(group, 3) + [random.choice(rest)]
            random.shuffle(picks)
            odd = [m for m in picks if m.emotion != base.emotion]
            odd_one_id = odd[0].id if odd else picks[0].id
        else:
            picks = random.sample(maqamet, 4)
            odd_one_id = picks[0].id
    else:
        picks = random.sample(maqamet, 4)
        odd_one_id = picks[0].id
    return jsonify({
        "choices": [{"id": m.id, "name": m.name_en} for m in picks],
        "odd_one_id": odd_one_id
    }), 200


@learning_bp.route("/complete-activity", methods=["POST"])
@require_jwt(roles=["admin", "expert", "learner"])
def learning_complete_activity():
        """
        Log an activity completion for a maqam
        ---
        tags:
            - Learning
        requestBody:
            required: true
            content:
                application/json:
                    schema:
                        type: object
                        properties:
                            maqam_id:
                                type: integer
                            user_id:
                                type: string
                            activity:
                                type: string
        responses:
            200:
                description: Activity logged
        """
        data = request.get_json() or {}
        maqam_id = data.get("maqam_id")
        user_id = data.get("user_id") or request.jwt_payload.get("email", "anonymous")
        activity = data.get("activity")
        if not all([maqam_id, user_id, activity]):
                return jsonify({"error": "missing"}), 400
        record_activity(user_id, int(maqam_id), activity)
        stat = get_or_create_user_stat(user_id)
        return jsonify({"ok": True, "progress": stat.activities}), 200


@learning_bp.route("/leaderboard", methods=["GET"])
def learning_leaderboard():
    """
    Get leaderboard combining quiz scores and activity counts
    ---
    tags:
      - Learning
    responses:
      200:
        description: Leaderboard
    """
    stats = UserStat.query.order_by(UserStat.best_score.desc(), UserStat.quizzes.desc(), UserStat.activities.desc()).all()
    board = [{
        "user_id": s.user_id,
        "best_score": s.best_score or 0.0,
        "quizzes": s.quizzes or 0,
        "activities": s.activities or 0,
        "level": s.level or "beginner",
    } for s in stats]
    return jsonify({"leaderboard": board}), 200


@learning_bp.route("/activity-log", methods=["GET"])
@require_jwt(roles=["admin", "expert", "learner"])
def learning_activity_log():
    """
    List recent activity completions
    ---
    tags:
      - Learning
    parameters:
      - in: query
        name: user_id
        schema:
          type: string
        required: false
        description: User ID
      - in: query
        name: limit
        schema:
          type: integer
        required: false
        description: Limit number of results
    responses:
      200:
        description: Activity log
    """
    q_user = request.args.get("user_id")
    limit = int(request.args.get("limit", 50) or 50)
    caller = request.jwt_payload.get("email", "anonymous")
    caller_role = request.jwt_payload.get("role", "learner")

    if q_user:
        if caller_role == "learner" and q_user != caller:
            return jsonify({"error": "forbidden"}), 403
        user_filter = q_user
    else:
        user_filter = caller

    query = ActivityLog.query.filter_by(user_id=user_filter).order_by(ActivityLog.created_at.desc())
    if limit > 0:
        query = query.limit(limit)
    rows = query.all()
    return jsonify({
        "user_id": user_filter,
        "count": len(rows),
        "activities": [
            {"id": r.id, "maqam_id": r.maqam_id, "activity": r.activity, "created_at": r.created_at.isoformat()}
            for r in rows
        ]
    }), 200
