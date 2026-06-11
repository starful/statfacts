"""
Resolve GEMINI_API_KEY — same order as other OK Series sites:
  1. Environment variable
  2. Local .env (python-dotenv)
  3. gcloud Secret Manager CLI
  4. google-cloud-secret-manager (Application Default Credentials)
"""
from __future__ import annotations

import os
import subprocess

from dotenv import load_dotenv

DEFAULT_GCP_PROJECT = "starful-258005"
DEFAULT_GEMINI_SECRET_ID = "GEMINI_API_KEY"


def _gcp_project_id() -> str:
    pid = (
        os.environ.get("GCP_PROJECT_ID", "").strip()
        or os.environ.get("GOOGLE_CLOUD_PROJECT", "").strip()
        or DEFAULT_GCP_PROJECT
    )
    if pid:
        return pid
    try:
        import google.auth

        _, project = google.auth.default()
        return (project or "").strip()
    except Exception:
        return DEFAULT_GCP_PROJECT


def _secret_id() -> str:
    return os.environ.get("GEMINI_API_KEY_SECRET_ID", "").strip() or DEFAULT_GEMINI_SECRET_ID


def _from_gcloud(project_id: str, secret_id: str) -> str:
    try:
        result = subprocess.run(
            [
                "gcloud",
                "secrets",
                "versions",
                "access",
                "latest",
                "--secret",
                secret_id,
                "--project",
                project_id,
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        key = (result.stdout or "").strip()
        if result.returncode == 0 and key:
            return key
    except Exception:
        pass
    return ""


def _from_secret_manager_client(project_id: str, secret_id: str) -> str:
    try:
        from google.cloud import secretmanager

        client = secretmanager.SecretManagerServiceClient()
        name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
        response = client.access_secret_version(request={"name": name})
        return response.payload.data.decode("UTF-8").strip()
    except Exception:
        return ""


def resolve_gemini_api_key(*, quiet: bool = False) -> str:
    """Return GEMINI_API_KEY without mutating os.environ."""
    key = os.environ.get("GEMINI_API_KEY", "").strip()
    if key:
        return key

    load_dotenv()
    key = os.environ.get("GEMINI_API_KEY", "").strip()
    if key:
        return key

    project_id = _gcp_project_id()
    secret_id = _secret_id()

    key = _from_gcloud(project_id, secret_id)
    if key:
        if not quiet:
            print(f"🔐 GEMINI_API_KEY loaded from Secret Manager ({secret_id}) via gcloud")
        return key

    key = _from_secret_manager_client(project_id, secret_id)
    if key:
        if not quiet:
            print(f"🔐 GEMINI_API_KEY loaded from Secret Manager ({secret_id}) via ADC")
        return key

    return ""


def ensure_gemini_api_key(*, quiet: bool = False) -> bool:
    """Load GEMINI_API_KEY into os.environ if missing. Returns True when set."""
    key = resolve_gemini_api_key(quiet=quiet)
    if key:
        os.environ["GEMINI_API_KEY"] = key
        return True
    return False
