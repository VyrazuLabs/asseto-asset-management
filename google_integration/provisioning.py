import base64
import logging
import secrets
import string
import time

from google.auth.transport.requests import AuthorizedSession
from google.oauth2.credentials import Credentials

from .oauth import SCOPES

logger = logging.getLogger(__name__)

CLOUD_RESOURCE_MANAGER_BASE = "https://cloudresourcemanager.googleapis.com/v3"
SERVICE_USAGE_BASE = "https://serviceusage.googleapis.com/v1"
FIREBASE_BASE = "https://firebase.googleapis.com/v1beta1"
IAM_BASE = "https://iam.googleapis.com/v1"

FIREBASE_ADMIN_ROLE = "roles/firebase.sdkAdminServiceAgent"
SERVICE_ACCOUNT_ID = "firebase-adminsdk"

OPERATION_POLL_INTERVAL_SECONDS = 2
OPERATION_POLL_TIMEOUT_SECONDS = 120


class ProvisioningError(Exception):
    """Raised when any step of GCP/Firebase auto-provisioning fails."""


def _authed_session(token_response: dict) -> AuthorizedSession:
    """Build a Google API session from an OAuth token-exchange response."""
    credentials = Credentials(token=token_response["access_token"], scopes=SCOPES)
    return AuthorizedSession(credentials)


def _generate_project_id() -> str:
    """Generate a globally-unique-enough GCP project ID (6-30 chars, lowercase)."""
    suffix = "".join(secrets.choice(string.digits + "abcdefghijklmnopqrstuvwxyz") for _ in range(8))
    return f"asseto-{suffix}"


def _poll_operation(session: AuthorizedSession, operation_name: str) -> dict:
    """Poll a Google API long-running Operation until it reports `done`.

    Args:
        session: authorized session to use for the poll requests.
        operation_name: the `name` field of the Operation resource
            (e.g. "operations/abc123" or "projects/.../operations/abc123").

    Returns:
        The final Operation resource body.

    Raises:
        ProvisioningError: If the operation fails or doesn't complete within
            `OPERATION_POLL_TIMEOUT_SECONDS`.
    """
    deadline = time.monotonic() + OPERATION_POLL_TIMEOUT_SECONDS
    url = f"{CLOUD_RESOURCE_MANAGER_BASE}/{operation_name}"
    while time.monotonic() < deadline:
        resp = session.get(url, timeout=30)
        resp.raise_for_status()
        body = resp.json()
        if body.get("done"):
            if "error" in body:
                raise ProvisioningError(f"Operation {operation_name} failed: {body['error']}")
            return body
        time.sleep(OPERATION_POLL_INTERVAL_SECONDS)
    raise ProvisioningError(f"Operation {operation_name} did not complete in time")


def create_gcp_project(session: AuthorizedSession, display_name: str) -> str:
    """Create a new GCP project via Cloud Resource Manager v3.

    Args:
        session: authorized Google API session.
        display_name: human-readable project name shown in GCP console.

    Returns:
        The created project's `projectId`.
    """
    project_id = _generate_project_id()
    resp = session.post(
        f"{CLOUD_RESOURCE_MANAGER_BASE}/projects",
        json={"projectId": project_id, "displayName": display_name},
        timeout=30,
    )
    resp.raise_for_status()
    _poll_operation(session, resp.json()["name"])
    return project_id


def enable_firebase_api(session: AuthorizedSession, project_id: str) -> None:
    """Enable the Firebase Management API on the project (required before addFirebase)."""
    resp = session.post(
        f"{SERVICE_USAGE_BASE}/projects/{project_id}/services/firebase.googleapis.com:enable",
        timeout=30,
    )
    resp.raise_for_status()


def add_firebase_to_project(session: AuthorizedSession, project_id: str) -> None:
    """Add Firebase to the newly-created GCP project."""
    resp = session.post(
        f"{FIREBASE_BASE}/projects/{project_id}:addFirebase",
        timeout=30,
    )
    resp.raise_for_status()
    _poll_operation(session, resp.json()["name"])


def create_firebase_web_app(session: AuthorizedSession, project_id: str, display_name: str) -> str:
    """Create a Firebase Web App under the project.

    Returns:
        The created web app's `appId`.
    """
    resp = session.post(
        f"{FIREBASE_BASE}/projects/{project_id}/webApps",
        json={"displayName": display_name},
        timeout=30,
    )
    resp.raise_for_status()
    operation = _poll_operation(session, resp.json()["name"])
    return operation["response"]["appId"]


