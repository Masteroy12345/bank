"""Minimal Appwrite REST adapter for SAFINUM's private server-side data.

The Appwrite API key is read only from the API process environment. It must never
be placed in Flutter, static assets, source control, or an HTTP response.
"""
from __future__ import annotations

import json
import os
import uuid
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen
from typing import Any, Iterable


APPWRITE_ENDPOINT = os.getenv("APPWRITE_ENDPOINT", "https://vps.kernelforge.codes/v1").rstrip("/")
APPWRITE_PROJECT_ID = os.getenv("APPWRITE_PROJECT_ID", "bank")
APPWRITE_API_KEY = os.getenv("APPWRITE_API_KEY", "")
APPWRITE_DATABASE_ID = os.getenv("APPWRITE_DATABASE_ID", "safinum")
APPWRITE_TRANSLATIONS_COLLECTION_ID = os.getenv(
    "APPWRITE_TRANSLATIONS_COLLECTION_ID", "translation_suggestions"
)
APPWRITE_AUDIO_COLLECTION_ID = os.getenv("APPWRITE_AUDIO_COLLECTION_ID", "audio_contributions")
APPWRITE_AUDIO_BUCKET_ID = os.getenv("APPWRITE_AUDIO_BUCKET_ID", "safinum-audio")


class AppwriteError(RuntimeError):
    """Sanitized Appwrite request error; never contains request headers or API key."""

    def __init__(self, status: int, message: str) -> None:
        super().__init__(message)
        self.status = status


def is_configured() -> bool:
    return bool(APPWRITE_API_KEY)


def _segment(value: str) -> str:
    return quote(value, safe="")


def _request(
    method: str,
    path: str,
    *,
    data: dict[str, Any] | None = None,
    raw_body: bytes | None = None,
    content_type: str | None = None,
    timeout: int = 20,
) -> tuple[Any, bytes]:
    if not is_configured():
        raise AppwriteError(503, "La persistance Appwrite n’est pas configurée côté serveur.")
    headers = {
        "X-Appwrite-Project": APPWRITE_PROJECT_ID,
        "X-Appwrite-Key": APPWRITE_API_KEY,
        "Accept": "application/json",
        "User-Agent": "SAFINUM-API/1.0",
    }
    body = raw_body
    if data is not None:
        body = json.dumps(data, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        headers["Content-Type"] = "application/json"
    elif content_type:
        headers["Content-Type"] = content_type
    req = Request(APPWRITE_ENDPOINT + path, data=body, headers=headers, method=method)
    try:
        with urlopen(req, timeout=timeout) as response:
            payload = response.read()
    except HTTPError as exc:
        # Do not echo request details; Appwrite's error body contains no credentials.
        try:
            response_data = json.loads(exc.read().decode("utf-8"))
            message = str(response_data.get("message", "Erreur Appwrite"))[:300]
        except Exception:
            message = "Erreur Appwrite"
        raise AppwriteError(exc.code, message) from None
    except (URLError, TimeoutError, OSError) as exc:
        raise AppwriteError(503, "Instance Appwrite inaccessible.") from None
    if not payload:
        return None, payload
    try:
        return json.loads(payload.decode("utf-8")), payload
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None, payload


def _query_equal(attribute: str, value: Any) -> str:
    values = value if isinstance(value, list) else [value]
    return f"equal({json.dumps(attribute)},{json.dumps(values, ensure_ascii=False)})"


def list_documents(
    collection_id: str,
    *,
    equals: dict[str, Any] | None = None,
    page_size: int = 100,
) -> list[dict[str, Any]]:
    """Fetch all rows matching simple equality filters with bounded pagination."""
    base = (
        f"/databases/{_segment(APPWRITE_DATABASE_ID)}/collections/"
        f"{_segment(collection_id)}/documents"
    )
    queries = [_query_equal(key, value) for key, value in (equals or {}).items()]
    results: list[dict[str, Any]] = []
    offset = 0
    while True:
        params = [("limit", str(page_size)), ("offset", str(offset))]
        params.extend(("queries[]", query) for query in queries)
        path = base + "?" + urlencode(params)
        response, _ = _request("GET", path)
        documents = response.get("documents", []) if isinstance(response, dict) else []
        results.extend(documents)
        if len(documents) < page_size or len(results) >= int(response.get("total", len(results))):
            break
        offset += len(documents)
    return results


def create_document(collection_id: str, document_id: str, data: dict[str, Any]) -> dict[str, Any]:
    path = (
        f"/databases/{_segment(APPWRITE_DATABASE_ID)}/collections/"
        f"{_segment(collection_id)}/documents"
    )
    response, _ = _request(
        "POST", path,
        data={"documentId": document_id, "data": data, "permissions": []},
    )
    return response


def update_document(collection_id: str, document_id: str, data: dict[str, Any]) -> dict[str, Any]:
    path = (
        f"/databases/{_segment(APPWRITE_DATABASE_ID)}/collections/"
        f"{_segment(collection_id)}/documents/{_segment(document_id)}"
    )
    response, _ = _request("PATCH", path, data={"data": data})
    return response


def _multipart_file(file_id: str, filename: str, mime_type: str, content: bytes) -> tuple[str, bytes]:
    boundary = "----SAFINUM" + uuid.uuid4().hex
    chunks = [
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"fileId\"\r\n\r\n{file_id}\r\n".encode(),
        (
            f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; "
            f"filename=\"{filename}\"\r\nContent-Type: {mime_type}\r\n\r\n"
        ).encode(),
        content,
        f"\r\n--{boundary}--\r\n".encode(),
    ]
    return f"multipart/form-data; boundary={boundary}", b"".join(chunks)


def upload_private_audio(file_id: str, filename: str, mime_type: str, content: bytes) -> dict[str, Any]:
    path = f"/storage/buckets/{_segment(APPWRITE_AUDIO_BUCKET_ID)}/files"
    content_type, body = _multipart_file(file_id, filename, mime_type, content)
    response, _ = _request("POST", path, raw_body=body, content_type=content_type, timeout=45)
    return response


def get_private_audio(file_id: str) -> bytes:
    path = (
        f"/storage/buckets/{_segment(APPWRITE_AUDIO_BUCKET_ID)}/files/"
        f"{_segment(file_id)}/view"
    )
    _, payload = _request("GET", path, timeout=45)
    return payload


def delete_private_audio(file_id: str) -> None:
    path = (
        f"/storage/buckets/{_segment(APPWRITE_AUDIO_BUCKET_ID)}/files/"
        f"{_segment(file_id)}"
    )
    _request("DELETE", path)


def all_count(collection_id: str, *, equals: dict[str, Any] | None = None) -> int:
    base = (
        f"/databases/{_segment(APPWRITE_DATABASE_ID)}/collections/"
        f"{_segment(collection_id)}/documents"
    )
    params = [("limit", "1")]
    params.extend(("queries[]", _query_equal(key, value)) for key, value in (equals or {}).items())
    response, _ = _request("GET", base + "?" + urlencode(params))
    return int(response.get("total", 0))
