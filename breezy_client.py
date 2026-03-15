"""
breezy_client.py
────────────────
Core Breezy HR API Client.
Handles all communication with the Breezy HR REST API (v3).

Docs: https://developer.breezy.hr/
"""

import os
import logging
import requests
from dotenv import load_dotenv

# Load .env file when running locally
load_dotenv()

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class BreezyClient:
    """
    Wrapper around the Breezy HR v3 API.
    All methods return a tuple: (data, http_status_code)
    """

    def __init__(self):
        self.api_key = os.environ.get("BREEZY_API_KEY", "")
        self.company_id = os.environ.get("BREEZY_COMPANY_ID", "")
        self.base_url = os.environ.get("BREEZY_BASE_URL", "https://api.breezy.hr/v3")

        if not self.api_key or not self.company_id:
            logger.warning("⚠️  BREEZY_API_KEY or BREEZY_COMPANY_ID is missing from environment.")

        self.headers = {
            "Authorization": self.api_key,
            "Content-Type": "application/json",
        }

    # ──────────────────────────────────────────────────────────
    # METHOD 1: GET /jobs
    # ──────────────────────────────────────────────────────────
    def get_jobs(self, page=1):
        """
        Fetch all open positions from Breezy HR.
        Supports basic pagination via the `page` parameter.

        Returns jobs in the standard format:
        {
            "id": str,
            "title": str,
            "location": str,
            "status": "OPEN" | "CLOSED" | "DRAFT",
            "external_url": str
        }
        """
        url = f"{self.base_url}/company/{self.company_id}/positions"
        params = {"page": page}

        logger.info(f"Fetching jobs — page {page}")

        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error: {e}")
            return {"error": "Could not connect to Breezy HR", "details": str(e)}, 503

        if response.status_code != 200:
            return self._handle_error(response)

        jobs_raw = response.json()

        # Map Breezy fields → our standard format
        jobs = []
        for job in jobs_raw:
            jobs.append({
                "id":           job.get("_id"),
                "title":        job.get("name"),
                "location":     self._extract_location(job),
                "status":       self._map_position_status(job.get("state")),
                "external_url": job.get("url"),
            })

        logger.info(f"Returning {len(jobs)} jobs")
        return jobs, 200

    # ──────────────────────────────────────────────────────────
    # METHOD 2: POST /candidates
    # ──────────────────────────────────────────────────────────
    def create_candidate(self, payload):
        """
        Create a new candidate in Breezy HR and attach them to a job
        in a single API call.

        Expected payload:
        {
            "name": str,
            "email": str,
            "phone": str,
            "resume_url": str,
            "job_id": str    ← which position to apply for
        }
        """
        job_id = payload.get("job_id")
        if not job_id:
            return {"error": "job_id is required in the request body"}, 400

        name = payload.get("name")
        email = payload.get("email")

        if not name or not email:
            return {"error": "name and email are required fields"}, 400

        url = f"{self.base_url}/company/{self.company_id}/position/{job_id}/candidates"

        # Map our payload → Breezy's expected format
        breezy_payload = {
            "name":          name,
            "email_address": email,
            "phone_number":  payload.get("phone", ""),
            "origin":        "applied",         # Marks them as an applicant
            "source":        "API Integration", # Visible in Breezy dashboard
        }

        # If a resume URL is provided, add it as a summary note
        resume_url = payload.get("resume_url")
        if resume_url:
            breezy_payload["summary"] = f"Resume: {resume_url}"

        logger.info(f"Creating candidate '{name}' for job '{job_id}'")

        try:
            response = requests.post(url, headers=self.headers, json=breezy_payload, timeout=10)
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error: {e}")
            return {"error": "Could not connect to Breezy HR", "details": str(e)}, 503

        if response.status_code not in [200, 201]:
            return self._handle_error(response)

        created = response.json()
        logger.info(f"Candidate created with ID: {created.get('_id')}")

        return {
            "message":      "Candidate created and application submitted successfully",
            "candidate_id": created.get("_id"),
            "name":         created.get("name"),
            "email":        created.get("email_address"),
            "job_id":       job_id,
        }, 201

    # ──────────────────────────────────────────────────────────
    # METHOD 3: GET /applications
    # ──────────────────────────────────────────────────────────
    def get_applications(self, job_id, page=1):
        """
        List all candidates (applications) for a specific job.
        Supports pagination via the `page` parameter.

        Returns applications in the standard format:
        {
            "id": str,
            "candidate_name": str,
            "email": str,
            "status": "APPLIED" | "SCREENING" | "REJECTED" | "HIRED"
        }
        """
        if not job_id:
            return {"error": "job_id is required"}, 400

        url = f"{self.base_url}/company/{self.company_id}/position/{job_id}/candidates"
        params = {"page": page}

        logger.info(f"Fetching applications for job '{job_id}' — page {page}")

        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error: {e}")
            return {"error": "Could not connect to Breezy HR", "details": str(e)}, 503

        if response.status_code != 200:
            return self._handle_error(response)

        candidates_raw = response.json()

        # Map Breezy fields → our standard format
        applications = []
        for c in candidates_raw:
            applications.append({
                "id":             c.get("_id"),
                "candidate_name": c.get("name"),
                "email":          c.get("email_address"),
                "status":         self._map_application_status(c.get("stage", {}).get("name")),
            })

        logger.info(f"Returning {len(applications)} applications")
        return applications, 200

    # ──────────────────────────────────────────────────────────
    # PRIVATE HELPERS
    # ──────────────────────────────────────────────────────────
    def _extract_location(self, job):
        """Extract a readable location string from a Breezy job object."""
        location = job.get("location")
        if not location:
            return "Remote / Not Specified"
        if isinstance(location, dict):
            return location.get("name", "Remote / Not Specified")
        return str(location)

    def _map_position_status(self, state):
        """Map Breezy position states to our standard OPEN/CLOSED/DRAFT."""
        mapping = {
            "published": "OPEN",
            "draft":     "DRAFT",
            "closed":    "CLOSED",
            "archived":  "CLOSED",
            "pending":   "DRAFT",
        }
        return mapping.get(state, "OPEN")

    def _map_application_status(self, stage_name):
        """Map Breezy pipeline stage names to our standard statuses."""
        if not stage_name:
            return "APPLIED"
        s = stage_name.upper()
        if "HIRED" in s or "OFFER" in s:
            return "HIRED"
        if "REJECT" in s or "DECLINED" in s or "WITHDRAWN" in s:
            return "REJECTED"
        if "SCREEN" in s or "REVIEW" in s or "INTERVIEW" in s or "ASSESSMENT" in s:
            return "SCREENING"
        return "APPLIED"

    def _handle_error(self, response):
        """Convert a non-2xx Breezy response to a clean JSON error."""
        try:
            error_body = response.json()
        except Exception:
            error_body = {"raw_response": response.text}

        logger.error(f"Breezy HR API error {response.status_code}: {error_body}")
        return {
            "error":       "Breezy HR API Error",
            "status_code": response.status_code,
            "details":     error_body,
        }, response.status_code