def get_web_app_config(session: AuthorizedSession, project_id: str, app_id: str) -> dict:
    """Fetch the Firebase web app's client config (apiKey, authDomain, etc.)."""
    resp = session.get(
        f"{FIREBASE_BASE}/projects/{project_id}/webApps/{app_id}/config",
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


def create_service_account(session: AuthorizedSession, project_id: str) -> str:
    """Create the IAM service account used for server-side Firebase Admin SDK access.

    Returns:
        The created service account's email address.
    """
    resp = session.post(
        f"{IAM_BASE}/projects/{project_id}/serviceAccounts",
        json={
            "accountId": SERVICE_ACCOUNT_ID,
            "serviceAccount": {"displayName": "Firebase Admin SDK (Asseto)"},
        },
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["email"]


def grant_firebase_admin_role(session: AuthorizedSession, project_id: str, service_account_email: str) -> None:
    """Grant the service account the Firebase Admin SDK role on the project."""
    member = f"serviceAccount:{service_account_email}"
    policy_url = f"{CLOUD_RESOURCE_MANAGER_BASE}/projects/{project_id}:getIamPolicy"
    resp = session.post(policy_url, timeout=30)
    resp.raise_for_status()
    policy = resp.json()
    policy.setdefault("bindings", []).append({"role": FIREBASE_ADMIN_ROLE, "members": [member]})
    set_resp = session.post(
        f"{CLOUD_RESOURCE_MANAGER_BASE}/projects/{project_id}:setIamPolicy",
        json={"policy": policy},
        timeout=30,
    )
    set_resp.raise_for_status()


def create_service_account_key(session: AuthorizedSession, project_id: str, service_account_email: str) -> str:
    """Generate a service account key (JSON) for the Firebase Admin service account.

    Returns:
        Decoded JSON key file content (a JSON string), suitable for Fernet
        encryption before storage.
    """
    resp = session.post(
        f"{IAM_BASE}/projects/{project_id}/serviceAccounts/{service_account_email}/keys",
        timeout=30,
    )
    resp.raise_for_status()
    private_key_data = resp.json()["privateKeyData"]
    return base64.b64decode(private_key_data).decode()


def provision_firebase_project(token_response: dict, display_name: str) -> dict:
    """Run the full create-project -> add-Firebase -> web-app -> service-account flow.

    Args:
        token_response: the dict returned by `oauth.exchange_code_for_tokens`.
        display_name: human-readable name for the new GCP project/web app.

    Returns:
        dict with all fields needed to populate `GoogleCloudFirebaseConfig`.

    Raises:
        ProvisioningError: If any step fails. The caller is responsible for
            recording `last_error` and NOT marking the config as connected —
            a partially-created GCP project is a known, out-of-scope-to-fix
            limitation (the admin must clean it up manually in GCP console).
    """
    session = _authed_session(token_response)

    try:
        project_id = create_gcp_project(session, display_name)
        enable_firebase_api(session, project_id)
        add_firebase_to_project(session, project_id)
        app_id = create_firebase_web_app(session, project_id, display_name)
        web_config = get_web_app_config(session, project_id, app_id)
        service_account_email = create_service_account(session, project_id)
        grant_firebase_admin_role(session, project_id, service_account_email)
        service_account_json = create_service_account_key(session, project_id, service_account_email)
    except Exception as exc:  # noqa: BLE001 - any API-call failure must surface as ProvisioningError
        logger.error("Firebase provisioning failed: %s", exc, exc_info=True)
        raise ProvisioningError(str(exc)) from exc

    return {
        "gcp_project_id": project_id,
        "firebase_web_app_id": app_id,
        "web_api_key": web_config.get("apiKey"),
        "web_auth_domain": web_config.get("authDomain"),
        "web_project_id": web_config.get("projectId"),
        "web_storage_bucket": web_config.get("storageBucket"),
        "web_messaging_sender_id": web_config.get("messagingSenderId"),
        "web_app_id": web_config.get("appId"),
        "encrypted_service_account_json": service_account_json,
        "encrypted_oauth_refresh_token": token_response.get("refresh_token"),
        "oauth_token_scopes": token_response.get("scope"),
    }
