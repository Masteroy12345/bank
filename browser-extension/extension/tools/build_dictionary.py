"""Génère extension/dictionary.js à partir de liste_mots_a_traduire.csv.

Chaque colonne de langue du CSV (entre « anglais » et « remarque », hors
« fiabilite_* ») devient automatiquement une langue de l'extension.

Usage : python3 extension/tools/build_dictionary.py
"""
import csv
import json
import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CSV_PATH = ROOT / "liste_mots_a_traduire.csv"
OUT_PATH = ROOT / "extension" / "dictionary.js"

AUDIO_DIR = ROOT / "extension" / "audio"
ITEMS_PATH = ROOT / "extension" / "recorder_items.js"
AUDIO_EXT = {".mp3", ".ogg", ".webm", ".wav", ".m4a"}

# Toutes les langues exigent une voix système locale correspondant au code exact.
# Les seuls autres sons possibles sont les enregistrements natifs associés à une entrée.
# Les modèles mentionnés dans ttsResourceInfo sont publics mais non intégrés.
KNOWN = {
    "pidgin": {"label": "Pidgin camerounais", "htmlLang": "wes", "description": "pidgin camerounais (Kamtok)", "ttsLang": "wes", "ttsMode": "system-exact", "translationStatus": "draft", "allowAI": True, "ttsResourceInfo": "OmniVoice répertorie wes (10,06 h); poids CC BY-NC, modèle non intégré et qualité locale non validée. Aucun repli vers l'anglais."},
    "fulfulde": {"label": "Fulfulde", "htmlLang": "fub", "description": "fulfulde de l'Adamaoua, Cameroun", "ttsLang": "fub", "ttsMode": "system-exact", "translationStatus": "draft", "allowAI": True, "ttsResourceInfo": "OmniVoice répertorie le Fulfulde d'Adamawa (fub, 13,12 h); poids CC BY-NC, modèle non intégré et qualité locale non validée. Aucun repli vers le français."},
    "ewondo": {"label": "Ewondo", "htmlLang": "ewo", "description": "ewondo (Beti, région de Yaoundé, Cameroun)", "ttsLang": "ewo", "ttsMode": "system-exact", "translationStatus": "draft", "allowAI": True, "ttsResourceInfo": "OmniVoice répertorie ewo (12,71 h); poids CC BY-NC, modèle non intégré et qualité locale non validée. Un enregistrement natif de mot existe; aucun repli vers le français."},
    "makaa": {"label": "Makaa (Cameroun)", "htmlLang": "mcp", "description": "Makaa du Cameroun (ISO 639-3 mcp)", "ttsLang": "mcp", "ttsMode": "system-exact", "translationStatus": "pending", "allowAI": False, "ttsResourceInfo": "Modèle MMS TTS public pour mcp, licence CC BY-NC 4.0; non intégré à l'extension."},
    "kanuri": {"label": "Kanuri", "htmlLang": "kau", "description": "Kanuri (variété à confirmer localement)", "ttsLang": "kau", "ttsMode": "system-exact", "translationStatus": "pending", "allowAI": False, "ttsResourceInfo": "TWB Voice est CC BY-NC, mais son checkpoint est une voix fixe de Kanuri central nigérian (knc), pas une voix camerounaise validée; non intégré."},
    "arabe_choa": {"label": "Arabe Choa / Shuwa", "htmlLang": "shu", "description": "arabe tchadien Choa/Shuwa; variété locale à confirmer", "ttsLang": "shu", "ttsMode": "system-exact", "translationStatus": "pending", "allowAI": False, "ttsResourceInfo": "OmniVoice répertorie shu (2,29 h); code Apache 2.0, poids CC BY-NC. Modèle non intégré."},
    "masa": {"label": "Masa (Masana)", "htmlLang": "mcn", "description": "Masana/Masa (ISO 639-3 mcn)", "ttsLang": "mcn", "ttsMode": "system-exact", "translationStatus": "pending", "allowAI": False, "ttsResourceInfo": "OmniVoice répertorie mcn (10,09 h); poids CC BY-NC. Modèle non intégré; variété locale à confirmer."},
    "bafia": {"label": "Bafia", "htmlLang": "ksf", "description": "Bafia (ISO 639-3 ksf)", "ttsLang": "ksf", "ttsMode": "system-exact", "translationStatus": "pending", "allowAI": False, "ttsResourceInfo": "OmniVoice répertorie ksf (16,43 h); poids CC BY-NC. Modèle non intégré et qualité locale non évaluée."},
    "toupouri": {"label": "Tupuri / Toupouri", "htmlLang": "tui", "description": "Tupuri/Toupouri (ISO 639-3 tui)", "ttsLang": "tui", "ttsMode": "system-exact", "translationStatus": "pending", "allowAI": False, "ttsResourceInfo": "OmniVoice répertorie tui (9,26 h); poids CC BY-NC. Modèle non intégré; autre jeu vocal repéré, droits à vérifier."},
    "basaa": {"label": "Basaa", "htmlLang": "bas", "description": "Basaa du Cameroun (ISO 639-3 bas)", "ttsLang": "bas", "ttsMode": "system-exact", "translationStatus": "pending", "allowAI": False, "ttsResourceInfo": "OmniVoice répertorie bas (10,66 h); poids CC BY-NC, non intégré. MMS signale de l'ASR mais pas de TTS pour bas."},
    "duala": {"label": "Duala", "htmlLang": "dua", "description": "Duala/Douala du Cameroun (ISO 639-3 dua)", "ttsLang": "dua", "ttsMode": "system-exact", "translationStatus": "pending", "allowAI": False, "ttsResourceInfo": "OmniVoice répertorie dua (12,13 h); poids CC BY-NC, non intégré. Un corpus distinct d'environ 4 h 30 reste à vérifier."},
    "yemba": {"label": "Yemba", "htmlLang": "ybb", "description": "Yemba (langue précise; ISO 639-3 ybb)", "ttsLang": "ybb", "ttsMode": "system-exact", "translationStatus": "pending", "allowAI": False, "ttsResourceInfo": "Modèle MMS TTS public pour ybb, licence CC BY-NC 4.0; non intégré à l'extension."},
    "mafa": {"label": "Mafa", "htmlLang": "maf", "description": "Mafa (ISO 639-3 maf)", "ttsLang": "maf", "ttsMode": "system-exact", "translationStatus": "pending", "allowAI": False, "ttsResourceInfo": "OmniVoice répertorie maf (9,97 h); poids CC BY-NC, non intégré. Les enregistrements externes doivent être vérifiés avant usage."},
}
DEFAULT_META = {"label": "", "htmlLang": "", "description": "", "ttsLang": "", "ttsMode": "none", "translationStatus": "pending", "allowAI": False, "ttsResourceInfo": "Aucune voix TTS vérifiée ou intégrée."}
EMPTY = {"", "A VALIDER", "NE PAS TRADUIRE"}


