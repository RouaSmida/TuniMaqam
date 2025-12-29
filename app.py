import os
import json
import time
import random
import jwt
from functools import wraps
from flasgger import Swagger
from flask import Flask, jsonify, request, redirect, send_from_directory, url_for
from authlib.integrations.flask_client import OAuth
from dotenv import load_dotenv
from werkzeug.utils import secure_filename

# Load .env before loading Config so env vars are visible
load_dotenv()

from config import Config
from extensions import db

# Pull settings from Config
JWT_SECRET = Config.JWT_SECRET
JWT_ALG = Config.JWT_ALG
JWT_EXP_SECONDS = Config.JWT_EXP_SECONDS

# --- In-memory quiz storage ---
QUIZZES = {}
QUIZ_COUNTER = 1


def issue_token(sub, role="learner", email=None):
    now = int(time.time())
    payload = {
        "sub": sub,
        "role": role,
        "email": email,
        "iat": now,
        "exp": now + JWT_EXP_SECONDS,
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALG)


def require_jwt(roles=None):
    """
    Decorator to require a valid JWT token.
    If roles is provided, the token's role must be in that list.
    """
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            auth = request.headers.get("Authorization", "")
            if not auth.startswith("Bearer "):
                return jsonify({"error": "Unauthorized - No token provided"}), 401

            token = auth.replace("Bearer ", "", 1).strip()
            try:
                payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])
            except jwt.ExpiredSignatureError:
                return jsonify({"error": "Token expired"}), 401
            except jwt.InvalidTokenError:
                return jsonify({"error": "Invalid token"}), 401
            except Exception:
                return jsonify({"error": "Token validation failed"}), 401

            user_role = payload.get("role", "learner")
            if roles and user_role not in roles:
                return jsonify({
                    "error": "Forbidden - Insufficient permissions",
                    "your_role": user_role,
                    "required_roles": roles
                }), 403

            request.jwt_payload = payload
            return f(*args, **kwargs)
        return wrapper
    return decorator


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    app.secret_key = app.config["SECRET_KEY"]
    db.init_app(app)

    # Swagger setup
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
                "description": "JWT Authorization header using the Bearer scheme. Example: \"Bearer {token}\""
            }
        }
    }
    Swagger(app, template=swagger_template)

    from models import Maqam, MaqamContribution

    # OAuth setup
    oauth = OAuth(app)
    oauth.register(
        name="google",
        client_id=app.config["GOOGLE_CLIENT_ID"],
        client_secret=app.config["GOOGLE_CLIENT_SECRET"],
        server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
        client_kwargs={"scope": "openid email profile"},
    )

    global QUIZZES  # fix typo
    QUIZZES = QUIZZES

    with app.app_context():
        db.create_all()

    # ========== AUTH ROUTES ==========

    @app.route("/auth/google/login")
    def auth_google_login():
        """
        Google OAuth login
        ---
        tags:
          - Auth
        responses:
          302:
            description: Redirect to Google OAuth
        """
        redirect_uri = app.config["OAUTH_REDIRECT_URI"]
        return oauth.google.authorize_redirect(redirect_uri)

    @app.route("/auth/google/callback")
    def auth_google_callback():
        """
        Google OAuth callback
        ---
        tags:
          - Auth
        responses:
          200:
            description: Returns bearer token (HTML or JSON)
        """
        token = oauth.google.authorize_access_token()
        userinfo = token.get("userinfo")
        if not userinfo or "email" not in userinfo:
            return jsonify({"error": "Failed to retrieve user info"}), 400

        email = userinfo["email"]
        if email in app.config["AUTH_ADMIN_EMAILS"]:
            role = "admin"
        elif email in app.config["AUTH_EXPERT_EMAILS"]:
            role = "expert"
        elif not app.config["AUTH_ALLOWED_EMAILS"] or email in app.config["AUTH_ALLOWED_EMAILS"]:
            role = app.config["AUTH_DEFAULT_ROLE"]
        else:
            return jsonify({"error": "Email not allowed"}), 403

        jwt_token = issue_token(sub=email, role=role, email=email)

        if request.accept_mimetypes.accept_html or request.args.get("ui") == "1":
            role_lower = role.lower()
            email_lower = email.lower()
            return f"""
            <!doctype html>
            <html lang="en">
            <head>
              <meta charset="utf-8" />
              <meta name="viewport" content="width=device-width, initial-scale=1.0" />
              <title>TuniMaqam Token</title>
              
              <!-- TYPOGRAPHY: Matches Main App (Reem Kufi, Inter, Outfit) -->
              <link rel="preconnect" href="https://fonts.googleapis.com">
              <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
              <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Outfit:wght@300;500;700;800&family=Reem+Kufi+Fun:wght@400..700&display=swap" rel="stylesheet">
              
              <style>
                :root {{
                  /* THEME: Sunlit Sidi Bou Said (Exact match to main app) */
                  --bg-base: #f8fafc;
                  --glass-surface: rgba(255, 255, 255, 0.75);
                  --glass-border: rgba(14, 165, 233, 0.2);
                  --glass-hover: rgba(255, 255, 255, 0.95);
                  
                  --sidi-blue: #0ea5e9;
                  --sidi-dark-blue: #0369a1;
                  --accent-gold: #f59e0b;
                  --accent-rose: #e11d48;
                  
                  --text-main: #0f172a;
                  --text-muted: #475569;
                  
                  --font-display: 'Reem Kufi Fun', sans-serif;
                  --font-tech: 'Inter', sans-serif;
                  
                  --shadow-card: 0 10px 30px -10px rgba(14, 165, 233, 0.15);
                }}

                * {{ box-sizing: border-box; }}
                
                body {{
                  margin: 0; min-height: 100vh;
                  font-family: var(--font-tech);
                  background-color: var(--bg-base);
                  background-image: linear-gradient(to bottom, #f0f9ff, #f8fafc);
                  color: var(--text-main);
                  display: flex; align-items: center; justify-content: center;
                  padding: 24px; position: relative; overflow: hidden;
                }}

                /* GRID OVERLAY */
                body::before {{
                  content: "";
                  position: absolute; inset: 0; z-index: 0;
                  background-image: 
                    linear-gradient(rgba(14, 165, 233, 0.08) 1px, transparent 1px),
                    linear-gradient(90deg, rgba(14, 165, 233, 0.08) 1px, transparent 1px);
                  background-size: 40px 40px;
                  mask-image: radial-gradient(circle at center, black 40%, transparent 85%);
                  -webkit-mask-image: radial-gradient(circle at center, black 40%, transparent 85%);
                  pointer-events: none;
                }}

                .card {{
                  position: relative; z-index: 1;
                  width: min(600px, 94vw);
                  background: var(--glass-surface);
                  border: 1px solid var(--glass-border);
                  border-radius: 20px;
                  padding: 32px;
                  box-shadow: var(--shadow-card);
                  backdrop-filter: blur(12px);
                  text-align: center;
                  transition: transform 0.2s ease, box-shadow 0.2s ease;
                }}
                .card:hover {{
                  transform: translateY(-4px);
                  background: var(--glass-hover);
                  box-shadow: 0 15px 40px -10px rgba(14, 165, 233, 0.25);
                  border-color: var(--sidi-blue);
                }}

                /* LOGO IMAGE */
                .logo-img {{
                  width: 60px; height: 60px;
                  border-radius: 50%;
                  object-fit: cover;
                  border: 3px solid var(--sidi-blue);
                  margin-bottom: 16px;
                  box-shadow: 0 4px 12px rgba(14, 165, 233, 0.2);
                }}

                h1 {{
                  margin: 0 0 8px;
                  font-family: var(--font-display);
                  font-weight: 700;
                  font-size: 2rem;
                  color: var(--sidi-dark-blue);
                }}

                .sub {{ margin: 0 0 24px; color: var(--text-muted); font-size: 1rem; line-height: 1.5; }}

                .pills {{ display: flex; gap: 10px; justify-content: center; flex-wrap: wrap; margin-bottom: 24px; }}
                .pill {{
                  display: inline-flex; align-items: center; gap: 8px;
                  padding: 8px 16px; border-radius: 99px;
                  font-weight: 600; font-size: 0.9rem;
                  background: #fff; 
                  color: var(--sidi-dark-blue);
                  border: 1px solid var(--glass-border);
                  box-shadow: 0 2px 5px rgba(0,0,0,0.05);
                }}
                .pill span {{ font-weight: 400; color: var(--text-muted); }}

                .label {{ 
                    font-size: 0.85rem; 
                    font-weight: 700; 
                    color: var(--sidi-blue); 
                    text-transform: uppercase; 
                    margin: 0 0 8px; 
                    text-align: left; 
                }}

                textarea {{
                  width: 100%;
                  min-height: 100px;
                  background: #fff;
                  color: var(--text-muted);
                  border: 1px solid #cbd5e1;
                  border-radius: 12px;
                  padding: 14px;
                  font-family: 'SFMono-Regular', Consolas, monospace;
                  font-size: 0.85rem;
                  line-height: 1.4;
                  resize: vertical;
                  margin-bottom: 24px;
                  box-shadow: inset 0 2px 4px rgba(0,0,0,0.02);
                }}
                textarea:focus {{
                    outline: none;
                    border-color: var(--sidi-blue);
                    box-shadow: 0 0 0 3px rgba(14, 165, 233, 0.15);
                    color: var(--text-main);
                }}

                .row {{ display: flex; gap: 12px; justify-content: center; }}

                .btn {{
                  cursor: pointer; border-radius: 10px;
                  padding: 12px 24px; font-weight: 700; font-size: 1rem;
                  font-family: var(--font-tech);
                  text-transform: uppercase; letter-spacing: 0.5px;
                  transition: all 0.2s ease;
                  width: 100%;
                }}
                
                /* Primary Action (Copy) */
                .btn.primary {{
                  background: linear-gradient(135deg, var(--sidi-blue), var(--sidi-dark-blue));
                  color: #fff;
                  border: none;
                  box-shadow: 0 4px 15px rgba(3, 105, 161, 0.2);
                }}
                .btn.primary:hover {{
                  transform: translateY(-2px);
                  box-shadow: 0 8px 25px rgba(3, 105, 161, 0.3);
                }}

                /* Secondary Action (Open App) */
                .btn.secondary {{
                  background: transparent;
                  border: 1px solid #cbd5e1;
                  color: var(--text-muted);
                }}
                .btn.secondary:hover {{
                  color: var(--sidi-dark-blue);
                  border-color: var(--sidi-blue);
                  background: rgba(14, 165, 233, 0.05);
                }}

              </style>
            </head>
            <body>
              <div class="card">
                <!-- SIDI BOU SAID IMAGE -->
                <img class="logo-img" src="https://img.freepik.com/premium-photo/vertical-shot-blue-door-sidi-bou-said-located-tunisia_665346-16824.jpg" alt="Logo" />
                
                <h1>Access Granted</h1>
                <p class="sub">Welcome to TuniMaqam. Use this token to authenticate your session.</p>
                
                <div class="pills">
                  <div class="pill"><span>Role:</span> {role_lower}</div>
                  <div class="pill"><span>Email:</span> {email_lower}</div>
                </div>

                <div class="label">Your JWT Token</div>
                <textarea id="tok" readonly>{jwt_token}</textarea>

                <div class="row">
                  <button class="btn primary" onclick="copyToken()">Copy Token</button>
                  <button class="btn secondary" onclick="window.location.href='/'">Enter App</button>
                </div>
              </div>

              <script>
                function copyToken() {{
                    var copyText = document.getElementById("tok");
                    copyText.select();
                    copyText.setSelectionRange(0, 99999); 
                    navigator.clipboard.writeText(copyText.value);
                    
                    // Simple visual feedback on button
                    var btn = document.querySelector('.btn.primary');
                    var original = btn.innerText;
                    btn.innerText = "Copied!";
                    btn.style.background = "var(--accent-gold)"; // Gold feedback
                    setTimeout(() => {{
                        btn.innerText = original;
                        btn.style.background = ""; 
                    }}, 2000);
                }}
              </script>
            </body>
            </html>
            """
        return jsonify({
            "access_token": jwt_token,
            "token_type": "Bearer",
            "expires_in": JWT_EXP_SECONDS,
            "role": role,
            "email": email
        }), 200

    @app.route("/auth/whoami", methods=["GET"])
    @require_jwt(roles=["admin", "expert", "learner"])
    def whoami():
        """
        Who am I (JWT payload)
        ---
        tags:
          - Auth
        security:
          - Bearer: []
        responses:
          200:
            description: JWT payload data
        """
        p = request.jwt_payload
        return jsonify({
            "email": p.get("email"),
            "role": p.get("role"),
            "exp": p.get("exp"),
            "iat": p.get("iat"),
            "sub": p.get("sub"),
        }), 200

    # ========== PUBLIC ROUTES ==========

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
        maqamet_count = Maqam.query.count()
        contributions_count = MaqamContribution.query.count()
        return jsonify({
            "services": ["knowledge", "learning", "recommendation", "analysis"],
            "maqamet_count": maqamet_count,
            "contributions_count": contributions_count
        }), 200

    # ========== KNOWLEDGE ROUTES (PUBLIC READ) ==========

    @app.route("/knowledge/maqam", methods=["GET"])
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

        result = []
        for m in Maqam.query.all():
            regions = json.loads(m.regions_json) if m.regions_json else []
            if region in regions:
                result.append(m.to_dict_full())
        return jsonify(result), 200


    @app.route("/knowledge/maqam/<int:maqam_id>", methods=["GET"])
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
        maqam = Maqam.query.get(maqam_id)
        if not maqam:
            return jsonify({"error": "Maqam not found"}), 404
        return jsonify(maqam.to_dict_full()), 200


    @app.route("/knowledge/maqam/by-name/<string:name_en>", methods=["GET"])
    def get_maqam_by_name(name_en):
        """
        Get maqam by English name
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
        maqam = Maqam.query.filter_by(name_en=name_en).first()
        if not maqam:
            return jsonify({"error": "Maqam not found"}), 404
        return jsonify(maqam.to_dict_full()), 200


    @app.route("/knowledge/maqam/<string:name_en>/related", methods=["GET"])
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
        base = Maqam.query.filter_by(name_en=name_en).first()
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


    @app.route("/knowledge/regions", methods=["GET"])
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

    # ========== CONTRIBUTION ROUTES (PROTECTED) ==========

    @app.route("/knowledge/maqam/<int:maqam_id>/contributions", methods=["POST"])
    @require_jwt(roles=["admin", "expert", "learner"])
    def add_maqam_contribution(maqam_id):
        """
        Add contribution to a maqam
        ---
        tags:
          - Contributions
        security:
          - Bearer: []
        parameters:
          - in: path
            name: maqam_id
            type: integer
            required: true
          - in: body
            name: body
            required: true
            schema:
              type: object
              properties:
                type: {type: string}
                payload: {type: object}
        responses:
          201:
            description: Contribution created (pending)
          400:
            description: Validation error
          404:
            description: Maqam not found
        """
        maqam = Maqam.query.get(maqam_id)
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

    @app.route("/knowledge/maqam/<int:maqam_id>/contributions", methods=["GET"])
    def list_maqam_contributions(maqam_id):
        """
        List contributions for a maqam
        ---
        tags:
          - Contributions
        parameters:
          - in: path
            name: maqam_id
            type: integer
            required: true
        responses:
          200:
            description: List of contributions
          404:
            description: Maqam not found
        """
        maqam = Maqam.query.get(maqam_id)
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

    @app.route("/knowledge/contributions/<int:contrib_id>/review", methods=["POST"])
    @require_jwt(roles=["admin"])
    def review_contribution(contrib_id):
        """
        Review a contribution (accept/reject)
        ---
        tags:
          - Contributions
        security:
          - Bearer: []
        parameters:
          - in: path
            name: contrib_id
            type: integer
            required: true
          - in: body
            name: body
            required: true
            schema:
              type: object
              properties:
                status:
                  type: string
                  enum: ["accepted", "rejected"]
        responses:
          200:
            description: Updated status
          400:
            description: Invalid status
          404:
            description: Contribution not found
        """
        contrib = MaqamContribution.query.get(contrib_id)
        if not contrib:
            return jsonify({"error": "Contribution not found"}), 404

        data = request.get_json() or {}
        new_status = data.get("status")

        if new_status not in ["accepted", "rejected"]:
            return jsonify({"error": "status must be 'accepted' or 'rejected'"}), 400

        contrib.status = new_status
        db.session.commit()
        return jsonify({"id": contrib.id, "status": contrib.status}), 200

    @app.route("/knowledge/maqam/<int:maqam_id>/audio", methods=["POST"])
    @require_jwt(roles=["admin", "expert"])
    def upload_maqam_audio(maqam_id):
        """
        Upload an audio clip for a maqam (stored as static file)
        ---
        tags:
          - Knowledge
        consumes:
          - multipart/form-data
        parameters:
          - in: path
            name: maqam_id
            type: integer
            required: true
          - in: formData
            name: audio
            type: file
            required: true
            description: WAV/MP3 audio file
        security:
          - Bearer: []
        responses:
          200:
            description: Audio stored; returns URL
            schema:
              type: object
              properties:
                audio_url: { type: string }
          400:
            description: No file
          401:
            description: Unauthorized
          404:
            description: Maqam not found
        """
        maqam = Maqam.query.get(maqam_id)
        if not maqam:
            return jsonify({"error": "maqam not found"}), 404

        file = request.files.get("audio")
        if not file:
            return jsonify({"error": "audio file is required"}), 400

        filename = secure_filename(file.filename)
        if not filename:
            return jsonify({"error": "invalid filename"}), 400

        save_dir = os.path.join(app.root_path, "static", "audio")
        os.makedirs(save_dir, exist_ok=True)
        save_path = os.path.join(save_dir, filename)
        file.save(save_path)

        audio_url = url_for("static", filename=f"audio/{filename}", _external=True)

        # Persist on this maqam
        maqam.audio_url = audio_url
        db.session.commit()

        return jsonify({"audio_url": audio_url}), 200


    # ========== ANALYSIS ROUTES (PROTECTED) ==========

    def normalize_note(note):
        if not note:
            return ""
        return ''.join([c for c in str(note).upper() if c.isalpha() or c in ['#', 'B', '-']]).strip()

    def analyze_notes_core(notes, optional_mood=None):
        input_notes = {normalize_note(n) for n in notes if n}
        candidates = []
        for m in Maqam.query.all():
            ajnas = json.loads(m.ajnas_json) if m.ajnas_json else []
            all_pattern_notes = set()
            for jins in ajnas:
                jins_notes = jins.get("notes", {})
                if isinstance(jins_notes, dict):
                    en_notes = jins_notes.get("en", [])
                    for n in en_notes:
                        all_pattern_notes.add(normalize_note(n))
                elif isinstance(jins_notes, list):
                    for n in jins_notes:
                        all_pattern_notes.add(normalize_note(n))
            if not all_pattern_notes:
                continue
            common = input_notes & all_pattern_notes
            if not common:
                continue
            overlap = len(common) / len(input_notes) if input_notes else 0
            confidence = round(overlap, 2)
            evidence = ["interval_pattern_match"]
            if optional_mood and m.emotion == optional_mood:
                confidence = min(1.0, confidence + 0.1)
                evidence.append("emotion_alignment")

            candidates.append({
                "maqam": m.name_en,
                "maqam_ar": m.name_ar,
                "confidence": confidence,
                "reason": f"Matched {len(common)} of {len(input_notes)} input notes with stored patterns",
                "evidence": evidence,
                "matched_notes": list(common)
            })
        candidates.sort(key=lambda c: c["confidence"], reverse=True)
        return candidates[:3]

    @app.route("/analysis/notes", methods=["POST"])
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

    @app.route("/analysis/audio", methods=["POST"])
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

        api_key = app.config.get("ASSEMBLYAI_API_KEY") or os.getenv("ASSEMBLYAI_API_KEY")
        api_url = app.config.get("ASSEMBLYAI_API_URL", "https://api.assemblyai.com/v2") or os.getenv("ASSEMBLYAI_API_URL", "https://api.assemblyai.com/v2")
        if not api_key:
            print("DEBUG: ASSEMBLYAI_API_KEY missing at runtime")
            return jsonify({"error": "ASSEMBLYAI_API_KEY not configured"}), 500

        import requests, time as _t
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
            _t.sleep(2)
        else:
            return jsonify({"error": "transcription timeout"}), 504

        raw_tokens = [w.get("text", "") for w in words]
        allowed = {"A","B","C","D","E","F","G","AB","BB","CB","DB","EB","FB","GB","A#","C#","D#","F#","G#","BB","EB","AB","DB","GB","Bb","Eb","Ab","Db","Gb"}
        extracted_notes = [t.strip().upper() for t in raw_tokens if t.strip().upper() in allowed]
        if not extracted_notes:
            extracted_notes = ["C", "D", "E", "G"]

        candidates = analyze_notes_core(extracted_notes, optional_mood)
        return jsonify({"extracted_notes": extracted_notes, "candidates": candidates}), 200

    # ========== LEARNING ROUTES ==========

    # ========== LEARNING ROUTES ==========

    @app.route("/learning/flashcards", methods=["GET"])
    def learning_flashcards():
        """
        Get flashcards by topic
        ---
        tags:
          - Learning
        parameters:
          - in: query
            name: topic
            type: string
            enum: ["emotion", "region", "usage"]
            required: false
          - in: query
            name: level
            type: string
            required: false
        responses:
          200:
            description: Flashcards
          400:
            description: Invalid topic
        """
        topic = request.args.get("topic", "emotion")
        level = request.args.get("level", "beginner")

        cards = []
        maqamet = Maqam.query.all()

        if topic == "emotion":
            for m in maqamet:
                cards.append({
                    "name_en": m.name_en,
                    "name_ar": m.name_ar,
                    "emotion_en": m.emotion,
                    "emotion_ar": getattr(m, "emotion_ar", None),
                    "regions_en": json.loads(m.regions_json) if m.regions_json else [],
                    "regions_ar": json.loads(getattr(m, "regions_ar_json", "[]") or "[]"),
                    # back: ONLY emotion in English (no usage here)
                    "back": [m.emotion] if m.emotion else [],
                    "level": m.difficulty_label,
                })

        elif topic == "region":
            for m in maqamet:
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
            for m in maqamet:
                usages_en = (m.usage or "").split(",") if m.usage else []
                usages_en = [u.strip() for u in usages_en if u.strip()]

                # make sure usages_ar is a LIST of strings
                if hasattr(m, "usage_ar_json") and m.usage_ar_json:
                    try:
                        usages_ar_list = json.loads(m.usage_ar_json)
                        if isinstance(usages_ar_list, list):
                            usages_ar = [u.strip() for u in usages_ar_list if str(u).strip()]
                        else:
                            usages_ar = []
                    except Exception:
                        usages_ar = []
                else:
                    # fallback: if you only stored a single Arabic usage string, wrap it in a list
                    raw_ar = getattr(m, "usage_ar", None)
                    usages_ar = [raw_ar.strip()] if raw_ar else []

                cards.append({
                    "name_en": m.name_en,
                    "name_ar": m.name_ar,
                    "emotion_en": m.emotion,
                    "emotion_ar": getattr(m, "emotion_ar", None),
                    "usage_en": ", ".join(usages_en),
                    # store Arabic usages as a LIST so frontend can join them
                    "usage_ar_list": usages_ar,
                    "regions_en": json.loads(m.regions_json) if m.regions_json else [],
                    "regions_ar": json.loads(getattr(m, "regions_ar_json", "[]") or "[]"),
                    "back": usages_en,      # English usages on back
                    "level": m.difficulty_label,
                })

        else:
            return jsonify({"error": "invalid topic"}), 400


        return jsonify({"topic": topic, "level": level, "count": len(cards), "cards": cards}), 200


    @app.route("/learning/plan", methods=["GET"])
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
            type: string
            required: false
        responses:
          200:
            description: Learning plan
          401:
            description: Unauthorized
        """
        level = request.args.get("level", "beginner")
        order = {"beginner": 1, "intermediate": 2, "advanced": 3}

        maqamet = Maqam.query.all()
        if not maqamet:
            return jsonify({"level": level, "count": 0, "items": []}), 200

        # Sort by difficulty label
        maqamet.sort(key=lambda m: order.get(getattr(m, "difficulty_label", "advanced"), 3))

        # Optional filter by level if present
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
                    "flashcards_emotion",
                    "flashcards_region",
                    "quiz_emotion"
                ]
            })

        return jsonify({"level": level, "count": len(plan), "items": plan}), 200

    @app.route("/learning/quiz/start", methods=["POST"])
    @require_jwt(roles=["admin", "expert", "learner"])
    def start_quiz():
        """
        Start a quiz
        ---
        tags:
          - Learning
        security:
          - Bearer: []
        parameters:
          - in: body
            name: body
            required: true
            schema:
              type: object
              properties:
                topic:
                  type: string
                  enum: ["emotion", "region", "usage"]
                lang:
                  type: string
                level:
                  type: string
        responses:
          200:
            description: Quiz questions (max ~7)
          401:
            description: Unauthorized
          500:
            description: No maqamet available
        """
        data = request.get_json() or {}
        topic = data.get("topic", "emotion")  # emotion | region | usage
        lang = data.get("lang", "en")
        level = data.get("level", "beginner")

        maqamet = Maqam.query.all()
        if not maqamet:
            return jsonify({"error": "no maqamet in database"}), 500

        random.shuffle(maqamet)
        questions = []

        for m in maqamet:
            if len(questions) >= 7:
                break

            # Pick correct answer based on topic (accepts Arabic naturally because we never transform it)
            if topic == "emotion":
                correct = getattr(m, "emotion", None)
            elif topic == "region":
                regions = json.loads(m.regions_json) if getattr(m, "regions_json", None) else []
                correct = regions[0] if regions else None
            else:  # usage
                usages = (m.usage or "").split(",") if getattr(m, "usage", None) else []
                usages = [u.strip() for u in usages if u.strip()]
                correct = usages[0] if usages else None

            if not correct:
                continue

            # English question text
            text_map_en = {
                "emotion": f"What is the main emotion of {m.name_en}?",
                "region": f"In which region is {m.name_en} used?",
                "usage": f"Give one typical usage of {m.name_en}.",
            }
            question_text_en = text_map_en.get(topic, text_map_en["emotion"])

            # Arabic question text
            text_map_ar = {
                "emotion": f"ما هي أهم العواطف في مقام {m.name_ar}؟" if m.name_ar else None,
                "region": f"في أي منطقة يُستعمل مقام {m.name_ar}؟" if m.name_ar else None,
                "usage": f"اذكر استعمالاً شائعاً لمقام {m.name_ar}." if m.name_ar else None,
            }
            question_text_ar = text_map_ar.get(topic)

            questions.append({
                "maqam_id": m.id,
                "question": question_text_en,
                "question_ar": question_text_ar,
                "maqam_en": m.name_en,
                "maqam_ar": m.name_ar,
                "emotion_en": m.emotion,
                "emotion_ar": getattr(m, "emotion_ar", None),
                "usage_en": m.usage,
                "usage_ar": getattr(m, "usage_ar", None),
                "regions_en": json.loads(m.regions_json) if m.regions_json else [],
                "regions_ar": json.loads(getattr(m, "regions_ar_json", "[]") or "[]"),
                "correct_answer": correct,
                "topic": topic,
                "lang": lang,
            })

        if not questions:
            return jsonify({"error": "no questions available"}), 500

        global QUIZ_COUNTER, QUIZZES
        quiz_id = QUIZ_COUNTER
        QUIZ_COUNTER += 1

        QUIZZES[quiz_id] = {
            "id": quiz_id,
            "topic": topic,
            "level": level,
            "questions": questions,
        }

        for idx, q in enumerate(questions):
            q["index"] = idx

        return jsonify({
            "quiz_id": quiz_id,
            "topic": topic,
            "level": level,
            "count": len(questions),
            "questions": questions,
        }), 200

    @app.route("/learning/quiz/<int:quiz_id>/answer", methods=["POST"])
    @require_jwt(roles=["admin", "expert", "learner"])
    def learning_quiz_answer(quiz_id):
        """
        Submit quiz answers
        ---
        tags:
          - Learning
        security:
          - Bearer: []
        parameters:
          - in: path
            name: quiz_id
            type: integer
            required: true
          - in: body
            name: body
            required: true
            schema:
              type: object
              properties:
                answers:
                  type: array
                  items: {type: string}
        responses:
          200:
            description: Score and details
          400:
            description: Validation error
          404:
            description: Quiz not found
        """
        quiz = QUIZZES.get(quiz_id)
        if not quiz:
            return jsonify({"error": "quiz not found"}), 404

        data = request.get_json() or {}
        answers = data.get("answers")
        if not isinstance(answers, list):
            return jsonify({"error": "answers list is required"}), 400

        questions = quiz["questions"]
        total = len(questions)
        correct_count = 0
        detailed = []

        # User answers can be Arabic or English; just compare raw strings
        for idx, q in enumerate(questions):
            user_answer = answers[idx] if idx < len(answers) else None
            correct_answer = q["correct_answer"]
            is_correct = (user_answer == correct_answer)
            if is_correct:
                correct_count += 1

            m = Maqam.query.get(q["maqam_id"])
            detailed.append({
                "question": q["question"],
                "question_ar": q.get("question_ar"),
                "user_answer": user_answer,
                "correct_answer": correct_answer,
                "is_correct": is_correct,
                "explanation": {
                    "maqam_en": m.name_en if m else None,
                    "maqam_ar": m.name_ar if m else None,
                    "emotion_en": m.emotion if m else None,
                    "emotion_ar": getattr(m, "emotion_ar", None) if m else None,
                }
            })

        score = correct_count / total if total else 0
        return jsonify({
            "quiz_id": quiz_id,
            "topic": quiz["topic"],
            "level": quiz["level"],
            "score": score,
            "correct": correct_count,
            "total": total,
            "details": detailed,
        }), 200

    # ========== RECOMMENDATION ROUTES (PROTECTED) ==========

    # ========== RECOMMENDATION ROUTES (PROTECTED) ==========

    @app.route("/recommendations/maqam", methods=["POST"])
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

        mood = (data.get("mood") or "").lower().strip()
        event = (data.get("event") or "").lower().strip()
        region = (data.get("region") or "").lower().strip()
        time_period = (data.get("time_period") or "").lower().strip()
        season = (data.get("season") or "").lower().strip()
        preserve = bool(data.get("preserve_heritage"))
        simple_for_beginners = bool(data.get("simple_for_beginners"))

        # Require at least one signal
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
            score = 0.05  # base
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
                "reason": "; ".join(reason_parts) or "General match",
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

    @app.route("/")
    def home():
        return send_from_directory("static", "index.html")

    import logging
    from logging.handlers import RotatingFileHandler
    import os

    if not os.path.exists("logs"):
        os.makedirs("logs")

    handler = RotatingFileHandler("logs/app.log", maxBytes=1_000_000, backupCount=3)
    handler.setLevel(logging.INFO)
    handler.setFormatter(logging.Formatter("[%(asctime)s] %(levelname)s %(message)s"))

    app.logger.addHandler(handler)
    app.logger.setLevel(logging.INFO)

    # test line so you SEE something
    app.logger.info("TuniMaqam app started")
    # ---------- END LOGGING SETUP ----------

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)