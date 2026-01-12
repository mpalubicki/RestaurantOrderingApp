import os
from google.cloud import secretmanager

def get_secret(secret_id: str) -> str:
    # local dev can use env vars directly
    local_val = os.environ.get(secret_id)
    if local_val:
        return local_val

    project_id = os.environ.get("GOOGLE_CLOUD_PROJECT") or os.environ.get("GCLOUD_PROJECT")
    if not project_id:
        raise RuntimeError("GOOGLE_CLOUD_PROJECT/GCLOUD_PROJECT not set")

    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
    return client.access_secret_version(request={"name": name}).payload.data.decode("utf-8")
