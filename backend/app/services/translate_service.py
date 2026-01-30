import os
from google.cloud import translate_v3 as translate


def translate_text(text: str, target_language: str, source_language: str | None = None) -> str:

    project_id = os.environ["GOOGLE_CLOUD_PROJECT"]
    location = os.getenv("TRANSLATE_LOCATION", "global")

    client = translate.TranslationServiceClient()
    parent = f"projects/{project_id}/locations/{location}"

    request = {
        "parent": parent,
        "contents": [text],
        "target_language_code": target_language,
    }
    if source_language:
        request["source_language_code"] = source_language

    response = client.translate_text(request=request)
    return response.translations[0].translated_text
