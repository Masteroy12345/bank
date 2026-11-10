from __future__ import annotations

import hashlib
import json
import re
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from . import appwrite_store

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
AUDIO_DIR = DATA_DIR / "audio"
DB_PATH = DATA_DIR / "safinum.sqlite3"
WEB_DIR = ROOT / "web"

with (DATA_DIR / "languages.json").open(encoding="utf-8") as f:
    LANGUAGES: list[dict[str, Any]] = json.load(f)
with (DATA_DIR / "catalog.json").open(encoding="utf-8") as f:
    CATALOG: dict[str, dict[str, str]] = json.load(f)

LANG_BY_CODE = {item["code"]: item for item in LANGUAGES}
SUPPORTED_LOCALES = {"fr", "en", *LANG_BY_CODE.keys()}
CATALOG_KEYS = set(CATALOG)

app = FastAPI(
    title="SAFINUM Language Layer",
    description=(
        "Prototype bilingue FR/EN et API de collecte/revue de langues camerounaises. "
        "Toutes les opérations bancaires de la démo sont fictives."
    ),
    version="0.1.0",
)
app.mount("/static", StaticFiles(directory=WEB_DIR), name="static")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def db() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    if appwrite_store.is_configured():
        return
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    with db() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS translation_suggestions (
                id TEXT PRIMARY KEY,
                phrase_key TEXT NOT NULL,
                source_locale TEXT NOT NULL,
                target_locale TEXT NOT NULL,
                source_text TEXT NOT NULL,
                translated_text TEXT NOT NULL,
                dialect TEXT NOT NULL DEFAULT '',
                speaker_role TEXT NOT NULL,
                consent INTEGER NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending_review',
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS audio_contributions (
                id TEXT PRIMARY KEY,
                phrase_key TEXT NOT NULL,
                locale TEXT NOT NULL,
                dialect TEXT NOT NULL DEFAULT '',
                speaker_role TEXT NOT NULL,
                consent INTEGER NOT NULL,
                file_name TEXT NOT NULL,
                mime_type TEXT NOT NULL,
                sha256 TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending_review',
                created_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_translation_review
                ON translation_suggestions(status, target_locale);
            CREATE INDEX IF NOT EXISTS idx_audio_review
                ON audio_contributions(status, locale, phrase_key);
            """
        )


init_db()


class TranslationRequest(BaseModel):
    source_locale: str = Field(min_length=2, max_length=8)
    target_locale: str = Field(min_length=2, max_length=8)
    phrase_key: str | None = Field(default=None, max_length=80)
    source_text: str | None = Field(default=None, max_length=1000)
    variables: dict[str, str] = Field(default_factory=dict)


class TranslationSuggestion(BaseModel):
    phrase_key: str = Field(min_length=2, max_length=80)
    source_locale: str = Field(min_length=2, max_length=8)
    target_locale: str = Field(min_length=2, max_length=8)
    source_text: str = Field(min_length=1, max_length=600)
    translated_text: str = Field(min_length=1, max_length=600)
    dialect: str = Field(default="", max_length=120)
    speaker_role: str = Field(pattern="^(native|fluent)$")
    consent: bool


def require_locale(code: str) -> None:
    if code not in SUPPORTED_LOCALES:
        raise HTTPException(status_code=422, detail=f"Langue non reconnue: {code}")


def numeric_tokens(text: str) -> list[str]:
    # Keep amount-like sequences and their exact ordering. Whitespace is ignored only
    # for comparisons so 15 000 and 15000 represent the same number; punctuation stays.
    found = re.findall(r"(?<!\w)\d+(?:[\s\u00a0.,]\d+)*(?!\w)", text)
    return [re.sub(r"[\s\u00a0]", "", token) for token in found]


def currency_tokens(text: str) -> list[str]:
    found = re.findall(r"(?i)(?<!\w)(FCFA|XAF|CFA|EUR|USD|€|\$)(?!\w)", text)
    return [token.upper() for token in found]


def financial_tokens_preserved(source: str, translated: str) -> bool:
    return numeric_tokens(source) == numeric_tokens(translated) and currency_tokens(source) == currency_tokens(translated)


def format_template(template: str, variables: dict[str, str]) -> str:
    required = set(re.findall(r"\{([A-Za-z_][A-Za-z0-9_]*)\}", template))
    if required != set(variables):
        missing = sorted(required - set(variables))
        extra = sorted(set(variables) - required)
        raise HTTPException(
            status_code=422,
            detail={"message": "Variables incorrectes", "missing": missing, "extra": extra},
        )
    result = template
    for key, value in variables.items():
        result = result.replace("{" + key + "}", value)
    return result


def template_variables(template: str) -> set[str]:
    return set(re.findall(r"\{([A-Za-z_][A-Za-z0-9_]*)\}", template))


def render_template(template: str, variables: dict[str, str]) -> str:
    if template_variables(template):
        return format_template(template, variables)
    if variables:
        raise HTTPException(status_code=422, detail="Cette phrase n’accepte pas de variables.")
    return template


def response_for_missing(req: TranslationRequest) -> dict[str, Any]:
    fallback = req.source_text or ""
    if not fallback and req.phrase_key in CATALOG and req.source_locale in CATALOG[req.phrase_key]:
        fallback = render_template(CATALOG[req.phrase_key][req.source_locale], req.variables)
    return {
        "translated": False,
        "status": "needs_review",
        "source_locale": req.source_locale,
        "target_locale": req.target_locale,
        "translation": fallback,
        "warning": "Aucune phrase validée dans la mémoire pour cette paire de langues; le texte source est conservé.",
        "financial_tokens_preserved": True,
    }


@app.get("/", include_in_schema=False)
def home() -> FileResponse:
    return FileResponse(WEB_DIR / "index.html")


@app.get("/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "safinum-language-layer",
        "version": app.version,
        "persistence": "appwrite" if appwrite_store.is_configured() else "sqlite",
    }


@app.get("/api/v1/languages")
def list_languages() -> dict[str, Any]:
    return {
        "interface_locales": ["fr", "en"],
        "items": LANGUAGES,
        "note": "Les dix langues locales sont des langues pilotes pour la collecte; leurs traductions bancaires ne sont pas déclarées actives.",
    }


@app.get("/api/v1/catalog/{locale}")
def get_catalog(locale: str, source_locale: str = Query(default="fr", min_length=2, max_length=8)) -> dict[str, Any]:
    require_locale(locale)
    require_locale(source_locale)
    if locale in {"fr", "en"}:
        return {
            "locale": locale,
            "supported": True,
            "items": {key: value[locale] for key, value in CATALOG.items()},
            "missing_keys": [],
            "translation_source": "approved_demo_catalog",
        }
    if source_locale not in {"fr", "en"}:
        raise HTTPException(status_code=422, detail="La source du catalogue local doit être fr ou en.")
    if appwrite_store.is_configured():
        rows = appwrite_store.list_documents(
            appwrite_store.APPWRITE_TRANSLATIONS_COLLECTION_ID,
            equals={"target_locale": locale, "source_locale": source_locale, "status": "approved"},
        )
        rows.sort(key=lambda row: row.get("created_at", ""))
    else:
        with db() as conn:
            rows = conn.execute(
                """SELECT phrase_key, translated_text FROM translation_suggestions
                   WHERE target_locale = ? AND source_locale = ? AND status = 'approved'
                   ORDER BY created_at ASC""",
                (locale, source_locale),
            ).fetchall()
    items = {row["phrase_key"]: row["translated_text"] for row in rows}
    missing_keys = sorted(CATALOG_KEYS - set(items))
    return {
        "locale": locale,
        "supported": bool(items),
        "complete": not missing_keys,
        "items": items,
        "missing_keys": missing_keys,
        "fallback_locale": source_locale,
        "translation_source": "community_reviewed" if items else None,
        "warning": "Les clés manquantes doivent rester dans la langue source." if missing_keys else None,
    }


@app.post("/api/v1/translate")
def translate(req: TranslationRequest) -> dict[str, Any]:
    require_locale(req.source_locale)
    require_locale(req.target_locale)
    if req.source_locale == req.target_locale:
        if req.phrase_key in CATALOG and req.source_locale in CATALOG[req.phrase_key]:
            text = render_template(CATALOG[req.phrase_key][req.source_locale], req.variables)
            if req.source_text is not None and req.source_text != text:
                raise HTTPException(status_code=422, detail="Le texte source ne correspond pas à la phrase du catalogue.")
        else:
            if req.variables:
                raise HTTPException(status_code=422, detail="Une phrase avec variables doit avoir une clé de catalogue.")
            text = req.source_text or ""
        return {
            "translated": True,
            "status": "unchanged",
            "source_locale": req.source_locale,
            "target_locale": req.target_locale,
            "translation": text,
            "financial_tokens_preserved": True,
        }

    if req.phrase_key and req.phrase_key in CATALOG:
        entry = CATALOG[req.phrase_key]
        if req.source_locale in entry and req.target_locale in entry:
            source_template = entry[req.source_locale]
            target_template = entry[req.target_locale]
            if template_variables(source_template) != template_variables(target_template):
                raise HTTPException(status_code=409, detail="Les variables de la traduction ne correspondent pas à la source.")
            source_text = render_template(source_template, req.variables)
            translated = render_template(target_template, req.variables)
            if req.source_text is not None and req.source_text != source_text:
                raise HTTPException(status_code=422, detail="Le texte source ne correspond pas à la phrase du catalogue.")
            if not financial_tokens_preserved(source_text, translated):
                raise HTTPException(status_code=409, detail="Échec du contrôle de conservation des montants ou devises.")
            return {
                "translated": True,
                "status": "approved_demo_phrase",
                "source_locale": req.source_locale,
                "target_locale": req.target_locale,
                "phrase_key": req.phrase_key,
                "translation": translated,
                "financial_tokens_preserved": True,
            }

    if req.source_text:
        for key, entry in CATALOG.items():
            source_template = entry.get(req.source_locale, "")
            target_template = entry.get(req.target_locale, "")
            if source_template and not template_variables(source_template) and source_template == req.source_text and target_template:
                if template_variables(source_template) != template_variables(target_template):
                    raise HTTPException(status_code=409, detail="Les variables de la traduction ne correspondent pas à la source.")
                translated = entry[req.target_locale]
                if not financial_tokens_preserved(req.source_text, translated):
                    raise HTTPException(status_code=409, detail="Échec du contrôle de conservation des montants ou devises.")
                return {
                    "translated": True,
                    "status": "approved_demo_phrase",
                    "source_locale": req.source_locale,
                    "target_locale": req.target_locale,
                    "phrase_key": key,
                    "translation": translated,
                    "financial_tokens_preserved": True,
                }
    if req.target_locale not in {"fr", "en"}:
        key = req.phrase_key
        if not key and req.source_text:
            key = next(
                (candidate for candidate, entry in CATALOG.items()
                 if entry.get(req.source_locale) == req.source_text and not template_variables(entry.get(req.source_locale, ""))),
                None,
            )
        if key in CATALOG and req.source_locale in CATALOG[key]:
            source_template = CATALOG[key][req.source_locale]
            source_text = render_template(source_template, req.variables)
            if req.source_text is not None and req.source_text != source_text:
                raise HTTPException(status_code=422, detail="Le texte source ne correspond pas à la phrase du catalogue.")
            if appwrite_store.is_configured():
                matches = appwrite_store.list_documents(
                    appwrite_store.APPWRITE_TRANSLATIONS_COLLECTION_ID,
                    equals={
                        "phrase_key": key,
                        "source_locale": req.source_locale,
                        "target_locale": req.target_locale,
                        "status": "approved",
                    },
                )
                matches = [row for row in matches if row.get("source_text") == source_template]
                matches.sort(key=lambda row: row.get("created_at", ""), reverse=True)
                row = matches[0] if matches else None
            else:
                with db() as conn:
                    row = conn.execute(
                        """SELECT translated_text FROM translation_suggestions
                           WHERE phrase_key = ? AND source_locale = ? AND target_locale = ?
                           AND source_text = ? AND status = 'approved'
                           ORDER BY created_at DESC LIMIT 1""",
                        (key, req.source_locale, req.target_locale, source_template),
                    ).fetchone()
            if row:
                translated_template = row["translated_text"]
                if template_variables(source_template) != template_variables(translated_template):
                    raise HTTPException(status_code=409, detail="Les variables de la traduction locale ne correspondent pas à la source.")
                translated = render_template(translated_template, req.variables)
                if not financial_tokens_preserved(source_text, translated):
                    raise HTTPException(status_code=409, detail="Échec du contrôle de conservation des montants ou devises.")
                return {
                    "translated": True,
                    "status": "community_reviewed",
                    "source_locale": req.source_locale,
                    "target_locale": req.target_locale,
                    "phrase_key": key,
                    "translation": translated,
                    "financial_tokens_preserved": True,
                }
    return response_for_missing(req)


@app.post("/api/v1/contributions/translations", status_code=201)
def contribute_translation(suggestion: TranslationSuggestion) -> dict[str, Any]:
    require_locale(suggestion.source_locale)
    require_locale(suggestion.target_locale)
    if suggestion.source_locale == suggestion.target_locale:
        raise HTTPException(status_code=422, detail="La langue source et la langue cible doivent être différentes.")
    if suggestion.target_locale in {"fr", "en"}:
        raise HTTPException(status_code=422, detail="Ce formulaire est réservé aux langues camerounaises en collecte.")
    if suggestion.phrase_key not in CATALOG or suggestion.source_locale not in CATALOG[suggestion.phrase_key]:
        raise HTTPException(status_code=422, detail="La phrase choisie n’existe pas dans le catalogue de démonstration.")
    if suggestion.source_text != CATALOG[suggestion.phrase_key][suggestion.source_locale]:
        raise HTTPException(status_code=422, detail="Le texte source ne correspond pas à la phrase du catalogue.")
    if not suggestion.consent:
        raise HTTPException(status_code=422, detail="Le consentement à l’enregistrement de la proposition est obligatoire.")
    if not financial_tokens_preserved(suggestion.source_text, suggestion.translated_text):
        raise HTTPException(
            status_code=422,
            detail="Les chiffres, montants et devises doivent être conservés à l’identique dans la proposition.",
        )
    contribution_id = str(uuid.uuid4())
    contribution_data = {
        "phrase_key": suggestion.phrase_key,
        "source_locale": suggestion.source_locale,
        "target_locale": suggestion.target_locale,
        "source_text": suggestion.source_text,
        "translated_text": suggestion.translated_text,
        "dialect": suggestion.dialect.strip(),
        "speaker_role": suggestion.speaker_role,
        "consent": suggestion.consent,
        "status": "pending_review",
        "created_at": utc_now(),
    }
    if appwrite_store.is_configured():
        appwrite_store.create_document(
            appwrite_store.APPWRITE_TRANSLATIONS_COLLECTION_ID, contribution_id, contribution_data
        )
    else:
        with db() as conn:
            conn.execute(
                """INSERT INTO translation_suggestions
                   (id, phrase_key, source_locale, target_locale, source_text, translated_text,
                    dialect, speaker_role, consent, status, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending_review', ?)""",
                (
                    contribution_id,
                    suggestion.phrase_key,
                    suggestion.source_locale,
                    suggestion.target_locale,
                    suggestion.source_text,
                    suggestion.translated_text,
                    suggestion.dialect.strip(),
                    suggestion.speaker_role,
                    int(suggestion.consent),
                    contribution_data["created_at"],
                ),
            )
    return {
        "id": contribution_id,
        "status": "pending_review",
        "served_to_users": False,
        "message": "Proposition enregistrée pour revue communautaire; elle n’est pas encore utilisée comme traduction.",
    }


@app.post("/api/v1/contributions/audio", status_code=201)
async def contribute_audio(
    request: Request,
    language_code: str = Query(min_length=2, max_length=8),
    phrase_key: str = Query(min_length=2, max_length=80),
    dialect: str = Query(default="", max_length=120),
    speaker_role: str = Query(pattern="^(native|fluent)$"),
    consent: bool = Query(default=False),
) -> dict[str, Any]:
    require_locale(language_code)
    if language_code in {"fr", "en"}:
        raise HTTPException(status_code=422, detail="La collecte audio de cette démo cible les langues camerounaises.")
    if phrase_key not in CATALOG:
        raise HTTPException(status_code=422, detail="Phrase de démonstration inconnue.")
    if not consent:
        raise HTTPException(status_code=422, detail="Le consentement à l’enregistrement audio est obligatoire.")
    content_type = request.headers.get("content-type", "").split(";", 1)[0].lower()
    allowed_types = {"audio/webm", "audio/ogg", "audio/wav", "audio/mpeg", "audio/mp4", "audio/x-wav"}
    if content_type not in allowed_types:
        raise HTTPException(status_code=415, detail="Format audio accepté : WebM, OGG, WAV, MP3 ou MP4 audio.")
    payload = await request.body()
    if not payload:
        raise HTTPException(status_code=400, detail="Fichier audio vide.")
    if len(payload) > 12 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="L’extrait audio dépasse la limite de 12 Mo.")
    extension = {
        "audio/webm": ".webm",
        "audio/ogg": ".ogg",
        "audio/wav": ".wav",
        "audio/x-wav": ".wav",
        "audio/mpeg": ".mp3",
        "audio/mp4": ".m4a",
    }[content_type]
    contribution_id = str(uuid.uuid4())
    file_name = contribution_id + extension
    digest = hashlib.sha256(payload).hexdigest()
    if appwrite_store.is_configured():
        appwrite_store.upload_private_audio(contribution_id, file_name, content_type, payload)
        try:
            appwrite_store.create_document(
                appwrite_store.APPWRITE_AUDIO_COLLECTION_ID,
                contribution_id,
                {
                    "phrase_key": phrase_key,
                    "locale": language_code,
                    "dialect": dialect.strip(),
                    "speaker_role": speaker_role,
                    "consent": True,
                    "file_id": contribution_id,
                    "mime_type": content_type,
                    "sha256": digest,
                    "status": "pending_review",
                    "created_at": utc_now(),
                },
            )
        except Exception:
            appwrite_store.delete_private_audio(contribution_id)
            raise
    else:
        AUDIO_DIR.mkdir(parents=True, exist_ok=True)
        (AUDIO_DIR / file_name).write_bytes(payload)
        with db() as conn:
            conn.execute(
                """INSERT INTO audio_contributions
                   (id, phrase_key, locale, dialect, speaker_role, consent, file_name,
                    mime_type, sha256, status, created_at)
                   VALUES (?, ?, ?, ?, ?, 1, ?, ?, ?, 'pending_review', ?)""",
                (contribution_id, phrase_key, language_code, dialect.strip(), speaker_role, file_name, content_type, digest, utc_now()),
            )
    return {
        "id": contribution_id,
        "status": "pending_review",
        "served_to_users": False,
        "sha256": digest,
        "message": "Audio enregistré pour revue; aucune voix n’est publiée avant validation.",
    }


@app.get("/api/v1/pronunciation/{language_code}/{phrase_key}")
def get_pronunciation(language_code: str, phrase_key: str) -> Response:
    require_locale(language_code)
    if appwrite_store.is_configured():
        rows = appwrite_store.list_documents(
            appwrite_store.APPWRITE_AUDIO_COLLECTION_ID,
            equals={"locale": language_code, "phrase_key": phrase_key, "status": "approved"},
        )
        rows.sort(key=lambda row: row.get("created_at", ""), reverse=True)
        row = rows[0] if rows else None
    else:
        with db() as conn:
            row = conn.execute(
                """SELECT file_name, mime_type FROM audio_contributions
                   WHERE locale = ? AND phrase_key = ? AND status = 'approved'
                   ORDER BY created_at DESC LIMIT 1""",
                (language_code, phrase_key),
            ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Aucun extrait de prononciation validé n’est encore disponible.")
    if appwrite_store.is_configured():
        audio = appwrite_store.get_private_audio(row["file_id"])
        return Response(content=audio, media_type=row["mime_type"])
    file_path = AUDIO_DIR / row["file_name"]
    if not file_path.is_file():
        raise HTTPException(status_code=404, detail="Le fichier audio validé est introuvable.")
    return FileResponse(file_path, media_type=row["mime_type"], filename=file_path.name)


@app.get("/api/v1/metrics")
def metrics() -> dict[str, Any]:
    if appwrite_store.is_configured():
        text_count = {
            status: appwrite_store.all_count(
                appwrite_store.APPWRITE_TRANSLATIONS_COLLECTION_ID, equals={"status": status}
            )
            for status in ("pending_review", "approved", "rejected")
        }
        audio_count = {
            status: appwrite_store.all_count(
                appwrite_store.APPWRITE_AUDIO_COLLECTION_ID, equals={"status": status}
            )
            for status in ("pending_review", "approved", "rejected")
        }
        approved = appwrite_store.list_documents(
            appwrite_store.APPWRITE_TRANSLATIONS_COLLECTION_ID, equals={"status": "approved"}
        )
        local_pairs = {
            (item["source_locale"], item["target_locale"])
            for item in approved if item.get("target_locale") not in {"fr", "en"}
        }
        return {
            "translation_suggestions": {k: v for k, v in text_count.items() if v},
            "audio_contributions": {k: v for k, v in audio_count.items() if v},
            "active_local_translation_pairs": len(local_pairs),
            "approved_local_phrases": sum(
                1 for item in approved if item.get("target_locale") not in {"fr", "en"}
            ),
            "note": "Les entrées collectées restent exclues de la traduction servie tant qu’elles ne sont pas validées.",
        }
    with db() as conn:
        text_count = conn.execute(
            "SELECT status, COUNT(*) AS n FROM translation_suggestions GROUP BY status"
        ).fetchall()
        audio_count = conn.execute(
            "SELECT status, COUNT(*) AS n FROM audio_contributions GROUP BY status"
        ).fetchall()
        active_pairs = conn.execute(
            """SELECT COUNT(*) AS n FROM (
                   SELECT DISTINCT source_locale, target_locale FROM translation_suggestions
                   WHERE status = 'approved' AND target_locale NOT IN ('fr', 'en')
               )"""
        ).fetchone()["n"]
        approved_local_phrases = conn.execute(
            """SELECT COUNT(*) AS n FROM translation_suggestions
               WHERE status = 'approved' AND target_locale NOT IN ('fr', 'en')"""
        ).fetchone()["n"]
    return {
        "translation_suggestions": {row["status"]: row["n"] for row in text_count},
        "audio_contributions": {row["status"]: row["n"] for row in audio_count},
        "active_local_translation_pairs": active_pairs,
        "approved_local_phrases": approved_local_phrases,
        "note": "Les entrées collectées restent exclues de la traduction servie tant qu’elles ne sont pas validées.",
    }


class USSDRequest(BaseModel):
    session_id: str = Field(min_length=1, max_length=100)
    text: str = Field(default="", max_length=100)
    locale: str = Field(default="fr", min_length=2, max_length=8)


@app.post("/api/v1/ussd")
def ussd(req: USSDRequest) -> dict[str, Any]:
    require_locale(req.locale)
    locale = req.locale if req.locale in {"fr", "en"} else "fr"
    is_local = req.locale not in {"fr", "en"}
    text = req.text.strip()
    if not text:
        menu = (
            "1. Consulter le solde\n2. Dernières opérations\n3. Envoyer de l’argent (simulation)\n0. Quitter"
            if locale == "fr"
            else "1. Check balance\n2. Recent activity\n3. Send money (simulation)\n0. Exit"
        )
        response = ("CON " if locale == "fr" else "CON ") + menu
        end_session = False
    else:
        choice = text.split("*")[-1]
        if choice == "1":
            response = "END Solde fictif : 125 000 XAF." if locale == "fr" else "END Demo balance: XAF 125,000."
            end_session = True
        elif choice == "2":
            response = "END Dernière opération fictive : + 12 500 XAF." if locale == "fr" else "END Latest demo activity: + XAF 12,500."
            end_session = True
        elif choice == "3":
            response = "END Simulation uniquement : aucun transfert réel n’est effectué." if locale == "fr" else "END Simulation only: no real transfer is made."
            end_session = True
        elif choice == "0":
            response = "END Merci. Démo terminée." if locale == "fr" else "END Thank you. Demo ended."
            end_session = True
        else:
            response = "END Choix non reconnu. Réessayez depuis le menu." if locale == "fr" else "END Invalid choice. Please try again from the menu."
            end_session = True
    if is_local:
        warning = "Langue locale en collecte : réponse USSD fournie en français jusqu’à validation des chaînes."
    else:
        warning = None
    return {
        "sessionId": req.session_id,
        "response": response,
        "end_session": end_session,
        "locale_requested": req.locale,
        "locale_served": locale,
        "translated": not is_local,
        "warning": warning,
    }


@app.exception_handler(Exception)
async def unexpected_error_handler(request: Request, exc: Exception) -> JSONResponse:
    # Do not leak database paths, local file paths, or exception internals to clients.
    return JSONResponse(status_code=500, content={"detail": "Erreur interne du prototype."})
