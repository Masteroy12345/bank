#!/usr/bin/env python3
"""Create the private SAFINUM database resources in an Appwrite project.

Required environment variables: APPWRITE_ENDPOINT, APPWRITE_PROJECT_ID,
APPWRITE_API_KEY. The API key is never printed or written to disk.
"""
from __future__ import annotations

import json
import os
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

ENDPOINT = os.getenv("APPWRITE_ENDPOINT", "https://vps.kernelforge.codes/v1").rstrip("/")
PROJECT_ID = os.getenv("APPWRITE_PROJECT_ID", "bank")
API_KEY = os.getenv("APPWRITE_API_KEY", "")
DATABASE_ID = os.getenv("APPWRITE_DATABASE_ID", "safinum")
TRANSLATIONS_ID = os.getenv("APPWRITE_TRANSLATIONS_COLLECTION_ID", "translation_suggestions")
AUDIO_ID = os.getenv("APPWRITE_AUDIO_COLLECTION_ID", "audio_contributions")
BUCKET_ID = os.getenv("APPWRITE_AUDIO_BUCKET_ID", "safinum-audio")


def segment(value: str) -> str:
    return quote(value, safe="")


def request(method: str, path: str, payload: dict | None = None):
    headers = {
        "X-Appwrite-Project": PROJECT_ID,
        "X-Appwrite-Key": API_KEY,
        "Accept": "application/json",
        "User-Agent": "SAFINUM-Appwrite-Setup/1.0",
    }
    data = None
    if payload is not None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = Request(ENDPOINT + path, data=data, headers=headers, method=method)
    try:
        with urlopen(req, timeout=25) as response:
            content = response.read()
            return response.status, json.loads(content.decode("utf-8")) if content else None
    except HTTPError as exc:
        content = exc.read().decode("utf-8", errors="replace")
        try:
            details = json.loads(content)
            message = details.get("message", "Erreur Appwrite")
        except Exception:
            message = "Erreur Appwrite"
        raise RuntimeError(f"Appwrite {exc.code}: {str(message)[:250]}") from None
    except (URLError, TimeoutError, OSError):
        raise RuntimeError("Instance Appwrite inaccessible.") from None


def ensure_get_or_create(get_path: str, create_path: str, payload: dict, label: str):
    try:
        _, result = request("GET", get_path)
        print(f"Déjà présent : {label}")
        return result
    except RuntimeError as exc:
        if "Appwrite 404" not in str(exc):
            raise
    _, result = request("POST", create_path, payload)
    print(f"Créé : {label}")
    return result


def ensure_attribute(collection_id: str, key: str, kind: str, *, size: int | None = None, required: bool = True, default=None):
    base = f"/databases/{segment(DATABASE_ID)}/collections/{segment(collection_id)}/attributes"
    get_path = f"{base}/{kind}/{segment(key)}"
    try:
        _, attribute = request("GET", get_path)
        if attribute.get("status") == "available":
            return
        print(f"En attente de l’attribut {collection_id}.{key}…")
    except RuntimeError as exc:
        if "Appwrite 404" not in str(exc):
            raise
        payload = {"key": key, "required": required}
        if size is not None:
            payload["size"] = size
        if default is not None:
            payload["default"] = default
        _, attribute = request("POST", f"{base}/{kind}", payload)
        print(f"Attribut demandé : {collection_id}.{key}")
    for _ in range(40):
        try:
            _, attribute = request("GET", get_path)
            if attribute.get("status") == "available":
                return
            if attribute.get("status") == "failed":
                raise RuntimeError(f"Échec de création de l’attribut {collection_id}.{key}.")
        except RuntimeError as exc:
            if "Appwrite 404" not in str(exc):
                raise
        time.sleep(1)
    raise RuntimeError(f"Délai dépassé pour l’attribut {collection_id}.{key}.")


