# Audio SAFINUM : disponibilité réelle et limites

## Décision pour la phrase témoin

La phrase demandée pour les échantillons est **« Bienvenue sur SAFINUM. »**. Les sources consultées n’ont pas permis d’établir une formulation complète et naturelle dans l’une des treize variétés choisies, et aucun locuteur local n’a validé de traduction. Il n’y a donc **aucune traduction audio prête à synthétiser** et aucun fichier de synthèse n’a été fabriqué. Ce constat concerne les sources vérifiées ici; il ne prouve pas qu’une telle phrase n’existe pas dans ces langues.

Les mots isolés repérés ne suffisent pas à construire la phrase. Par exemple, le cours de pidgin camerounais répertorie « Welkom » comme salutation d’arrivée, le guide d’arabe tchadien donne « Ahlan wa sahlan » pour accueillir quelqu’un dans un lieu, et une liste Yemba présente une formule de bienvenue générale. Ces indices ne vérifient ni « sur SAFINUM », ni la naturalité de la phrase complète, ni l’orthographe locale. Ils ne sont donc pas utilisés comme traductions.

Le moteur vocal intégré à l’extension n’a pas de voix de bibliothèque correspondant exactement aux treize codes sélectionnés. Le code a été réglé pour refuser les voix françaises ou anglaises de remplacement : il ne lit qu’un enregistrement natif déjà associé au texte, ou une voix système locale dont le code correspond exactement à la langue. À défaut, l’interface signale l’indisponibilité au lieu de simuler une prononciation.

## Modèles repérés — aucun n’est intégré ni validé ici

