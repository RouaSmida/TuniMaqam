from flask import Blueprint, jsonify, request, current_app
from authlib.integrations.flask_client import OAuth
from services.auth_service import issue_token, require_jwt
from services.user_service import get_or_create_user_stat

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

# OAuth will be initialized in create_app and attached to the blueprint
oauth = None


def init_oauth(app):
    """Initialize OAuth with the Flask app."""
    global oauth
    oauth = OAuth(app)
    oauth.register(
        name="google",
        client_id=app.config["GOOGLE_CLIENT_ID"],
        client_secret=app.config["GOOGLE_CLIENT_SECRET"],
        server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
        client_kwargs={"scope": "openid email profile"},
    )


@auth_bp.route("/google/login")
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
    redirect_uri = current_app.config["OAUTH_REDIRECT_URI"]
    return oauth.google.authorize_redirect(redirect_uri)


@auth_bp.route("/google/callback")
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
    if email in current_app.config["AUTH_ADMIN_EMAILS"]:
        role = "admin"
    elif email in current_app.config["AUTH_EXPERT_EMAILS"]:
        role = "expert"
    elif not current_app.config["AUTH_ALLOWED_EMAILS"] or email in current_app.config["AUTH_ALLOWED_EMAILS"]:
        role = current_app.config["AUTH_DEFAULT_ROLE"]
    else:
        return jsonify({"error": "Email not allowed"}), 403

    jwt_token = issue_token(sub=email, role=role, email=email)
    jwt_exp = current_app.config['JWT_EXP_SECONDS']

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
          <link rel="preconnect" href="https://fonts.googleapis.com">
          <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
          <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Outfit:wght@300;500;700;800&family=Reem+Kufi+Fun:wght@400..700&display=swap" rel="stylesheet">
          <style>
            :root {{
              --bg-base: #f8fafc; --glass-surface: rgba(255, 255, 255, 0.75);
              --glass-border: rgba(14, 165, 233, 0.2); --glass-hover: rgba(255, 255, 255, 0.95);
              --sidi-blue: #0ea5e9; --sidi-dark-blue: #0369a1;
              --text-main: #0f172a; --text-muted: #475569;
              --font-display: 'Reem Kufi Fun', sans-serif; --font-tech: 'Inter', sans-serif;
              --shadow-card: 0 10px 30px -10px rgba(14, 165, 233, 0.15);
            }}
            * {{ box-sizing: border-box; }}
            body {{
              margin: 0; min-height: 100vh; font-family: var(--font-tech);
              background: linear-gradient(to bottom, #f0f9ff, #f8fafc);
              color: var(--text-main); display: flex; align-items: center;
              justify-content: center; padding: 24px;
            }}
            .card {{
              width: min(600px, 94vw); background: var(--glass-surface);
              border: 1px solid var(--glass-border); border-radius: 20px;
              padding: 32px; box-shadow: var(--shadow-card); text-align: center;
            }}
            h1 {{ margin: 0 0 8px; font-family: var(--font-display); font-weight: 700;
              font-size: 2rem; color: var(--sidi-dark-blue); }}
            .sub {{ margin: 0 0 24px; color: var(--text-muted); }}
            .pills {{ display: flex; gap: 10px; justify-content: center; margin-bottom: 24px; }}
            .pill {{ padding: 8px 16px; border-radius: 99px; font-weight: 600;
              background: #fff; border: 1px solid var(--glass-border); }}
            .pill span {{ font-weight: 400; color: var(--text-muted); }}
            .label {{ font-size: 0.85rem; font-weight: 700; color: var(--sidi-blue);
              text-transform: uppercase; margin: 0 0 8px; text-align: left; }}
            textarea {{
              width: 100%; min-height: 100px; background: #fff; border: 1px solid #cbd5e1;
              border-radius: 12px; padding: 14px; font-family: monospace; font-size: 0.85rem;
              resize: vertical; margin-bottom: 24px;
            }}
            .row {{ display: flex; gap: 12px; }}
            .btn {{
              cursor: pointer; border-radius: 10px; padding: 12px 24px;
              font-weight: 700; font-size: 1rem; width: 100%;
            }}
            .btn.primary {{
              background: linear-gradient(135deg, var(--sidi-blue), var(--sidi-dark-blue));
              color: #fff; border: none;
            }}
            .btn.secondary {{ background: transparent; border: 1px solid #cbd5e1; color: var(--text-muted); }}
          </style>
        </head>
        <body>
          <div class="card">
            <h1>Access Granted</h1>
            <p class="sub">Welcome to TuniMaqam. Use this token to authenticate your session.</p>
            <div class="pills">
              <div class="pill"><span>Role:</span> {role_lower}</div>
              <div class="pill"><span>Email:</span> {email_lower}</div>
            </div>
            <div class="label">Your JWT Token</div>
            <textarea id="tok" readonly>{jwt_token}</textarea>
            <div class="row">
              <button class="btn primary" onclick="navigator.clipboard.writeText(document.getElementById('tok').value);this.innerText='Copied!';setTimeout(()=>this.innerText='Copy Token',2000)">Copy Token</button>
              <button class="btn secondary" onclick="window.location.href='/'">Enter App</button>
            </div>
          </div>
        </body>
        </html>
        """
    return jsonify({
        "access_token": jwt_token,
        "token_type": "Bearer",
        "expires_in": jwt_exp,
        "role": role,
        "email": email
    }), 200


@auth_bp.route("/demo-token", methods=["GET"])
def auth_demo_token():
    """
    Issue a short-lived demo token for local testing (no OAuth)
    ---
    tags:
      - Auth
    responses:
      200:
        description: Demo bearer token
      403:
        description: Disabled
    """
    if not current_app.config.get("ENABLE_DEMO_TOKEN", True):
        return jsonify({"error": "demo token disabled"}), 403

    email = current_app.config.get("DEMO_TOKEN_EMAIL", "demo@local")
    role = current_app.config.get("DEMO_TOKEN_ROLE", "learner")
    jwt_exp = current_app.config['JWT_EXP_SECONDS']
    token = issue_token(sub=email, role=role, email=email)
    return jsonify({
        "access_token": token,
        "token_type": "Bearer",
        "expires_in": jwt_exp,
        "role": role,
        "email": email
    }), 200


@auth_bp.route("/whoami", methods=["GET"])
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
        "level": get_or_create_user_stat(p.get("email", "anonymous")).level,
    }), 200
