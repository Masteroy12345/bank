#!/usr/bin/env python3
"""Smoke tests for a running local SAFINUM API; test rows/files are removed afterward."""
import json
import sqlite3
import sys
import urllib.error
import urllib.request
from pathlib import Path

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000"
ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "safinum.sqlite3"
created_translations = []
created_audio = []


def request(path, method="GET", payload=None, expected=200):
    data = None if payload is None else json.dumps(payload).encode()
    headers = {"Content-Type": "application/json"} if data is not None else {}
    req = urllib.request.Request(BASE + path, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            body = response.read().decode()
            assert response.status == expected, (path, response.status, body)
            return json.loads(body) if body else None
    except urllib.error.HTTPError as error:
        body = error.read().decode()
        assert error.code == expected, (path, error.code, body)
        return json.loads(body)


def cleanup():
    if not DB_PATH.exists():
        return
    audio_files = []
    with sqlite3.connect(DB_PATH) as conn:
        for audio_id in created_audio:
            row = conn.execute("SELECT file_name FROM audio_contributions WHERE id=?", (audio_id,)).fetchone()
            if row:
                audio_files.append(ROOT / "data" / "audio" / row[0])
            conn.execute("DELETE FROM audio_contributions WHERE id=?", (audio_id,))
        for translation_id in created_translations:
            conn.execute("DELETE FROM translation_suggestions WHERE id=?", (translation_id,))
    for file_path in audio_files:
        file_path.unlink(missing_ok=True)


def run():
    try:
        assert request("/health")["status"] == "ok"
        language_result = request("/api/v1/languages")
        assert len(language_result["items"]) == 10
        assert {"fr", "en"}.issubset(set(language_result["interface_locales"]))
        assert request("/api/v1/catalog/en")["items"]["balance_label"] == "Available balance"

        translated = request("/api/v1/translate", "POST", {
            "source_locale": "fr", "target_locale": "en", "phrase_key": "balance_label",
            "source_text": "Solde disponible"
        })
        assert translated["translation"] == "Available balance" and translated["translated"]

        financial = request("/api/v1/translate", "POST", {
            "source_locale": "fr", "target_locale": "en", "phrase_key": "transfer_confirmation",
            "source_text": "Confirmer l’envoi de 15 000 XAF à Aline ?",
            "variables": {"amount": "15 000 XAF", "recipient": "Aline"}
        })
        assert financial["translation"] == "Confirm the transfer of 15 000 XAF to Aline?"
        assert financial["financial_tokens_preserved"] is True
        request("/api/v1/translate", "POST", {
            "source_locale": "fr", "target_locale": "en", "phrase_key": "transfer_confirmation",
            "variables": {"amount": "15 000 XAF"}
        }, expected=422)

        pending = request("/api/v1/translate", "POST", {
            "source_locale": "fr", "target_locale": "ewo", "phrase_key": "balance_label",
            "source_text": "Solde disponible"
        })
        assert pending["translated"] is False and pending["translation"] == "Solde disponible"

        proposal = {
            "phrase_key": "balance_account", "source_locale": "fr", "target_locale": "ewo",
            "source_text": "Compte principal · XAF", "translated_text": "XAF / demo-review-sample",
            "dialect": "test only", "speaker_role": "native", "consent": True
        }
        created = request("/api/v1/contributions/translations", "POST", proposal, expected=201)
        created_translations.append(created["id"])
        assert created["status"] == "pending_review" and created["served_to_users"] is False
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute("UPDATE translation_suggestions SET status='approved' WHERE id=?", (created["id"],))

        approved = request("/api/v1/translate", "POST", {
            "source_locale": "fr", "target_locale": "ewo", "phrase_key": "balance_account",
            "source_text": "Compte principal · XAF"
        })
        assert approved["status"] == "community_reviewed"
        assert approved["translation"] == "XAF / demo-review-sample"
        local_catalog = request("/api/v1/catalog/ewo?source_locale=fr")
        assert local_catalog["supported"] is True
        assert local_catalog["items"]["balance_account"] == "XAF / demo-review-sample"

        unsafe = dict(proposal, translated_text="Compte principal · FCFA")
        request("/api/v1/contributions/translations", "POST", unsafe, expected=422)
        wrong_source = dict(proposal, source_text="Solde fictif")
        request("/api/v1/contributions/translations", "POST", wrong_source, expected=422)

        audio_url = BASE + "/api/v1/contributions/audio?language_code=ewo&phrase_key=balance_label&speaker_role=native&consent=true"
        audio_req = urllib.request.Request(
            audio_url, data=b"FAKE-TEST-AUDIO-NOT-A-VOICE",
            headers={"Content-Type": "audio/webm"}, method="POST"
        )
        with urllib.request.urlopen(audio_req, timeout=5) as response:
            audio = json.loads(response.read().decode())
            assert response.status == 201
        created_audio.append(audio["id"])
        assert audio["status"] == "pending_review" and audio["served_to_users"] is False
        try:
            urllib.request.urlopen(BASE + "/api/v1/pronunciation/ewo/balance_label", timeout=5)
            raise AssertionError("pending audio was publicly served")
        except urllib.error.HTTPError as error:
            assert error.code == 404

        ussd = request("/api/v1/ussd", "POST", {"session_id": "test-1", "text": "", "locale": "en"})
        assert ussd["response"].startswith("CON ") and "Check balance" in ussd["response"]
        ussd_local = request("/api/v1/ussd", "POST", {"session_id": "test-2", "text": "", "locale": "ewo"})
        assert ussd_local["translated"] is False and ussd_local["warning"]

        print("PASS: FR/EN, 10 langues, placeholders financiers, collecte et activation revue, contrôle devise, audio en attente, USSD.")
    finally:
        cleanup()


if __name__ == "__main__":
    run()
