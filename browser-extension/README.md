# Extension Safinum — SAFINUM Innovate Challenge 2026

Extension de navigateur qui prépare un sélecteur de **13 langues** (les trois langues existantes et dix ajoutées), sans modifier le code source du service ciblé. Les dix nouvelles langues sont visibles mais leurs traductions restent vides jusqu'à validation locale.

## Contenu du dépôt

| Fichier / dossier | Description |
|---|---|
| `PRESELECTION EPREUVE SAFINUM INNOVATE CHALLENGE Fr.pdf` | Énoncé officiel de l'épreuve de présélection |
| `liste_mots_a_traduire.csv` | Textes de l'environnement de test, en FR / EN et 13 colonnes de langues; les dix nouvelles colonnes restent vides et en attente de validation |
| `extension/` | Extension Chrome « Safinum Lingua » (Manifest V3) : dictionnaire généré depuis le CSV, protection des valeurs financières, lecture vocale, traduction IA facultative des messages inédits |
| `spending-pal/` | Copie du dépôt Flutter [`yohanangulo/spending-pal`](https://github.com/yohanangulo/spending-pal), intégrée comme sous-dossier ; provenance et commit source dans `spending-pal/SOURCE_REPO.md` |
| `docs/AUDIO_ET_LIMITES.md` | État des phrases audio, modèles, variétés et licences vérifiés |
| `audio_samples/README.md` | Explique pourquoi aucun échantillon synthétique non validé n'est inclus |
| `enregistrements_a_verifier/` | Dossier de recherche local, exclu du ZIP et de la publication tant que les variétés et droits n'ont pas été vérifiés |
| `capture/` | Captures de travail locales, exclues du ZIP et de la publication |
| `logo safinum.png`, `logo safinum blanc.png` | Logos de l'événement |

## L'épreuve en bref

Prototype fonctionnel qui doit :
1. traduire les textes, instructions et messages de l'interface ;
2. accompagner un parcours (solde, frais, transfert) ;
3. **préserver exactement** montants, frais, bénéficiaires, conditions et alertes de sécurité ;
4. fonctionner sans modifier le code du service cible ;
5. traduire un **message inédit** injecté par le jury pendant la démo.

Livrables : description, prototype, vidéo ≤ 3 min, note technique (architecture, intégration, dépendances, limites), langues prises en charge + méthode de validation linguistique.

## Environnement de test : https://safinum.cm/hackathon-test

Application Vue.js « Safinum Pay », bascule FR/EN, 5 étapes :

| Étape | Contenu |
|---|---|
| 1. Solde | 250 000 FCFA, compte `CM 001 2345 6789 01`, 4 transactions récentes |
| 2. Frais | Compte Safinum (gratuit), Mobile Money (1,5 %, min 100, max 2 500), Autre banque (2 %, min 200, max 5 000) |
| 3. Bénéficiaire | Jean-Paul Mbarga, +237 6 99 12 34 56, motif, note, case « J'ai vérifié… » |
| 4. Récapitulatif | Montant, frais, total, bénéficiaire, téléphone, référence `SAF-2026-XXXXXX` |
| 5. Reçu | « Transfert effectué », mêmes valeurs |

Codes d'erreur : `AMOUNT_001`, `AMOUNT_002`, `BENEFICIARY_001`, `SECURITY_001`, `SECURITY_002`, `NETWORK_001`, `CONFIRM_001`.

### Comment le jury vérifie (panneau caché `?jury=1`)

- **Injection de contenu inédit** : encadré « Message important » ajouté après chargement (texte en FR ou EN).
- **Déclenchement d'erreurs / alertes** à la demande.
- **Couverture de traduction** : capture des textes visibles sans extension, puis % de textes modifiés avec l'extension.
- **Intégrité** : relit le `textContent` des éléments de valeur (solde, frais, total, montant, bénéficiaire, téléphone, référence) et la `value` des champs. Normalisation : suppression de « FCFA », espaces, virgules, points, apostrophes, puis minuscules. Le moindre écart → **« Compromis »**.

### Contraintes pour l'extension

- Ne rien ajouter ni modifier dans les éléments qui affichent une valeur (`25 000 FCFA` reste `25 000 FCFA`).
- Ne jamais toucher au contenu des champs de saisie (ex. « Paiement de services »).
- Traduire le texte affiché des `<option>`, jamais leur `value`.
- `MutationObserver` obligatoire : Vue réécrit les textes à chaque étape / changement de langue.
- Gérer le français **et** l'anglais comme langues sources.
- Ne pas collecter, stocker ou transmettre les données affichées : masquer montants, noms, numéros et références avant tout appel à un service externe.

### Barème du site (100 pts)

| Critère | Points |
|---|---|
| Fonctionnement du prototype | 25 |
| Fidélité des traductions | 20 |
| Sécurité et intégrité financière | 20 |
| Intégration aux services existants | 15 |
| Accessibilité et expérience utilisateur | 10 |
| Innovation et pertinence | 10 |

Qualité linguistique vérifiée à part. Défauts majeurs : contresens sur une action (envoyer / confirmer / annuler), montant modifié, alerte affaiblie, traduction d'un nom / numéro / référence, texte tronqué bloquant.

## Les 13 langues et l'état réel des ressources

Les choix sont **pidgin camerounais, Fulfulde, Ewondo, Makaa, Kanuri, Arabe Choa/Shuwa, Masa, Bafia, Tupuri, Basaa, Duala, Yemba et Mafa**. **Bekwil est écarté.** Les trois premières ont des traductions dans le CSV, mais ce sont des brouillons. Les dix suivantes ont des colonnes vides, sont marquées « traductions à faire » et restent inchangées à l'écran; l'IA est désactivée pour elles. Les montants, devises, numéros, références et variables financières ne sont pas générés ni altérés.

| Langue et code ISO 639-3 | Traductions dans l'extension | Ressources vocales publiques et limites |
|---|---|---|
| Pidgin camerounais (`wes`) | Brouillons, à valider localement | OmniVoice répertorie `wes` et environ 10,06 h de données; poids CC BY-NC. Modèle non intégré, qualité locale non validée. Le repli anglais a été retiré; aucune voix Pidgin native n'est intégrée. |
| Fulfulde d'Adamawa (`fub`) | Brouillons, à valider localement | OmniVoice répertorie Adamawa (`fub`, environ 13,12 h); poids CC BY-NC, modèle non intégré et qualité non validée. Deux enregistrements humains de mots existent; le repli français a été retiré. Le modèle MMS « Fulah » (`ful`) est plus large, pas une preuve pour `fub`. |
| Ewondo (`ewo`) | Brouillons, à valider localement | OmniVoice répertorie `ewo` (environ 12,71 h); poids CC BY-NC, modèle non intégré et qualité non validée. Un enregistrement humain de mot existe; le repli français a été retiré. |
| Makaa du Cameroun (`mcp`) | Aucune; traduction à faire | Le modèle MMS TTS `mcp` existe, sous CC BY-NC 4.0, mais n'est pas intégré. Il s'agit de Makaa camerounais, pas de Maca/Maká paraguayen (`mca`). [Modèle](https://huggingface.co/facebook/mms-tts-mcp) · [Code ISO](https://iso639-3.sil.org/code/mcp). |
| Kanuri (`kau`) | Aucune; traduction à faire | TWB Voice est sous CC BY-NC et utilise une voix féminine fixe; ses données décrites sont du Kanuri central (`knc`) du Nigeria, pas une variété camerounaise démontrée. Évaluation publiée : 2,8/5 en prononciation et 2,76/5 en naturel. Non intégré ni utilisé. [Fiche modèle](https://huggingface.co/CLEAR-Global/TWB-Voice-Kanuri-TTS-1.0). |
| Arabe Choa/Shuwa (`shu`) | Aucune; traduction à faire | OmniVoice répertorie le Chadian Arabic (`shu`, environ 2,29 h); poids CC BY-NC et code Apache 2.0, modèle non intégré. Le nom de la variété locale doit être vérifié par des locuteurs. [Langues OmniVoice](https://github.com/k2-fsa/OmniVoice/blob/master/docs/languages.md) · [Licence/modèle](https://huggingface.co/k2-fsa/OmniVoice). |
| Masa/Masana (`mcn`) | Aucune; traduction à faire | OmniVoice répertorie `mcn` (environ 10,09 h); poids CC BY-NC, non intégrés. [Langues OmniVoice](https://github.com/k2-fsa/OmniVoice/blob/master/docs/languages.md). |
| Bafia (`ksf`) | Aucune; traduction à faire | OmniVoice répertorie `ksf` (environ 16,43 h); poids CC BY-NC, non intégrés. La durée de données indiquée n'est pas un test de qualité de la voix. [Langues OmniVoice](https://github.com/k2-fsa/OmniVoice/blob/master/docs/languages.md). |
| Tupuri/Toupouri (`tui`) | Aucune; traduction à faire | OmniVoice répertorie `tui` (environ 9,26 h); poids CC BY-NC, non intégrés. Le jeu Common Voice Tupuri est une ressource distincte, pas un modèle; vérifier ses conditions avant tout usage. [Langues OmniVoice](https://github.com/k2-fsa/OmniVoice/blob/master/docs/languages.md) · [Jeu Mozilla](https://mozilladatacollective.com/datasets/cmu61uab500mnnq07gvl1kufs). |
| Basaa (`bas`) | Aucune; traduction à faire | OmniVoice répertorie le Basa du Cameroun (`bas`, environ 10,66 h); poids CC BY-NC, non intégrés. MMS répertorie de l'ASR mais pas de TTS pour `bas`. [Langues OmniVoice](https://github.com/k2-fsa/OmniVoice/blob/master/docs/languages.md) · [Couverture MMS](https://dl.fbaipublicfiles.com/mms/misc/language_coverage_mms.html). |
| Duala (`dua`) | Aucune; traduction à faire | OmniVoice répertorie `dua` (environ 12,13 h); poids CC BY-NC, non intégrés. Un corpus distinct d'environ 4 h 30 à une voix n'est pas un modèle prêt à l'emploi; ses droits doivent être vérifiés. [Langues OmniVoice](https://github.com/k2-fsa/OmniVoice/blob/master/docs/languages.md) · [Corpus](https://mozilladatacollective.com/datasets/cmpmpf0jw021bnu0743hu7763). |
| Yemba (`ybb`) | Aucune; traduction à faire | Le modèle MMS TTS `ybb` existe sous CC BY-NC 4.0, mais n'est pas intégré. Yemba est une langue précise choisie à la place du groupe Bamiléké. [Modèle](https://huggingface.co/facebook/mms-tts-ybb) · [Code ISO](https://iso639-3.sil.org/code/ybb). |
| Mafa (`maf`) | Aucune; traduction à faire | OmniVoice répertorie `maf` (environ 9,97 h); poids CC BY-NC, non intégrés. Des enregistrements existent ailleurs, mais leurs droits pour entraîner ou diffuser une voix doivent être vérifiés. [Langues OmniVoice](https://github.com/k2-fsa/OmniVoice/blob/master/docs/languages.md). |

Les heures indiquées sont des volumes d'entraînement décrits par OmniVoice, **pas** des corpus audio libres à extraire, une mesure de qualité, ni une voix disponible dans cette extension. Le code OmniVoice est sous Apache 2.0, mais ses poids sont sous CC BY-NC. Les modèles MMS cités sont aussi sous CC BY-NC 4.0. Aucun n'a été téléchargé, testé ou intégré; aucune voix réelle n'a été réutilisée ni clonée.

### Phrase témoin et échantillons audio

Pour la phrase **« Bienvenue sur SAFINUM. »**, aucune source consultée ne permet de retenir une formulation complète et naturelle dans les treize variétés, et aucun locuteur local ne l'a approuvée. **Aucun échantillon synthétique n'a donc été généré**; les choix de langue ne doivent pas être confondus avec une disponibilité audio. Les sons existants dans `extension/audio/` sont des enregistrements humains de mots isolés en Fulfulde et Ewondo, pas des phrases synthétiques. La synthèse exige une traduction validée, une voix de la bonne variété et des droits compatibles avec l'usage prévu. Détails et sources : [`docs/AUDIO_ET_LIMITES.md`](docs/AUDIO_ET_LIMITES.md).

## Lecture vocale

Survoler un texte déjà traduit fait apparaître un bouton 🔊 (ou **Alt+L** sur l'élément qui a le focus, **Échap** pour arrêter); le texte lu est surligné. Un enregistrement de locuteur natif est joué s'il existe (`extension/audio/<langue>/<id>.<ext>`). Sinon, seule une voix système locale dont le code correspond exactement à la langue choisie est acceptée. **Aucune voix française ou anglaise ne remplace une langue locale**; si aucun enregistrement ou aucune voix exacte n'existe, la lecture est signalée comme indisponible. Les modèles mentionnés dans le tableau ne comptent pas comme intégrés.

Les options permettent de régler le débit et signalent si une voix locale de code exact ou un enregistrement natif est disponible. Les voix « en ligne » restent exclues : aucun texte lu n'est envoyé à un service externe. Le choix de langue indique si les traductions sont des brouillons ou encore absentes. La traduction IA, lorsqu'elle est activée pour l'une des trois langues historiques, reste également non validée; elle est désactivée pour les dix langues sans données.

Enregistrements actuellement intégrés : Fulfulde S02 (Sannu), F12 (Meere); Ewondo F12 (Zezé) — crédits et licences dans `extension/audio/CREDITS.md`. Pour en ajouter : fenêtre de l'extension → **🎙 Enregistrer les mots**. La page ne propose que les textes déjà présents dans le CSV; les dix langues sans traductions indiquent pourquoi aucune prise n'est encore disponible. Les fichiers restent locaux jusqu'à ce qu'un propriétaire les ajoute au dépôt.

## Installer l'extension

Le même dossier `extension/` est prévu pour les navigateurs ci-dessous. Les instructions indiquent comment le charger localement; le parcours complet du site de démonstration n'a pas été revalidé pour cette mise à jour.

| Navigateur | Installation |
|---|---|
| Google Chrome | `chrome://extensions` → **Mode développeur** → **Charger l'extension non empaquetée** → dossier `extension/` |
| Microsoft Edge | `edge://extensions` → **Mode développeur** → **Charger l'extension décompressée** → dossier `extension/` |
| Brave | `brave://extensions` → **Mode développeur** → **Charger l'extension non empaquetée** → dossier `extension/` |
| Opera | `opera://extensions` → **Mode développeur** → **Charger l'extension non empaquetée** → dossier `extension/` |
| Mozilla Firefox | `about:debugging#/runtime/this-firefox` → **Charger un module complémentaire temporaire** → fichier `extension/manifest.json` (retiré à la fermeture de Firefox) |

Puis ouvrir https://safinum.cm/hackathon-test : le sélecteur 🌍 apparaît en bas à gauche.

### Contrôles exécutés pour cette mise à jour

La génération du dictionnaire, le test `python3 extension/tools/test_language_matrix.py`, la syntaxe JavaScript des scripts vérifiés, la compilation syntaxique Python et `git diff --check` ont réussi. Le test automatique vérifie les 13 choix, les dix colonnes vides, l'absence de traduction IA dans ces langues, le statut brouillon des trois langues existantes, l'exclusion des lignes financières/date protégées et l'absence de voix de remplacement. Un smoke test Chromium sur une fixture locale a aussi confirmé 13 options, la sélection de Makaa, le maintien du texte source et l'intégrité du montant et du champ de saisie. Le parcours complet du site réel n'a pas été vérifié; les tests Flutter n'ont pas été exécutés et aucun fichier Flutter n'a été modifié.

- **Voix :** seuls les enregistrements natifs ou une voix système locale de code exact sont utilisés. Firefox utilise directement les voix du système, sans option. Opera sous Linux n'a pas de synthèse vocale : seuls les enregistrements de locuteurs natifs y sont lus.
- **Téléphone :** Chrome pour Android n'accepte pas les extensions. Firefox pour Android les accepte, mais l'extension n'y a pas été testée.

Après une modification du CSV : `python3 extension/tools/build_dictionary.py`, puis recharger l'extension. Chaque colonne de langue du CSV devient une langue de l'extension.
