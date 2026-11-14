# Bank — application mobile et API SAFINUM

Ce dépôt sépare l’application Flutter issue de [`yohanangulo/spending-pal`](https://github.com/yohanangulo/spending-pal) et le prototype API SAFINUM. Le code amont a été réutilisé avec l’autorisation confirmée pour ce projet; crédits et README d’origine restent dans `app/README.md`.

> **Prototype de démonstration uniquement.** Les comptes, noms, soldes et mouvements sont fictifs. Aucune banque ni aucun opérateur mobile-money n’est connecté. N’utilisez pas de données financières réelles.

## Structure

```text
app/    Application Flutter basée sur SpendingPal
api/    API FastAPI SAFINUM, interface web, USSD simulé et collecte
browser-extension/ Extension navigateur SAFINUM, autonome et documentée
```

## Extension navigateur

Le sous-projet `browser-extension/` est séparé de `app/` et `api/`; il ne modifie ni l’authentification Firebase de l’application mobile ni la configuration Appwrite de l’API. Il expose 13 choix de langue dans l’extension; seules les trois langues historiques ont des traductions, encore à valider. Les dix autres restent en attente de traductions et d’une revue par des locuteurs locaux. La synthèse refuse les voix françaises/anglaises de remplacement; aucun échantillon de phrase n’a été généré sans validation locale. Voir `browser-extension/README.md` et `browser-extension/docs/AUDIO_ET_LIMITES.md` pour les ressources, licences et résultats de test.

## API SAFINUM

L’API propose une démonstration bancaire FR/EN, un menu USSD simulé et la collecte de traductions et d’audios pour dix langues camerounaises. Les propositions restent privées et `pending_review`; aucune traduction ou voix locale n’est diffusée avant approbation humaine. Les tests protègent notamment les montants et devises.

### Démarrer en local

```bash
cd api
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

Ouvrir `http://127.0.0.1:8000/`; la documentation de l’API est à `/docs`. Sans `APPWRITE_API_KEY`, l’API utilise SQLite et des fichiers locaux ignorés par Git, ce qui permet le développement et les tests hors ligne.

### Appwrite auto-hébergé

Le endpoint prévu est `https://vps.kernelforge.codes/v1`, le projet Appwrite est `bank` et la base de données dédiée à SAFINUM est `safinum`. L’API serveur comporte un adaptateur Appwrite et un script idempotent pour créer des ressources privées : collections `translation_suggestions` et `audio_contributions`, bucket `safinum-audio`.

**État de la configuration distante : incomplète.** La base `safinum` existe, mais la clé actuellement référencée n’autorise pas la lecture ni l’écriture des collections (`collections.read` et `collections.write` manquants). Aucune collection ni aucun bucket SAFINUM n’a été créé. Le code et les tests locaux de l’adaptateur sont prêts; il faudra fournir une clé serveur projet avec les scopes `databases.read/write`, `collections.read/write`, `attributes.read/write`, `indexes.read/write`, `documents.read/write`, `buckets.read/write` et `files.read/write/delete`, puis relancer l’installation.

Après ajout des scopes :

1. Copier `api/.env.example` vers `api/.env` et remplir la clé **dans ce fichier local non versionné**, ou l’injecter dans l’environnement du serveur.
2. Depuis `api/`, lancer `set -a; . ./.env; set +a; python3 scripts/setup_appwrite.py`.
3. Démarrer l’API avec les mêmes variables. Le script configure les collections et le bucket en accès privé; la clé API est utilisée uniquement côté serveur.

**Sécurité :** ne jamais copier la clé dans `app/`, une ressource statique, un fichier suivi par Git, une URL ou une réponse HTTP. L’application Flutter ne reçoit que des paramètres publics. Les audios et les documents sont créés sans permissions publiques.

### Tests de l’API

Les tests locaux n’utilisent pas le serveur Appwrite :

```bash
cd api
python3 -m unittest tests.test_appwrite_store -v
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
# Dans un autre terminal :
python3 tests/smoke_test.py http://127.0.0.1:8000
```

Le smoke test utilise SQLite, crée puis supprime ses enregistrements factices; ne pas le lancer contre une base Appwrite de production.

### Limites de l’application Flutter

Le code Flutter conserve les dépendances Firebase présentes dans le dépôt amont. **La migration de son authentification et de ses données Firebase vers Appwrite n’est pas incluse dans l’intégration SAFINUM côté API.** Aucun SDK ou secret Appwrite n’est embarqué dans le client. Une migration complète de l’application nécessitera une décision explicite sur les fonctions Firebase à remplacer et une adaptation séparée.

## Ressources des dix langues

La recherche détaillée, les liens vers les sources primaires, les licences et les limites de couverture sont dans [`api/docs/LANGUES_ET_SOURCES.md`](api/docs/LANGUES_ET_SOURCES.md). Conclusion principale : les ressources trouvées sont fragmentaires; aucune ne constitue une traduction bancaire complète, sûre et déjà approuvée. Vérifier les licences, les variétés et les droits avant d’intégrer un corpus externe. Le prototype n’importe aucun corpus externe.

## Application Flutter

Voir `app/README.md` pour les instructions et la configuration héritées du projet source. Le SDK Flutter doit être installé pour exécuter l’application.