| Langue et code | Ressource vocale vérifiable | Limites importantes |
|---|---|---|
| Pidgin camerounais (`wes`) | [OmniVoice](https://github.com/k2-fsa/OmniVoice/blob/master/docs/languages.md) répertorie Cameroon Pidgin (`wes`, 10,06 h de données d’entraînement). | Les heures ne mesurent pas la qualité. Le code du projet est Apache-2.0, mais les poids préentraînés sont CC-BY-NC : usage non commercial seulement. Le modèle n’est pas intégré et aucun rendu natif n’a été vérifié. |
| Fulfulde d’Adamawa (`fub`) | [OmniVoice](https://github.com/k2-fsa/OmniVoice/blob/master/docs/languages.md) répertorie Adamawa Fulfulde (`fub`, 13,12 h). | Poids CC-BY-NC et qualité de prononciation non validée. Le modèle MMS `ful` concerne une catégorie plus large, pas une validation de la variété `fub`. Aucun modèle n’est intégré. |
| Ewondo (`ewo`) | [OmniVoice](https://github.com/k2-fsa/OmniVoice/blob/master/docs/languages.md) répertorie `ewo` (12,71 h). | Poids CC-BY-NC et qualité non validée. Le [catalogue MMS](https://dl.fbaipublicfiles.com/mms/misc/language_coverage_mms.html) ne marque pas Ewondo comme TTS. Aucun modèle n’est intégré. |
| Makaa (`mcp`) | [MMS TTS Makaa](https://huggingface.co/facebook/mms-tts-mcp), checkpoint VITS pour `mcp`. | Licence CC-BY-NC 4.0; inférence locale à installer; non testé ni intégré. Il s’agit du Makaa camerounais, distinct du Maca/Maká paraguayen (`mca`). |
| Kanuri (`kau`) | [TWB Voice Kanuri](https://huggingface.co/CLEAR-Global/TWB-Voice-Kanuri-TTS-1.0), checkpoint téléchargeable. | Bien que la fiche indique Kanuri (`kau`), les données décrites correspondent au Kanuri central (`knc`) du Nigeria, pas à une variété camerounaise démontrée. Le checkpoint incorpore une voix féminine unique et est sous CC-BY-NC; l’évaluation publiée est de 2,8/5 en prononciation et 2,76/5 en naturel. Il n’a pas été utilisé. |
| Arabe Choa/Shuwa (`shu`) | [OmniVoice](https://github.com/k2-fsa/OmniVoice/blob/master/docs/languages.md) répertorie Chadian Arabic (`shu`, 2,29 h). | Couverture d’entraînement, pas validation d’une voix Shuwa camerounaise. Poids CC-BY-NC, modèle non intégré, qualité non testée. |
| Masa/Masana (`mcn`) | [OmniVoice](https://github.com/k2-fsa/OmniVoice/blob/master/docs/languages.md) répertorie `mcn` (10,09 h). | Poids CC-BY-NC; variété et qualité locales non validées; modèle non intégré. |
| Bafia (`ksf`) | [OmniVoice](https://github.com/k2-fsa/OmniVoice/blob/master/docs/languages.md) répertorie `ksf` (16,43 h). | Le volume d’entraînement n’est pas une mesure de qualité. Poids CC-BY-NC; modèle non intégré. |
| Tupuri (`tui`) | [OmniVoice](https://github.com/k2-fsa/OmniVoice/blob/master/docs/languages.md) répertorie Tupuri (`tui`, 9,26 h). | La fiche ne prouve pas la couverture de la variété camerounaise Bango/Kaélé plutôt que Banwere. Poids CC-BY-NC; modèle non intégré. |
| Basaa (`bas`) | [OmniVoice](https://github.com/k2-fsa/OmniVoice/blob/master/docs/languages.md) répertorie Basa (Cameroon, `bas`, 10,66 h). | Couverture de données, pas voix validée. Le catalogue [MMS](https://dl.fbaipublicfiles.com/mms/misc/language_coverage_mms.html) indique ASR/LID mais pas TTS pour `bas`. Poids OmniVoice CC-BY-NC; non intégré. |
| Duala (`dua`) | [OmniVoice](https://github.com/k2-fsa/OmniVoice/blob/master/docs/languages.md) répertorie `dua` (12,13 h). | Variété et qualité non validées. Un corpus audio distinct n’est pas un modèle TTS prêt à utiliser. Poids CC-BY-NC; non intégré. |
| Yemba (`ybb`) | [MMS TTS Yemba](https://huggingface.co/facebook/mms-tts-ybb), checkpoint VITS pour `ybb`. | Licence CC-BY-NC 4.0; inférence locale à installer; non testé ni intégré. Le checkpoint n’a pas été évalué par un locuteur local dans ce travail. |
| Mafa (`maf`) | [OmniVoice](https://github.com/k2-fsa/OmniVoice/blob/master/docs/languages.md) répertorie `maf` (9,97 h). | La variété camerounaise et la qualité ne sont pas établies par ces heures. Poids CC-BY-NC; modèle non intégré. |

Pour OmniVoice, la fiche distingue le code Apache-2.0 des poids CC-BY-NC; l’exemple d’inférence se fait localement et la fiche consultée n’annonce pas de fournisseur d’inférence hébergé. Le mode automatique sans référence ne prouve pas une prononciation native; le clonage à partir d’un audio de référence nécessite des droits et le consentement du locuteur. Aucune voix réelle n’a été réutilisée ni clonée ici. Une licence non commerciale n’autorise pas un usage commercial par défaut.

## Fichiers réellement présents

Les sons sous `extension/audio/` sont des **enregistrements humains de mots isolés**, pas des phrases synthétisées : deux entrées Fulfulde et une entrée Ewondo. Les crédits et licences sont dans [`extension/audio/CREDITS.md`](../extension/audio/CREDITS.md). Aucun échantillon de phrase synthétique n’est présent pour les treize langues.

Avant d’ajouter une phrase : obtenir sa traduction exacte et sa rétrotraduction, la faire approuver par un locuteur de la variété retenue, vérifier la licence du modèle/du fichier audio et faire écouter le rendu à des locuteurs locaux. Conserver les montants, devises et variables inchangés; ne jamais diffuser une traduction financière non approuvée.
