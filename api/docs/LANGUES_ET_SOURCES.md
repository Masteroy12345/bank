# Langues pilotes SAFINUM : ressources et précautions

## Ce qu’il faut retenir

Les dix langues disposent de ressources partielles — corpus de parole lue, quelques lexiques ou corpus parallèles et des références linguistiques — mais **aucune source consultée n’établit un corpus bancaire complet ou des traductions financières déjà approuvées**. Les jeux de parole ne sont pas des traducteurs; dictionnaires, textes religieux et corpus narratifs ne constituent pas des libellés bancaires validés.

Avant toute utilisation, vérifier la licence de chaque fichier et la variété couverte. Certaines conditions NOODL/Nwulite-Obodo, certains droits de dictionnaires et certaines métadonnées ne sont pas résolus. Les langues locales restent en collecte et en revue : l’API ne doit jamais diffuser une proposition avant l’approbation humaine. Conserver la phrase source, les montants et devises, l’orthographe originale, le code de langue et la variété déclarée. Pour les instructions de paiement, consentements, frais, crédits, sécurité et recours, exiger une validation linguistique et conformité indépendante; le français reste le recours lorsqu’une traduction n’est pas approuvée.

## Synthèse rapide

| Langue | Ressources repérées | Point de vigilance majeur |
|---|---|---|
| Ewondo (`ewo`) | Common Voice, jeux ASR/TTS, corpus parallèle ewondo–français, lexique Yanda, prototype Apertium | Variétés et tons; licences Nwulite-Obodo à clarifier; Apertium est expérimental. |
| Fulfulde Adamawa (`fub`) | Corpus narratif parallèle, Common Voice, parole alignée, Apertium, dictionnaire et clavier Ajami | Pas de traduction financière; corpus narratif et TTS mono-voix ne sont pas représentatifs; vérifier NOODL. |
| Bamoun/Bamun (`bax`) | Corpus parallèle Bamun–français, Common Voice, jeux TTS, clavier Unicode Bamum | Pas de traduction financière; licence du corpus parallèle à clarifier et variété/graphie à valider. |
| Bulu (`bum`) | Common Voice, jeux ASR/TTS, dictionnaire multilingue, étude grammaticale | Pas de corpus parallèle français vérifié; droits du dictionnaire non établis; plusieurs dialectes. |
| Basaa (`bas`) | BOUQuET multilingue, ASR, dictionnaires et travaux d’orthographe | Licences ASR contradictoires; volume Basaa isolé de BOUQuET non vérifié. |
| Éton (`eto`) | Common Voice, jeu TTS, dictionnaire éton–français sous CC BY-NC-SA | Métadonnées du jeu ASR contradictoires (`eto`/`etn`); pas de corpus de phrases bancaires. |
| Tupuri (`tui`) | Common Voice, corpus ASR Bango/Banwere, TTS Bango, références lexicales | NOODL peut imposer des obligations; couverture surtout en parole lue; le dictionnaire numérisé est incomplet. |
| Bafut (`bfd`) | Common Voice, dictionnaire Bafut–anglais, grammaire, claviers Unicode | Pas de corpus parallèle français; ELAR est restreint; droits lexicaux à vérifier. |
| Ghomálá’ (`bbj`) | MAFAND français–Ghomala, lexique, dictionnaire et parole/texte bibliques | Licences et droits des textes sources à vérifier; aucune validation bancaire. |
| Medumba (`byv`) | Common Voice, petit corpus parallèle, article décrivant un corpus plus large, jeu TTS | Distinguer corpus attesté et corpus rapporté; jeu TTS NOODL très restrictif. |

## Ressources par langue

### Ewondo (`ewo`)