def ensure_index(collection_id: str, key: str, attributes: list[str]):
    base = f"/databases/{segment(DATABASE_ID)}/collections/{segment(collection_id)}/indexes"
    get_path = f"{base}/{segment(key)}"
    try:
        _, result = request("GET", get_path)
        if result.get("status") == "available":
            return
        if result.get("status") == "failed":
            raise RuntimeError(f"Échec de création de l’index {collection_id}.{key}.")
    except RuntimeError as exc:
        if "Appwrite 404" not in str(exc):
            raise
    else:
        print(f"En attente de l’index {collection_id}.{key}…")
    if "result" not in locals() or result.get("status") == "failed":
        request("POST", base, {"key": key, "type": "key", "attributes": attributes})
        print(f"Index demandé : {collection_id}.{key}")
    for _ in range(40):
        try:
            _, result = request("GET", get_path)
            if result.get("status") == "available":
                return
            if result.get("status") == "failed":
                raise RuntimeError(f"Échec de création de l’index {collection_id}.{key}.")
        except RuntimeError as exc:
            if "Appwrite 404" not in str(exc):
                raise
        time.sleep(1)
    raise RuntimeError(f"Délai dépassé pour l’index {collection_id}.{key}.")


def ensure_collection(collection_id: str, name: str):
    return ensure_get_or_create(
        f"/databases/{segment(DATABASE_ID)}/collections/{segment(collection_id)}",
        f"/databases/{segment(DATABASE_ID)}/collections",
        {"collectionId": collection_id, "name": name, "permissions": [], "documentSecurity": False},
        f"collection {collection_id} (privée)",
    )


def setup_translation_collection():
    ensure_collection(TRANSLATIONS_ID, "SAFINUM — propositions de traduction")
    strings = [
        ("phrase_key", 80, True, None),
        ("source_locale", 8, True, None),
        ("target_locale", 8, True, None),
        ("source_text", 600, True, None),
        ("translated_text", 600, True, None),
        ("dialect", 120, True, ""),
        ("speaker_role", 20, True, None),
        ("status", 32, True, "pending_review"),
        ("created_at", 40, True, None),
    ]
    for key, size, required, default in strings:
        ensure_attribute(TRANSLATIONS_ID, key, "string", size=size, required=required, default=default)
    ensure_attribute(TRANSLATIONS_ID, "consent", "boolean")
    ensure_index(TRANSLATIONS_ID, "status_idx", ["status"])
    ensure_index(TRANSLATIONS_ID, "translation_lookup_idx", ["phrase_key", "source_locale", "target_locale", "status"])
    ensure_index(TRANSLATIONS_ID, "catalog_lookup_idx", ["target_locale", "source_locale", "status"])


def setup_audio_collection():
    ensure_collection(AUDIO_ID, "SAFINUM — métadonnées audio privées")
    strings = [
        ("phrase_key", 80, True, None),
        ("locale", 8, True, None),
        ("dialect", 120, True, ""),
        ("speaker_role", 20, True, None),
        ("file_id", 36, True, None),
        ("mime_type", 80, True, None),
        ("sha256", 64, True, None),
        ("status", 32, True, "pending_review"),
        ("created_at", 40, True, None),
    ]
    for key, size, required, default in strings:
        ensure_attribute(AUDIO_ID, key, "string", size=size, required=required, default=default)
    ensure_attribute(AUDIO_ID, "consent", "boolean")
    ensure_index(AUDIO_ID, "audio_status_idx", ["status"])
    ensure_index(AUDIO_ID, "audio_lookup_idx", ["locale", "phrase_key", "status"])


def setup_audio_bucket():
    get_path = f"/storage/buckets/{segment(BUCKET_ID)}"
    create_path = "/storage/buckets"
    payload = {
        "bucketId": BUCKET_ID,
        "name": "SAFINUM — audios privés en attente de revue",
        "permissions": [],
        "fileSecurity": True,
        "enabled": True,
        "maximumFileSize": 12 * 1024 * 1024,
        "allowedFileExtensions": ["webm", "ogg", "wav", "mp3", "m4a"],
    }
    ensure_get_or_create(get_path, create_path, payload, f"bucket {BUCKET_ID} (privé)")


def main():
    if not API_KEY:
        raise SystemExit("APPWRITE_API_KEY doit être fourni uniquement dans l’environnement du serveur.")
    print(f"Appwrite : {ENDPOINT} · projet {PROJECT_ID}")
    ensure_get_or_create(
        f"/databases/{segment(DATABASE_ID)}",
        "/databases",
        {"databaseId": DATABASE_ID, "name": "SAFINUM — données linguistiques", "enabled": True},
        f"base de données {DATABASE_ID}",
    )
    setup_translation_collection()
    setup_audio_collection()
    setup_audio_bucket()
    print("Initialisation Appwrite terminée. Les collections et audios ne sont pas accessibles publiquement.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        # Error content is sanitized by request(); never print environment or request headers.
        print(f"Échec d’initialisation : {exc}", file=sys.stderr)
        raise SystemExit(1)
