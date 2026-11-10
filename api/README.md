# SAFINUM — API linguistique et banque simulée

Prototype de démonstration isolé : interface bancaire fictive FR/EN, API, parcours USSD simulé et collecte de propositions de traduction et d’audios pour dix langues camerounaises.

> Les noms, soldes, opérations et transferts sont fictifs. Aucune banque ni aucun service mobile-money n’est connecté. Ne pas envoyer de données financières réelles.

## Démarrer en local

Depuis la racine du dépôt :

```bash
cd api
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

Ouvrir `http://127.0.0.1:8000/`; la documentation OpenAPI est à `/docs`. Sans `APPWRITE_API_KEY`, les propositions et fichiers restent dans SQLite et dans le stockage local sous `data/`. Ces fichiers sont ignorés par Git.

## Fonctionnalités

- Démonstration bancaire FR/EN avec solde et mouvements fictifs; aucun argent ne circule.
- Catalogue explicite de phrases FR/EN; dix langues en collecte, non déclarées traduites par défaut.
- Traduction par phrase exacte : une proposition locale reste en attente; le texte source est renvoyé tant qu’une traduction n’a pas été vérifiée et approuvée.
- Validation des variables, montants et devises avant réponse : les valeurs financières doivent rester intactes.
- Collecte de texte et d’audio WebM/OGG/WAV/MP3/MP4 (maximum 12 Mo) avec consentement déclaré.
- Les audios restent privés et en attente; l’API ne sert que les enregistrements approuvés. Pas de transcription automatique ni de synthèse vocale intégrée.
- USSD simulé en français et en anglais; si une traduction locale n’est pas approuvée, le service indique le repli en français.

## Routes principales

| Méthode | Route | Usage |
|---|---|---|
| `GET` | `/health` | Vérifier l’API |
| `GET` | `/api/v1/languages` | Lister les langues pilotes et celles de l’interface |
| `GET` | `/api/v1/catalog/fr` ou `/api/v1/catalog/en` | Charger le catalogue de démonstration |
| `GET` | `/api/v1/catalog/{locale}?source_locale=fr` | Lire les phrases locales approuvées et les clés manquantes |
| `POST` | `/api/v1/translate` | Traduire une phrase exacte ou conserver le texte source si la phrase n’est pas approuvée |
| `POST` | `/api/v1/contributions/translations` | Proposer une phrase avec variété, rôle du locuteur et consentement |
| `POST` | `/api/v1/contributions/audio?language_code=ewo&phrase_key=balance_label&speaker_role=native&consent=true` | Envoyer un audio de test avec consentement |
| `GET` | `/api/v1/pronunciation/{language_code}/{phrase_key}` | Lire un enregistrement après approbation humaine |
| `GET` | `/api/v1/metrics` | Compter les propositions et validations |
| `POST` | `/api/v1/ussd` | Simuler le parcours USSD FR/EN ou un repli local signalé |

Exemple de traduction avec montant dynamique :

```json
{
  "source_locale": "fr",
  "target_locale": "en",
  "phrase_key": "transfer_confirmation",
  "source_text": "Confirmer l’envoi de 15 000 XAF à Aline ?",
  "variables": {"amount": "15 000 XAF", "recipient": "Aline"}
}
```

La réponse conserve `15 000 XAF` et le nom transmis; toutes les variables attendues dans la phrase doivent être fournies.

## Appwrite auto-hébergé

Le serveur Appwrite configuré est `https://vps.kernelforge.codes/v1`, projet `bank`; les données SAFINUM doivent aller dans la base `safinum`. L’adaptateur utilise la clé API **uniquement dans le processus serveur** et envoie l’en-tête `X-Appwrite-Key`. Le client Flutter et les fichiers statiques ne reçoivent jamais cette clé.

Le script `scripts/setup_appwrite.py` configure deux collections (`translation_suggestions`, `audio_contributions`) et le bucket `safinum-audio`. Documents, collections et bucket sont privés par défaut; aucune permission publique n’est accordée. L’installation distante reste bloquée : la clé actuellement référencée est dépourvue de `collections.read` et `collections.write`, et aucune collection ni aucun bucket n’a été créé. Il faut une clé de serveur avec les scopes suivants : `databases.read/write`, `collections.read/write`, `attributes.read/write`, `indexes.read/write`, `documents.read/write`, `buckets.read/write` et `files.read/write/delete`.

Quand les scopes sont disponibles :

```bash
cp .env.example .env
# Remplir .env localement; ne jamais versionner ou partager ce fichier.
set -a
. ./.env
set +a
python3 scripts/setup_appwrite.py
```

Les variables configurables sont décrites dans `.env.example`. Sans clé, l’API continue de fonctionner en mode local SQLite. Pour une configuration de production, injecter le secret dans l’environnement du serveur plutôt que de conserver un `.env` sur une machine exposée.

## Revue humaine

Aucune route publique d’administration ou d’approbation n’est exposée. Chaque traduction et audio nouvellement soumis reste `pending_review`. Une personne habilitée doit examiner langue/variété, sens, chiffres et devises, prononciation, qualité et consentement avant de passer une entrée à `approved` dans l’environnement d’administration sécurisé. Les éléments non approuvés ne sont pas renvoyés comme traduction ni servis comme audio.

## Langues, ressources et licences

Les dix langues pilotes sont Ewondo (`ewo`), Fulfulde Adamawa (`fub`), Bamoun (`bax`), Bulu (`bum`), Basaa (`bas`), Éton (`eto`), Tupuri (`tui`), Bafut (`bfd`), Ghomálá’ (`bbj`) et Medumba (`byv`). La documentation [`docs/LANGUES_ET_SOURCES.md`](docs/LANGUES_ET_SOURCES.md) recense les sources, licences et lacunes. Aucune source consultée ne fournit un corpus bancaire complet ni des traductions financières déjà approuvées. Aucun corpus externe n’est importé dans ce prototype.

## Tests

En mode local, depuis `api/` :

```bash
python3 -m py_compile backend/main.py backend/appwrite_store.py scripts/setup_appwrite.py
python3 -m unittest tests.test_appwrite_store -v
```

Démarrer ensuite l’API et exécuter dans un autre terminal :

```bash
python3 tests/smoke_test.py http://127.0.0.1:8000
```

Le smoke test couvre les dix langues, FR/EN, les variables financières, le repli avant validation, l’activation après approbation de test, les contrôles de source/devise, l’audio en attente et l’USSD. Il utilise SQLite et supprime ses données factices à la fin; **ne pas le lancer contre Appwrite en production**. Les tests `test_appwrite_store` simulent Appwrite sur localhost et n’utilisent aucune clé réelle.

## Sécurité et limites

- Pas d’authentification ni de rôles d’administration dans la démo; ne pas exposer directement l’API à Internet sans ajouter contrôle d’accès et protections adaptées.
- La base SQLite et les audios locaux sont des données potentiellement sensibles; éviter les données personnelles, contrôler l’accès et supprimer un audio si le consentement est retiré.
- Ne jamais enregistrer de compte bancaire, téléphone réel, PIN, OTP, solde ou instruction de paiement dans les contributions.
- Une ressource publique n’est pas automatiquement autorisée à l’usage commercial, à l’entraînement ou à la redistribution. Vérifier les licences et droits séparément pour chaque fichier.
- Avant un pilote financier, faire relire toutes les chaînes à risque par des locuteurs compétents et les responsables conformité/juridiques; tester la compréhension, l’accessibilité et les erreurs.
