import time
import jwt
from functools import wraps
from flask import request, jsonify, current_app


def issue_token(sub, role="learner", email=None):
    """Issue a JWT token with the given subject, role, and email."""
    jwt_secret = current_app.config['JWT_SECRET']
    jwt_alg = current_app.config['JWT_ALG']
    jwt_exp = current_app.config['JWT_EXP_SECONDS']
    
    now = int(time.time())
    payload = {
        "sub": sub,
        "role": role,
        "email": email,
        "iat": now,
        "exp": now + jwt_exp,
    }
    return jwt.encode(payload, jwt_secret, algorithm=jwt_alg)


def require_jwt(roles=None):
    """
    Decorator to require a valid JWT token.
    If roles is provided, the token's role must be in that list.
    """
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            jwt_secret = current_app.config['JWT_SECRET']
            jwt_alg = current_app.config['JWT_ALG']
            
            auth = request.headers.get("Authorization", "")
            if not auth.startswith("Bearer "):
                return jsonify({"error": "Unauthorized - No token provided"}), 401

            token = auth.replace("Bearer ", "", 1).strip()
            try:
                payload = jwt.decode(token, jwt_secret, algorithms=[jwt_alg])
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