def norm(s: str) -> str:
    """Doit rester identique à norm() dans content.js."""
    s = unicodedata.normalize("NFC", s)
    s = s.replace("’", "'").replace("‘", "'")
    s = re.sub(r"[\s  ]+", " ", s).strip()
    return s.lower()


def main() -> int:
    with CSV_PATH.open(encoding="utf-8-sig", newline="") as f:
        rows = [r for r in csv.reader(f, delimiter=";") if r and not r[0].startswith("#")]

    header = rows[0]
    col = {name: i for i, name in enumerate(header)}
    start, end = col["anglais"] + 1, col["remarque"]
    lang_cols = [c for c in header[start:end] if not c.startswith("fiabilite_")]
    languages = []
    for c in lang_cols:
        meta = KNOWN.get(c, {**DEFAULT_META, "label": c.replace("_", " ").title(), "description": c.replace("_", " ")})
        languages.append({"code": c, **meta})

    entries: dict[str, dict] = {}
    entry_counts = {c: set() for c in lang_cols}
    glossary: list[dict] = []
    ui: dict[str, dict] = {}  # textes propres à l'extension (U…)
    items: list[dict] = []  # pour l'outil d'enregistrement
    conflicts = 0
    for r in rows[1:]:
        rid = r[col["id"]].strip()
        if not rid:
            continue
        if rid.startswith(("X", "D")):  # protégés / dates : jamais traduits
            continue
        tr = {c: r[col[c]] for c in lang_cols if r[col[c]].strip() not in EMPTY}
        for code in tr:
            entry_counts[code].add(rid)
        if rid.startswith("U"):
            ui[rid] = {"fr": r[col["francais"]], "en": r[col["anglais"]], **tr}
            items.append({"id": rid, "fr": r[col["francais"]], **tr})
            continue
        if rid.startswith("V"):
            glossary.append({"fr": r[col["francais"]], "en": r[col["anglais"]], **tr})
            continue
        items.append({"id": rid, "fr": r[col["francais"]], **tr})
        value = {"id": rid, **tr}
        for src in (r[col["francais"]], r[col["anglais"]]):
            key = norm(src)
            old = entries.get(key)
            if old and {k: v for k, v in old.items() if k != "id"} != tr:
                print(f"CONFLIT {key!r}: {old['id']} vs {rid}", file=sys.stderr)
                conflicts += 1
                continue
            entries.setdefault(key, value)

    for language in languages:
        language["entryCount"] = len(entry_counts[language["code"]])
        suffix = "brouillon à valider" if language["translationStatus"] == "draft" else "à traduire"
        language["selectorLabel"] = f"{language['label']} — {suffix}"

    # Enregistrements : extension/audio/<langue>/<id>.<ext>
    audio: dict[str, dict] = {}
    for c in lang_cols:
        d = AUDIO_DIR / c
        if d.is_dir():
            files = {f.stem: f.name for f in sorted(d.iterdir()) if f.suffix.lower() in AUDIO_EXT}
            if files:
                audio[c] = files

    payload = {"languages": languages, "entries": entries, "glossary": glossary, "ui": ui, "audio": audio}
    OUT_PATH.write_text(
        "// Fichier généré par tools/build_dictionary.py — ne pas modifier à la main.\n"
        "globalThis.SAFINUM_DICT = "
        + json.dumps(payload, ensure_ascii=False, indent=1)
        + ";\n",
        encoding="utf-8",
    )
    ITEMS_PATH.write_text(
        "// Fichier généré par tools/build_dictionary.py — ne pas modifier à la main.\n"
        "globalThis.SAFINUM_ITEMS = " + json.dumps(items, ensure_ascii=False, indent=1) + ";\n",
        encoding="utf-8",
    )
    names = ", ".join(l["label"] for l in languages)
    print(f"Langues : {names} — {len(entries)} entrées, {len(glossary)} termes de glossaire, {len(ui)} textes d'extension")
    for l in languages:
        print(f"  {l['label']} : {len(audio.get(l['code'], {}))} enregistrement(s)")
    return 1 if conflicts else 0


if __name__ == "__main__":
    sys.exit(main())
