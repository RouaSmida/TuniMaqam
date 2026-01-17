# TuniMaqam API - Error Catalog

This document provides a comprehensive catalog of all error responses returned by the TuniMaqam API.

## Table of Contents

- [HTTP Status Codes Overview](#http-status-codes-overview)
- [Authentication Errors (401, 403)](#authentication-errors)
- [Validation Errors (400)](#validation-errors)
- [Resource Errors (404)](#resource-errors)
- [Rate Limiting Errors (429)](#rate-limiting-errors)
- [Server Errors (500, 502, 504)](#server-errors)
- [Error Response Format](#error-response-format)

---

## HTTP Status Codes Overview

| Code | Status | Description |
|------|--------|-------------|
| 200 | OK | Request successful |
| 201 | Created | Resource created successfully |
| 400 | Bad Request | Invalid request parameters or body |
| 401 | Unauthorized | Missing or invalid authentication token |
| 403 | Forbidden | Valid token but insufficient permissions |
| 404 | Not Found | Requested resource does not exist |
| 409 | Conflict | Resource already exists or state conflict |
| 422 | Unprocessable Entity | Request understood but cannot be processed |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Unexpected server error |
| 502 | Bad Gateway | External service (AssemblyAI) error |
| 504 | Gateway Timeout | External service timeout |

---

## Error Response Format

All error responses follow a consistent JSON structure:

```json
{
  "error": "Human-readable error message",
  "code": "ERROR_CODE",
  "details": {}  // Optional: additional context
}
```

---

## Authentication Errors

### AUTH_001: Missing Authorization Header

**Status:** 401 Unauthorized

**Cause:** Request to protected endpoint without Authorization header.

```json
{
  "error": "Missing Authorization header",
  "code": "AUTH_001"
}
```

**Solution:** Include `Authorization: Bearer <token>` header in request.

---

### AUTH_002: Invalid Token Format

**Status:** 401 Unauthorized

**Cause:** Authorization header does not follow "Bearer <token>" format.

```json
{
  "error": "Invalid token format. Expected: Bearer <token>",
  "code": "AUTH_002"
}
```

**Solution:** Ensure header format is exactly `Authorization: Bearer eyJ...`

---

### AUTH_003: Token Expired

**Status:** 401 Unauthorized

**Cause:** JWT token has exceeded its expiration time.

```json
{
  "error": "Token has expired",
  "code": "AUTH_003",
  "details": {
    "expired_at": "2026-01-10T12:00:00Z"
  }
}
```

**Solution:** Obtain a new token via `/auth/google/login` or `/auth/demo-token`.

---

### AUTH_004: Invalid Token Signature

**Status:** 401 Unauthorized

**Cause:** Token signature verification failed (tampered or wrong secret).

```json
{
  "error": "Invalid token signature",
  "code": "AUTH_004"
}
```

**Solution:** Obtain a fresh token from the authentication endpoint.

---

### AUTH_005: Insufficient Permissions

**Status:** 403 Forbidden

**Cause:** User role does not have permission for this endpoint.

```json
{
  "error": "Insufficient permissions. Required role: admin",
  "code": "AUTH_005",
  "details": {
    "user_role": "learner",
    "required_roles": ["admin", "expert"]
  }
}
```

**Solution:** Request access from an administrator or use an account with appropriate role.

---

## Validation Errors

### VAL_001: Missing Required Field

**Status:** 400 Bad Request

**Cause:** Required field missing from request body.

```json
{
  "error": "Missing required field: notes",
  "code": "VAL_001",
  "details": {
    "field": "notes",
    "location": "body"
  }
}
```

---

### VAL_002: Invalid Field Type

**Status:** 400 Bad Request

**Cause:** Field value is of incorrect type.

```json
{
  "error": "Invalid type for field 'notes': expected array, got string",
  "code": "VAL_002",
  "details": {
    "field": "notes",
    "expected_type": "array",
    "received_type": "string"
  }
}
```

---

### VAL_003: Invalid Note Format

**Status:** 400 Bad Request

**Cause:** Note in array is not a valid musical note.

```json
{
  "error": "Invalid note format: 'X' is not a valid musical note",
  "code": "VAL_003",
  "details": {
    "invalid_note": "X",
    "valid_notes": ["C", "D", "E", "F", "G", "A", "B", "C#", "Db", "..."]
  }
}
```

---

### VAL_004: Empty Notes Array

**Status:** 400 Bad Request

**Cause:** Notes array is empty.

```json
{
  "error": "notes list is required",
  "code": "VAL_004"
}
```

---

### VAL_005: Invalid Quiz ID

**Status:** 400 Bad Request

**Cause:** Quiz session ID does not exist or has expired.

```json
{
  "error": "Invalid or expired quiz session",
  "code": "VAL_005",
  "details": {
    "quiz_id": "abc123"
  }
}
```

---

### VAL_006: Invalid Audio Format

**Status:** 400 Bad Request

**Cause:** Uploaded audio file is not in a supported format.

```json
{
  "error": "Unsupported audio format. Supported: MP3, WAV, OGG",
  "code": "VAL_006",
  "details": {
    "received_format": "video/mp4",
    "supported_formats": ["audio/mpeg", "audio/wav", "audio/ogg"]
  }
}
```

---

### VAL_007: Missing Audio File

**Status:** 400 Bad Request

**Cause:** Audio file not provided in multipart form data.

```json
{
  "error": "audio file is required (field 'audio')",
  "code": "VAL_007"
}
```

---

## Resource Errors

### RES_001: Maqam Not Found

**Status:** 404 Not Found

**Cause:** Requested maqam ID or name does not exist.

```json
{
  "error": "Maqam not found",
  "code": "RES_001",
  "details": {
    "maqam_id": 999
  }
}
```

---

### RES_002: Contribution Not Found

**Status:** 404 Not Found

**Cause:** Requested contribution ID does not exist.

```json
{
  "error": "Contribution not found",
  "code": "RES_002",
  "details": {
    "contribution_id": 123
  }
}
```

---

### RES_003: Audio Not Found

**Status:** 404 Not Found

**Cause:** Requested audio record ID does not exist.

```json
{
  "error": "Audio record not found",
  "code": "RES_003"
}
```

---

### RES_004: User Stats Not Found

**Status:** 404 Not Found

**Cause:** No statistics found for the requesting user.

```json
{
  "error": "User statistics not found",
  "code": "RES_004"
}
```

---

## Rate Limiting Errors

### RATE_001: Rate Limit Exceeded

**Status:** 429 Too Many Requests

**Cause:** Client has exceeded the allowed request rate.

```json
{
  "error": "Rate limit exceeded",
  "code": "RATE_001",
  "details": {
    "limit": "200 per hour",
    "retry_after": 3600
  }
}
```

**Headers:**
```
Retry-After: 3600
X-RateLimit-Limit: 200
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1704931200
```

**Solution:** Wait until the rate limit window resets, or contact administrator for limit increase.

---

## Server Errors

### SRV_001: Internal Server Error

**Status:** 500 Internal Server Error

**Cause:** Unexpected server-side error.

```json
{
  "error": "An unexpected error occurred",
  "code": "SRV_001"
}
```

**Action:** Check server logs at `logs/app.log` for details.

---

### SRV_002: Database Connection Error

**Status:** 500 Internal Server Error

**Cause:** Unable to connect to database.

```json
{
  "error": "Database connection failed",
  "code": "SRV_002"
}
```

---

### SRV_003: AssemblyAI Upload Failed

**Status:** 502 Bad Gateway

**Cause:** Failed to upload audio to AssemblyAI.

```json
{
  "error": "Audio upload failed",
  "code": "SRV_003",
  "details": {
    "service": "AssemblyAI",
    "upstream_status": 500
  }
}
```

---

### SRV_004: Transcription Timeout

**Status:** 504 Gateway Timeout

**Cause:** AssemblyAI transcription took too long.

```json
{
  "error": "Transcription timed out",
  "code": "SRV_004",
  "details": {
    "timeout_seconds": 60
  }
}
```

---

### SRV_005: AssemblyAI Not Configured

**Status:** 200 OK (with warning)

**Cause:** AssemblyAI API key not configured; fallback notes used.

```json
{
  "extracted_notes": ["C", "D", "E", "G"],
  "candidates": [...],
  "warning": "ASSEMBLYAI_API_KEY not configured, used fallback notes"
}
```

---

## Contribution-Specific Errors

### CONTRIB_001: Invalid Contribution Type

**Status:** 400 Bad Request

```json
{
  "error": "Invalid contribution type",
  "code": "CONTRIB_001",
  "details": {
    "received": "invalid_type",
    "valid_types": ["new_maqam", "correction", "addition", "audio"]
  }
}
```

---

### CONTRIB_002: Contribution Already Reviewed

**Status:** 409 Conflict

```json
{
  "error": "Contribution has already been reviewed",
  "code": "CONTRIB_002",
  "details": {
    "status": "accepted",
    "reviewed_at": "2026-01-10T12:00:00Z"
  }
}
```

---

### CONTRIB_003: Invalid Review Decision

**Status:** 400 Bad Request

```json
{
  "error": "Invalid review decision",
  "code": "CONTRIB_003",
  "details": {
    "received": "maybe",
    "valid_decisions": ["accepted", "rejected"]
  }
}
```

---

## Quiz-Specific Errors

### QUIZ_001: Quiz Session Expired

**Status:** 400 Bad Request

```json
{
  "error": "Quiz session has expired",
  "code": "QUIZ_001",
  "details": {
    "quiz_id": 123,
    "expired_at": "2026-01-10T12:00:00Z"
  }
}
```

---

### QUIZ_002: Answers Count Mismatch

**Status:** 400 Bad Request

```json
{
  "error": "Answer count does not match question count",
  "code": "QUIZ_002",
  "details": {
    "expected": 20,
    "received": 15
  }
}
```

---

## Best Practices for Error Handling

### Client-Side Recommendations

1. **Always check HTTP status codes** before parsing response body
2. **Implement exponential backoff** for 429 and 5xx errors
3. **Cache tokens** and refresh before expiration
4. **Log error codes** for debugging and support requests
5. **Display user-friendly messages** based on error codes

### Example Error Handler (JavaScript)

```javascript
async function handleApiResponse(response) {
  if (!response.ok) {
    const error = await response.json();
    
    switch (response.status) {
      case 401:
        // Redirect to login
        window.location.href = '/auth/google/login';
        break;
      case 403:
        alert('You do not have permission for this action');
        break;
      case 429:
        const retryAfter = response.headers.get('Retry-After');
        alert(`Rate limited. Please wait ${retryAfter} seconds.`);
        break;
      default:
        console.error(`API Error [${error.code}]: ${error.error}`);
    }
    
    throw new Error(error.error);
  }
  
  return response.json();
}
```

---

## Contact & Support

For unresolved errors or questions, contact the TuniMaqam team with:
- Error code (e.g., `AUTH_003`)
- Request endpoint and method
- Timestamp of the error
- Any relevant request/response data (excluding sensitive information)
