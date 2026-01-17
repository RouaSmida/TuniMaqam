# TuniMaqam API - Authentication Guide

This guide explains how to authenticate with the TuniMaqam API using JWT tokens and Google OAuth 2.0.

## Table of Contents

- [Overview](#overview)
- [Authentication Methods](#authentication-methods)
- [Quick Start](#quick-start)
- [Google OAuth 2.0 Flow](#google-oauth-20-flow)
- [Demo Token (Development)](#demo-token-development)
- [Using JWT Tokens](#using-jwt-tokens)
- [Role-Based Access Control](#role-based-access-control)
- [Token Lifecycle](#token-lifecycle)
- [Security Best Practices](#security-best-practices)
- [Troubleshooting](#troubleshooting)

---

## Overview

TuniMaqam uses **JSON Web Tokens (JWT)** for API authentication. Tokens are obtained through:

1. **Google OAuth 2.0** - Production authentication via Google accounts
2. **Demo Token** - Development/testing authentication (when enabled)

All protected endpoints require a valid JWT in the `Authorization` header.

---

## Authentication Methods

| Method | Use Case | Token Lifetime |
|--------|----------|----------------|
| Google OAuth | Production | Configurable (default: 24 hours) |
| Demo Token | Development/Testing | 1 hour |

---

## Quick Start

### Step 1: Obtain a Token

**For Development:**
```bash
curl http://localhost:8000/auth/demo-token
```

Response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "Bearer",
  "expires_in": 3600
}
```

**For Production:**
Navigate to `http://your-domain.com/auth/google/login` in a browser.

### Step 2: Use the Token

Include the token in the `Authorization` header:

```bash
curl -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..." \
     http://localhost:8000/knowledge/maqam
```

---

## Google OAuth 2.0 Flow

### Prerequisites

1. Create a project in [Google Cloud Console](https://console.cloud.google.com/)
2. Enable the "Google+ API" or "Google Identity" API
3. Create OAuth 2.0 credentials (Web application)
4. Add authorized redirect URIs:
   - Development: `http://localhost:8000/auth/google/callback`
   - Production: `https://your-domain.com/auth/google/callback`

### Environment Variables

```bash
# Required for Google OAuth
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret
OAUTH_REDIRECT_URI=http://localhost:8000/auth/google/callback

# JWT Configuration
JWT_SECRET=your-secure-random-secret-min-32-chars
JWT_EXP_SECONDS=86400  # 24 hours
```

### OAuth Flow Diagram

```
┌─────────┐      ┌─────────────┐      ┌────────────┐
│  User   │      │  TuniMaqam  │      │   Google   │
└────┬────┘      └──────┬──────┘      └─────┬──────┘
     │                  │                   │
     │ 1. Visit /auth/google/login          │
     │─────────────────>│                   │
     │                  │                   │
     │ 2. Redirect to Google OAuth          │
     │<─────────────────│                   │
     │                  │                   │
     │ 3. Authenticate with Google          │
     │─────────────────────────────────────>│
     │                  │                   │
     │ 4. Redirect with auth code           │
     │<─────────────────────────────────────│
     │                  │                   │
     │ 5. /auth/google/callback?code=...    │
     │─────────────────>│                   │
     │                  │                   │
     │                  │ 6. Exchange code  │
     │                  │──────────────────>│
     │                  │                   │
     │                  │ 7. User info      │
     │                  │<──────────────────│
     │                  │                   │
     │ 8. JWT Token     │                   │
     │<─────────────────│                   │
     │                  │                   │
```

### API Endpoints

#### GET /auth/google/login

Initiates Google OAuth flow. Redirects user to Google's consent screen.

**Response:** 302 Redirect to Google OAuth

---

#### GET /auth/google/callback

Handles OAuth callback. Exchanges authorization code for user info and issues JWT.

**Query Parameters:**
- `code` - Authorization code from Google
- `state` - CSRF protection token (optional)

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "Bearer",
  "expires_in": 86400,
  "user": {
    "email": "user@example.com",
    "name": "User Name",
    "role": "learner"
  }
}
```

---

## Demo Token (Development)

For local development and testing, a demo token endpoint is available.

#### GET /auth/demo-token

**Prerequisites:** Set `ENABLE_DEMO_TOKEN=1` in environment.

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "Bearer",
  "expires_in": 3600,
  "warning": "Demo token - do not use in production"
}
```

**Demo Token Payload:**
```json
{
  "sub": "demo-user",
  "email": "demo@tunimaqam.local",
  "role": "learner",
  "iat": 1704931200,
  "exp": 1704934800
}
```

---

## Using JWT Tokens

### Token Format

TuniMaqam uses HS256-signed JWTs with the following structure:

**Header:**
```json
{
  "alg": "HS256",
  "typ": "JWT"
}
```

**Payload:**
```json
{
  "sub": "user-unique-id",
  "email": "user@example.com",
  "name": "User Name",
  "role": "learner",
  "iat": 1704931200,
  "exp": 1705017600
}
```

### Including Token in Requests

**HTTP Header:**
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**cURL Example:**
```bash
TOKEN="eyJhbGciOiJIUzI1NiIs..."

# Get all maqamet
curl -H "Authorization: Bearer $TOKEN" \
     http://localhost:8000/knowledge/maqam

# Start a quiz
curl -X POST \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     http://localhost:8000/learning/quiz/start

# Analyze notes
curl -X POST \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"notes": ["C", "D", "E", "F", "G"]}' \
     http://localhost:8000/analysis/notes
```

**JavaScript Example:**
```javascript
const token = localStorage.getItem('tunimaqam_token');

const response = await fetch('/knowledge/maqam', {
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  }
});

const maqamet = await response.json();
```

**Python Example:**
```python
import requests

token = "eyJhbGciOiJIUzI1NiIs..."
headers = {"Authorization": f"Bearer {token}"}

response = requests.get(
    "http://localhost:8000/knowledge/maqam",
    headers=headers
)

maqamet = response.json()
```

---

## Role-Based Access Control

### Available Roles

| Role | Description | Permissions |
|------|-------------|-------------|
| `learner` | Default role for all users | Read maqamet, take quizzes, submit contributions |
| `expert` | Verified music experts | Learner + review contributions, upload audio |
| `admin` | System administrators | Expert + create/delete maqamet, manage users |

### Role Assignment

Roles are assigned based on email allowlists configured in environment:

```bash
# Comma-separated email addresses
ADMIN_EMAILS=admin@example.com,superuser@example.com
EXPERT_EMAILS=expert1@example.com,musicologist@example.com
```

Users not in either list default to `learner` role.

### Protected Endpoints by Role

| Endpoint | Learner | Expert | Admin |
|----------|---------|--------|-------|
| GET /knowledge/maqam | ✅ | ✅ | ✅ |
| GET /learning/* | ✅ | ✅ | ✅ |
| POST /analysis/* | ✅ | ✅ | ✅ |
| POST /recommendations/* | ✅ | ✅ | ✅ |
| POST /knowledge/maqam/{id}/contributions | ✅ | ✅ | ✅ |
| POST /knowledge/maqam/{id}/audio | ❌ | ✅ | ✅ |
| POST /knowledge/contributions/{id}/review | ❌ | ✅ | ✅ |
| POST /knowledge/maqam | ❌ | ❌ | ✅ |
| PUT /knowledge/maqam/{id} | ❌ | ❌ | ✅ |
| DELETE /knowledge/maqam/{id} | ❌ | ❌ | ✅ |

---

## Token Lifecycle

### Token Validation

On each request, the server:

1. Extracts token from `Authorization` header
2. Verifies HS256 signature against `JWT_SECRET`
3. Checks expiration time (`exp` claim)
4. Extracts user info and role from payload
5. Validates role against endpoint requirements

### Checking Current Session

#### GET /auth/whoami

Returns current user information and computed learner level.

**Request:**
```bash
curl -H "Authorization: Bearer $TOKEN" \
     http://localhost:8000/auth/whoami
```

**Response:**
```json
{
  "user": {
    "sub": "user-123",
    "email": "user@example.com",
    "name": "User Name",
    "role": "learner"
  },
  "level": "intermediate",
  "stats": {
    "best_score": 0.75,
    "total_quizzes": 12,
    "activity_count": 45
  }
}
```

### Token Expiration

When a token expires:

1. Server returns 401 Unauthorized with `AUTH_003` error code
2. Client should redirect to `/auth/google/login` for re-authentication
3. No refresh token mechanism currently implemented

---

## Security Best Practices

### For API Consumers

1. **Store tokens securely**
   - Browser: Use `httpOnly` cookies or secure localStorage
   - Mobile: Use platform keychain/keystore
   - Server: Use environment variables or secrets manager

2. **Never expose tokens in URLs**
   ```
   ❌ GET /api/data?token=eyJ...
   ✅ Authorization: Bearer eyJ...
   ```

3. **Handle token expiration gracefully**
   ```javascript
   if (response.status === 401) {
     localStorage.removeItem('token');
     window.location.href = '/auth/google/login';
   }
   ```

4. **Use HTTPS in production**
   - Tokens transmitted over HTTP can be intercepted
   - TuniMaqam enforces HTTPS in production deployments

### For Deployment

1. **Use strong secrets**
   ```bash
   # Generate secure JWT secret
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

2. **Configure CORS properly**
   ```bash
   CORS_ORIGINS=https://your-frontend.com,https://admin.your-domain.com
   ```

3. **Enable rate limiting**
   ```bash
   RATE_LIMIT_DEFAULT=200 per hour
   ```

4. **Never use demo tokens in production**
   ```bash
   ENABLE_DEMO_TOKEN=0  # or unset
   ```

---

## Troubleshooting

### Common Issues

#### "Missing Authorization header"

**Cause:** Request does not include Authorization header.

**Solution:**
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" http://...
```

#### "Token has expired"

**Cause:** JWT expiration time has passed.

**Solution:** Obtain a new token via OAuth or demo endpoint.

#### "Invalid token signature"

**Cause:** Token was signed with a different secret, or has been tampered.

**Solutions:**
- Ensure `JWT_SECRET` matches across all instances
- Obtain a fresh token
- Check for token corruption during storage/transmission

#### "Insufficient permissions"

**Cause:** User role does not match endpoint requirements.

**Solution:** Contact administrator for role upgrade, or use appropriate endpoint.

#### Google OAuth errors

| Error | Cause | Solution |
|-------|-------|----------|
| `redirect_uri_mismatch` | Callback URL not registered | Add URL in Google Cloud Console |
| `invalid_client` | Wrong client ID/secret | Verify credentials in environment |
| `access_denied` | User declined consent | User must approve access |

---

## API Reference

### Authentication Endpoints Summary

| Endpoint | Method | Auth Required | Description |
|----------|--------|---------------|-------------|
| `/auth/google/login` | GET | No | Start OAuth flow |
| `/auth/google/callback` | GET | No | OAuth callback handler |
| `/auth/demo-token` | GET | No | Get demo token (dev only) |
| `/auth/whoami` | GET | Yes | Get current user info |

---

## Contact

For authentication issues or questions, contact the TuniMaqam team with:
- Error code and message
- Request details (endpoint, headers)
- Environment (development/production)
