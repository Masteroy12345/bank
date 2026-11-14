"""Smoke tests for the SAFINUM 13-language catalog and draft safeguards."""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CSV_PATH = ROOT / "liste_mots_a_traduire.csv"
DICT_PATH = ROOT / "extension" / "dictionary.js"
ITEMS_PATH = ROOT / "extension" / "recorder_items.js"
CONTENT_PATH = ROOT / "extension" / "content.js"
POPUP_PATH = ROOT / "extension" / "popup.js"
POPUP_HTML_PATH = ROOT / "extension" / "popup.html"
EXPECTED = [
    "pidgin", "fulfulde", "ewondo", "makaa", "kanuri", "arabe_choa",
    "masa", "bafia", "toupouri", "basaa", "duala", "yemba", "mafa",
]
NEW = EXPECTED[3:]
EMPTY = {"", "A VALIDER", "NE PAS TRADUIRE"}

with CSV_PATH.open(encoding="utf-8-sig", newline="") as stream:
    rows = [row for row in csv.reader(stream, delimiter=";") if row and not row[0].startswith("#")]
header = rows[0]
col = {name: index for index, name in enumerate(header)}
assert all(row[col["id"]].strip() for row in rows[1:]), "CSV contains a blank-ID data row"
lang_cols = [name for name in header[col["anglais"] + 1 : col["remarque"]] if not name.startswith("fiabilite_")]
assert lang_cols == EXPECTED, f"Unexpected language order/count: {lang_cols}"
for code in NEW:
    assert f"fiabilite_{code}" in col, f"Missing reliability column for {code}"
    for row in rows[1:]:
        assert row[col[code]].strip() in EMPTY, f"Unreviewed translation in {code}: {row[col['id']]}"
        assert row[col[f"fiabilite_{code}"]].strip() in EMPTY, f"Unreviewed reliability in {code}: {row[col['id']]}"

source = DICT_PATH.read_text(encoding="utf-8")
payload = json.loads(source.split("=", 1)[1].strip().removesuffix(";"))
languages = payload["languages"]
assert [language["code"] for language in languages] == EXPECTED
by_code = {language["code"]: language for language in languages}
for code in EXPECTED:
    language = by_code[code]
    assert language["ttsMode"] == "system-exact", f"Foreign-language fallback enabled for {code}"
    assert language["ttsLang"] == language["htmlLang"], f"TTS locale differs from selected language for {code}"
for code in EXPECTED[:3]:
    language = by_code[code]
    assert language["translationStatus"] == "draft"
    assert language["entryCount"] > 0
    assert language["allowAI"] is True
for code in NEW:
    language = by_code[code]
    assert language["translationStatus"] == "pending"
    assert language["entryCount"] == 0
    assert language["allowAI"] is False
    assert language["ttsMode"] == "system-exact"
    assert language["htmlLang"]
for entry in payload["entries"].values():
    for code in NEW:
        assert not entry.get(code), f"Generated dictionary contains an unreviewed {code} translation"
    assert not str(entry.get("id", "")).startswith(("X", "D")), "Protected financial/date row entered the dictionary"

items_source = ITEMS_PATH.read_text(encoding="utf-8")
items = json.loads(items_source.split("=", 1)[1].strip().removesuffix(";"))
assert all(not str(item.get("id", "")).startswith(("X", "D")) for item in items)
content = CONTENT_PATH.read_text(encoding="utf-8")
popup = POPUP_PATH.read_text(encoding="utf-8")
popup_html = POPUP_HTML_PATH.read_text(encoding="utf-8")
assert 'ttsMode === "approximate"' not in content
assert 'pickVoice("fr") || pickVoice("en")' not in content
assert "exactVoice(lang.htmlLang)" in content
assert "sourceVoice(seg.lang)" in content
assert "voiceFr" not in popup and "voiceEn" not in popup
assert "voice-fr" not in popup_html and "voice-en" not in popup_html
print("PASS: 13 languages in order; new translations blank; no new AI translation; existing translations remain drafts; protected rows excluded; all playback requires exact-language voices or native recordings.")
