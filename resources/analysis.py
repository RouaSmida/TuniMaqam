import os
import time
from flask import Blueprint, jsonify, request, current_app

from services.auth_service import require_jwt
from services.analysis_service import analyze_notes_core

analysis_bp = Blueprint('analysis', __name__, url_prefix='/analysis')


@analysis_bp.route("/notes", methods=["POST"])
@require_jwt(roles=["admin", "expert", "learner"])
def analyze_notes():
    """
    Analyze notes and suggest maqamet
    ---
    tags:
      - Analysis
    security:
      - Bearer: []
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            notes:
              type: array
              items: {type: string}
            optional_mood:
              type: string
    responses:
      200:
        description: Candidates
      400:
        description: Validation error
      401:
        description: Unauthorized
    """
    data = request.get_json() or {}
    notes = data.get("notes")
    optional_mood = data.get("optional_mood")
    if not notes or not isinstance(notes, list):
        return jsonify({"error": "notes list is required"}), 400
    candidates = analyze_notes_core(notes, optional_mood)
    return jsonify({"candidates": candidates}), 200


@analysis_bp.route("/audio", methods=["POST"])
@require_jwt(roles=["admin", "expert", "learner"])
def analyze_audio():
    """
    Analyze audio and infer maqam candidates
    ---
    tags:
      - Analysis
    consumes:
      - multipart/form-data
    parameters:
      - in: formData
        name: audio
        type: file
        required: true
        description: WAV/MP3 audio file
      - in: formData
        name: optional_mood
        type: string
        required: false
    security:
      - Bearer: []
    responses:
      200:
        description: Extracted notes and maqam candidates
      400:
        description: Missing audio
      401:
        description: Unauthorized
      500:
        description: Missing AssemblyAI key
    """
    file = request.files.get("audio")
    form = request.form.to_dict() if request.form else {}
    optional_mood = form.get("optional_mood")
    if not file:
        return jsonify({"error": "audio file is required (field 'audio')"}), 400

    api_key = current_app.config.get("ASSEMBLYAI_API_KEY") or os.getenv("ASSEMBLYAI_API_KEY")
    api_url = current_app.config.get("ASSEMBLYAI_API_URL", "https://api.assemblyai.com/v2") or os.getenv("ASSEMBLYAI_API_URL", "https://api.assemblyai.com/v2")

    # Graceful fallback if key missing (for demo/offline usage)
    if not api_key:
        extracted_notes = ["C", "D", "E", "G"]
        candidates = analyze_notes_core(extracted_notes, optional_mood)
        return jsonify({"extracted_notes": extracted_notes, "candidates": candidates, "warning": "ASSEMBLYAI_API_KEY not configured, used fallback notes"}), 200

    import requests
    headers = {"authorization": api_key}

    upload_resp = requests.post(f"{api_url}/upload", headers=headers, data=file.stream)
    if upload_resp.status_code != 200:
        return jsonify({"error": "audio upload failed"}), 502
    upload_url = upload_resp.json().get("upload_url")

    payload = {"audio_url": upload_url, "punctuate": False}
    transcribe_resp = requests.post(f"{api_url}/transcript", json=payload, headers=headers)
    if transcribe_resp.status_code != 200:
        return jsonify({"error": "transcription request failed"}), 502
    transcript_id = transcribe_resp.json().get("id")

    words = []
    for _ in range(30):
        status_resp = requests.get(f"{api_url}/transcript/{transcript_id}", headers=headers)
        status_json = status_resp.json()
        st = status_json.get("status")
        if st == "completed":
            words = status_json.get("words", []) or []
            break
        if st == "error":
            return jsonify({"error": "transcription failed"}), 502
        time.sleep(2)
    else:
        return jsonify({"error": "transcription timeout"}), 504

    raw_tokens = [w.get("text", "") for w in words]
    allowed = {"A","B","C","D","E","F","G","AB","BB","CB","DB","EB","FB","GB","A#","C#","D#","F#","G#","BB","EB","AB","DB","GB","Bb","Eb","Ab","Db","Gb"}
    extracted_notes = [t.strip().upper() for t in raw_tokens if t.strip().upper() in allowed]
    if not extracted_notes:
        extracted_notes = ["C", "D", "E", "G"]

    candidates = analyze_notes_core(extracted_notes, optional_mood)
    return jsonify({"extracted_notes": extracted_notes, "candidates": candidates}), 200
