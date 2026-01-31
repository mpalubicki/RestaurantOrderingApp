import os
from google.cloud import secretmanager

def get_secret(secret_id: str, version_id: str = "latest") -> str:
    project_id = os.environ.get("GOOGLE_CLOUD_PROJECT") or os.environ.get("GCP_PROJECT")
    if not project_id:
        raise RuntimeError("GOOGLE_CLOUD_PROJECT is not set")

    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{project_id}/secrets/{secret_id}/versions/{version_id}"
    return client.access_secret_version(request={"name": name}).payload.data.decode("utf-8")