- **Parole :** [Common Voice – catalogue officiel](https://commonvoice.mozilla.org/en/datasets) répertorie des données Ewondo CC0. [Ewondo-ASR-Dataset (CLARIN/VLO)](https://vlo.clarin.eu/record/Other_47_oai_mdc_oai_clarin_eu_ewondo_asr_dataset_a2d44d9f.xml) décrit 1 781 enregistrements lus, 16 locuteurs et des transcriptions marquées en tons; le dialecte précis n’est pas donné. Les jeux ASR/TTS de l’IADH renvoient à la licence Nwulite-Obodo, dont les conditions détaillées doivent être vérifiées.
- **Texte et outils :** [Ewondo–French Parallel Corpus (CLARIN)](https://vlo.clarin.eu/record/Other_47_oai_mdc_oai_clarin_eu_ewondo_french_parallel_corpus_4c300545.xml) contient des textes ewondo–français issus d’enregistrements et de transcriptions, mais pas de phrases bancaires. [Apertium Ewondo–français](https://github.com/Ngue-Um/apertium-ewo-fra) est un prototype GPL-3.0 en incubateur; ses auteurs documentent des limites de tons/orthographe et des exemples à finaliser dans [l’article de 2022](https://www.euppublishing.com/doi/10.3366/ijhac.2022.0289).
- **À faire :** choisir la variété avec les locuteurs, conserver les tons/diacritiques et faire valider chaque terme financier. Ne pas traiter Apertium ou un corpus général comme un traducteur prêt pour des opérations.

### Fulfulde Adamawa (`fub`)

- **Texte :** le [corpus parallèle Adamawa Fulfulde–français de récits](https://mozilladatacollective.com/datasets/cml5asbhf009sme079y6sa9hm) est décrit comme contenant 1 977 lignes narratives; le catalogue indique NOODL-1.0, dont les obligations détaillées restent à confirmer.
- **Parole et outils :** [Common Voice](https://commonvoice.mozilla.org/en/datasets) répertorie le locale `fub` sous CC0. [Le jeu TTS Adamawa Fulfulde (CLARIN)](https://vlo.clarin.eu/record/Other_47_oai_mdc_oai_clarin_eu_adamawa_fulfulde_tts_dataset_5ddc826a.xml) comprend environ 3 h 31 de parole lue d’une seule personne et indique NOODL-Obodo. [Apertium-fub](https://github.com/apertium/apertium-fub) fournit des briques morphologiques GPL-3.0; la paire disponible est aussi [Fulfulde–anglais](https://github.com/apertium/apertium-fub-eng), pas français. Un dictionnaire [SIL](https://www.silcam.org/resources/archives/82623) et un clavier [Fulfulde Ajami Keyman](https://help.keyman.com/keyboard/fulfulde_ajami_qwerty/current-version) sont documentés.
- **À faire :** préciser script et variété; un corpus narratif ou une voix mono-locuteur ne valide pas des frais, consentements ou consignes bancaires. Examiner NOODL et les droits du dictionnaire avant tout usage commercial.

### Bamoun / Bamun (`bax`)

- **Texte et parole :** [Bamun–French Parallel Corpus 2.0 (CLARIN)](https://vlo.clarin.eu/record/Other_47_oai_mdc_oai_clarin_eu_bamun_french_parallel_corpus_2_0_2637e53d.xml) décrit 4 444 unités alignées; la licence est nommée Nwulite-Obodo, mais ses conditions détaillées doivent être vérifiées. [Common Voice (CLARIN)](https://vlo.clarin.eu/record/Other_47_oai_mdc_oai_clarin_eu_common_voice_scripted_speech_27_0_bamun_e5908218.xml) est sous CC0. Deux jeux TTS, [voix masculine](https://vlo.clarin.eu/record/Other_47_oai_mdc_oai_clarin_eu_bamun_tts_dataset_male_voice_ec8d8b52.xml) et [voix féminine](https://vlo.clarin.eu/record/Other_47_oai_mdc_oai_clarin_eu_bamun_tts_dataset_female_voice_d415a546.xml), ont aussi une licence nommée Nwulite-Obodo.
- **Saisie et orthographe :** le [clavier Bamum Keyman](https://keyman.com/keyboards/bamum) est une ressource Unicode sous MIT. Les notes [Bamum Unicode](https://www.unicode.org/charts/PDF/UA6A0.pdf) aident à préserver les signes; orthographe et variété doivent être choisies avec les locuteurs.
- **À faire :** les ressources sont utiles pour recherche et saisie, pas pour publier des messages financiers approuvés. Ne pas présumer de la représentativité des voix ou de l’exhaustivité du corpus parallèle.

### Bulu (`bum`)

- **Parole :** [Common Voice – catalogue officiel](https://commonvoice.mozilla.org/en/datasets) répertorie Bulu (`bum`) sous CC0. [Bulu-ASR-Dataset (CLARIN)](https://vlo.clarin.eu/record/Other_47_oai_mdc_oai_clarin_eu_bulu_asr_dataset_8aff566d.xml) décrit 819 enregistrements lus, 8 locuteurs et 9 sessions; la fiche indique la licence NWU Lite Obodo. [Bulu-TTS-Dataset (CLARIN)](https://vlo.clarin.eu/record/Other_47_oai_mdc_oai_clarin_eu_bulu_tts_dataset_1_0_6b9ee29d.xml) est mono-locuteur et la licence doit aussi être vérifiée.
- **Lexique :** le [dictionnaire Webonary Bulu](https://www.webonary.org/bulu/en/) est consultable en plusieurs langues et présente quatre dialectes (Yelinda, Yembana, Yengono, Bene). La licence de réutilisation des entrées n’est pas établie. Une [étude grammaticale ciblée](https://idiom.ucsd.edu/~eclem/barlew-clem-2014-augment-in-bulu.pdf) examine l’augment nominal; ce n’est pas un outil NLP.
- **À faire :** aucune traduction Bulu–français bancaire ou lexique financier approuvé n’a été vérifié. Ne pas confondre les dialectes et vérifier les droits avant extraction du dictionnaire.

### Basaa (`bas`)

- **Texte :** [BOUQuET sur Hugging Face](https://huggingface.co/datasets/facebook/bouquet) inclut `bas_Latn` et le français; une description rapporte 1 364 phrases dans cinq langues, sans décompte Basaa isolé confirmé. Le dépôt est CC BY 4.0 avec accès conditionné; ce contenu générique n’est pas une traduction bancaire.
- **Parole et lexique :** [Basaa-ASR-Dataset (CLARIN)](https://vlo.clarin.eu/record/Other_47_oai_mdc_oai_clarin_eu_basaa_asr_dataset_dd3e2174.xml) décrit 2 498 enregistrements, 15 locuteurs et 25 sessions. La notice CLARIN indique NWULITE-OBODO alors que l’index IADH/MDC indique NOODL-1.0 : demander une clarification écrite avant réutilisation. Le [dictionnaire Webonary](https://www.webonary.org/basaa/) et le dépôt [SIL Cameroon](https://www.silcam.org/resources/archives/47253) recensent des ressources lexicales, sans licence ouverte de réutilisation vérifiée. L’article [RAIL 2023 sur la conversion orthographique](https://aclanthology.org/2023.rail-1.11/) décrit une expérience, pas un normaliseur certifié.
- **À faire :** résoudre la licence et la variété orthographique, préserver les tons/diacritiques et faire valider le vocabulaire financier par des locuteurs et spécialistes.

### Éton (`eto`)

- **Ressources :** [Common Voice – catalogue officiel](https://commonvoice.mozilla.org/en/datasets) répertorie Eton (`eto`) sous CC0. Le [dictionnaire éton–français (PDF)](https://mark.vandevelde.cnrs.fr/wp-content/uploads/2022/11/dictionnaire_eton-francais.pdf) inclut un index inverse et une esquisse grammaticale; sa licence est CC BY-NC-SA 4.0. [Eton-TTS-Dataset (CLARIN)](https://vlo.clarin.eu/record/Other_47_oai_mdc_oai_clarin_eu_eton_tts_dataset_511d7dbe.xml) décrit 1 802 clips d’une locutrice; la licence Nwuli te Obodo est à vérifier.
- **Attention :** [Eton-ASR-Dataset (CLARIN)](https://vlo.clarin.eu/record/Other_47_oai_mdc_oai_clarin_eu_eton_asr_dataset_0c68aa5d.xml) décrit 1 402 clips et 11 locuteurs, mais le champ de langue indique `eto` alors que la description mentionne `etn`. Ne pas intégrer ce jeu sous `eto` avant correction ou confirmation du dépositaire.
- **À faire :** le dictionnaire est lexical, pas un corpus de phrases; confirmer l’orthographe et la variété avec les locuteurs. Pas de traduction financière approuvée repérée.

### Tupuri (`tui`)

- **Parole :** [Common Voice – catalogue officiel](https://commonvoice.mozilla.org/en/datasets) répertorie Tupuri sous CC0. [Tupuri-ASR-Dataset (CLARIN)](https://vlo.clarin.eu/record/Other_47_oai_mdc_oai_clarin_eu_tupuri_asr_dataset_d058d59a.xml) comprend 2 085 enregistrements lus, séparés entre Bango et Banwere, et est indiqué sous NOODL-1.0. Les jeux [TTS Bango voix féminine](https://vlo.clarin.eu/record/Other_47_oai_mdc_oai_clarin_eu_tupuri_bango_tts_dataset_female_voice_1f09dd2c.xml) et [TTS Bango voix masculine, marquée « Sample »](https://vlo.clarin.eu/record/Other_47_oai_mdc_oai_clarin_eu_sample_tupuri_bango_tts_dataset_male_voi_259b9597.xml) sont des données, pas des modèles prêts à déployer.
- **Texte et droits :** le [dictionnaire Tupuri–français–anglais](https://archive.org/details/rosettaproject_tui_detail-1) est annoncé ailleurs comme un ouvrage de 342 pages, mais la numérisation consultable ne contient que 6 pages. Vérifier les obligations NOODL, en particulier pour l’usage commercial ou le partage.
- **À faire :** sélectionner explicitement la variété; aucun corpus financier ni traduction approuvée n’a été trouvé. Une classification de famille linguistique dans une fiche ASR contredit des références linguistiques : utiliser le code `tui` et la validation communautaire plutôt que cette étiquette.

### Bafut (`bfd`)

- **Parole et outils :** la fiche Common Voice v27.0 [MDC](https://mozilladatacollective.com/datasets/cmu5sjsp60039o107kdjdkbzw) et son [manifeste de version](https://raw.githubusercontent.com/common-voice/cv-dataset/main/datasets/scripted-speech/cv-corpus-27.0-2026-09-11.json) indiquent 7 178 clips, 11,18 heures brutes, 10,05 heures validées et 36 contributeurs, sous CC0. Les statistiques ne prouvent pas la couverture dialectale. Le [dictionnaire Bafut–anglais Webonary](https://www.webonary.org/bafut/) comporte 6 152 entrées; les droits de réutilisation des entrées ne sont pas vérifiés. Des claviers [Keyman AZERTY](https://keyman.com/keyboards/sil_cameroon_azerty?bcp47=bfd) et [QWERTY](https://keyman.com/keyboards/sil_cameroon_qwerty?bcp47=bfd) sont documentés.
- **Archives à accès limité :** la collection [ELAR sur le système honorifique royal Bafut](https://www.elararchive.org/uncategorized/SO_27f1feaf-7ba5-453d-88fb-51e7aafd9928/) est en accès utilisateur. Ses [conditions](https://www.elararchive.org/legal/) limitent l’usage à l’étude privée sans autorisation écrite de diffusion ou réutilisation. Ne pas l’ingérer par défaut.
- **À faire :** aucune traduction bancaire Bafut–français ni modèle ASR/TTS validé n’a été trouvé. Confirmer variété et saisie avec la communauté.

### Ghomálá’ / Ghomala (`bbj`)

- **Texte :** [MAFAND-MT, corpus fr-bbj](https://github.com/masakhane-io/lafand-mt/tree/main/data/json_files/fr-bbj) comprend train/dev/test pour des textes de presse; le dépôt indique une licence non commerciale (CC-BY-NC) et précise que les licences des textes français sources varient. Le nombre d’exemples n’a pas été confirmé. Le petit [lexique français–Ghomala de Bandjoun](https://huggingface.co/datasets/stfotso/french-ghomala-bandjoun) est affiché sous Apache-2.0, mais les droits de l’ouvrage source doivent être clarifiés.
- **Lexique et audio :** un [dictionnaire Ghomálá’-Français](https://www.lielatatomdjap.org/images/pdf/DICTIONNAIRE_GHOMALA.pdf) est accessible en PDF, licence non vérifiée. Le [Nouveau Testament parlé](https://huggingface.co/datasets/flagship-ai/ghomala-spoken-bible) aligne du texte et de l’audio, mais les droits des textes bibliques sous-jacents restent à part; ce corpus religieux n’est pas un jeu bancaire. Les métadonnées détaillées de la fiche Common Voice ne sont pas confirmées.
- **À faire :** vérifier les licences et la variété; les ressources ne permettent pas d’approuver des chaînes financières sans traduction humaine indépendante et tests de compréhension.

### Medumba (`byv`)

- **Parole :** la fiche [Common Voice Medumba (MDC)](https://mozilladatacollective.com/datasets/cmu5u7v5l006to1074tzolo77) indique CC0; certains comptes et partitions de validation sont incohérents, à auditer dans les fichiers avant entraînement. Le [Sample Medumba-TTS-Dataset (MDC)](https://mozilladatacollective.com/datasets/cmqf58twx06fdl207ihp2oywl) contient 994 clips, environ 71 minutes, une voix et l’accès est sur demande. La fiche NOODL interdit notamment clonage de voix et usages GenAI sans autorisation explicite : ne pas l’intégrer à la production.
- **Texte :** [French–Medumba (Hugging Face)](https://huggingface.co/datasets/maseyan/French_Medumba) annonce 510 paires et CC BY 4.0, mais le dépôt est gated et la variété/provenance sont incomplètes. [Un article AfricaNLP 2025](https://aclanthology.org/2025.africanlp-1.18/) rapporte 2 050 phrases validées par un comité, mais ne relie pas de dépôt de données ni de licence; ne pas confondre les deux corpus.
- **À faire :** confirmer l’accès et les licences avant toute utilisation. Aucun corpus bancaire approuvé n’a été trouvé; préserver les signes AGLC/tons et faire réviser les chaînes sensibles par des locuteurs et la conformité.

## Modules communs à prévoir

1. **Validation linguistique et métier :** pour chaque chaîne sensible, versionner source française, traduction, rétrotraduction, code de langue, variété, date et approbateurs; faire relire par des locuteurs compétents, conformité/juridique et produit, puis tester la compréhension.
2. **Saisie et Unicode :** préserver la graphie d’origine, tons, diacritiques et scripts; tester les polices et claviers avec des locuteurs. Toute normalisation doit être documentée, réversible et sans perte.
3. **Audio et confidentialité :** consentement explicite, collecte minimale, accès restreint, durée de conservation claire et suppression possible. Ne jamais collecter PIN, OTP, numéros de compte ou conversations financières réelles.
4. **ASR/TTS :** les ressources trouvées sont principalement des enregistrements lus, pas des modèles validés. Mesurer les erreurs par variété et par domaine; exiger une vérification humaine pour tout contenu financier.
5. **Licences :** vérifier séparément le code, les textes, les audio et les dérivés. « Public » ou téléchargeable ne signifie pas nécessairement commercialisable ni libre d’entraînement; résoudre par écrit les fiches contradictoires et respecter les accès restreints.

Aucun corpus externe n’est intégré dans ce dépôt : ces références servent à la revue et à la planification d’une collecte consentie. La liste n’est pas une preuve d’exhaustivité des ressources existantes.
