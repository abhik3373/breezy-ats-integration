"""
handler.py
──────────
AWS Lambda handler functions for the Breezy HR ATS Integration.

Three endpoints:
  GET  /jobs                  → get_jobs()
  POST /candidates            → create_candidate()
  GET  /applications?job_id=  → get_applications()
"""

import json
import logging
from breezy_client import BreezyClient

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


# ──────────────────────────────────────────────
# SHARED HELPER: Standard HTTP Response Builder
# ──────────────────────────────────────────────
def _response(data, status_code=200):
    """
    Build a standard Lambda HTTP response.
    Always includes CORS headers and JSON content type.
    """
    return {
        "statusCode": status_code,
        "headers": {
            "Access-Control-Allow-Origin":  "*",
            "Access-Control-Allow-Headers": "Content-Type,Authorization",
            "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
            "Content-Type":                 "application/json",
        },
        "body": json.dumps(data),
    }


# ──────────────────────────────────────────────
# HANDLER 1: GET /jobs
# ──────────────────────────────────────────────
def get_jobs(event, context):
    """
    Fetch a list of open job positions from Breezy HR.

    Query parameters:
      page (optional, default=1) — for pagination

    Response: List of job objects
    [
      {
        "id": "string",
        "title": "string",
        "location": "string",
        "status": "OPEN|CLOSED|DRAFT",
        "external_url": "string"
      }
    ]
    """
    logger.info("Handler: GET /jobs")

    query_params = event.get("queryStringParameters") or {}
    page = int(query_params.get("page", 1))

    client = BreezyClient()
    data, status = client.get_jobs(page=page)

    return _response(data, status)


# ──────────────────────────────────────────────
# HANDLER 2: POST /candidates
# ──────────────────────────────────────────────
def create_candidate(event, context):
    """
    Accept a candidate application and submit it to Breezy HR.

    Request body (JSON):
    {
      "name": "string",
      "email": "string",
      "phone": "string",
      "resume_url": "string",
      "job_id": "string"
    }

    Response: Created candidate summary
    """
    logger.info("Handler: POST /candidates")

    # Parse the request body
    try:
        body = json.loads(event.get("body") or "{}")
    except json.JSONDecodeError:
        return _response({"error": "Invalid JSON in request body"}, 400)

    # Validate required fields early
    required_fields = ["name", "email", "job_id"]
    missing = [f for f in required_fields if not body.get(f)]
    if missing:
        return _response(
            {"error": f"Missing required fields: {', '.join(missing)}"},
            400
        )

    client = BreezyClient()
    data, status = client.create_candidate(body)

    return _response(data, status)


# ──────────────────────────────────────────────
# HANDLER 3: GET /applications
# ──────────────────────────────────────────────
def get_applications(event, context):
    """
    List all candidates who applied to a specific job.

    Query parameters:
      job_id (required) — the position ID to look up
      page   (optional, default=1) — for pagination

    Response: List of application objects
    [
      {
        "id": "string",
        "candidate_name": "string",
        "email": "string",
        "status": "APPLIED|SCREENING|REJECTED|HIRED"
      }
    ]
    """
    logger.info("Handler: GET /applications")

    query_params = event.get("queryStringParameters") or {}
    job_id = query_params.get("job_id")
    page   = int(query_params.get("page", 1))

    if not job_id:
        return _response(
            {"error": "job_id is required as a query parameter (e.g. ?job_id=abc123)"},
            400
        )

    client = BreezyClient()
    data, status = client.get_applications(job_id=job_id, page=page)

    return _response(data, status)
