// Safinum Lingua — traduit l'interface d'un service financier en langues camerounaises
// sans modifier son code. Principe : on ne touche qu'aux nœuds texte « libellés »,
// jamais aux valeurs (montants, numéros, références, noms) ni aux champs de saisie.
(() => {
  "use strict";
  if (globalThis.__safinumLingua) return;
  globalThis.__safinumLingua = true;

  const DICT = globalThis.SAFINUM_DICT || { languages: [], entries: {}, glossary: [] };
  // Langues = colonnes du CSV (voir tools/build_dictionary.py)
  const LANGS = Object.fromEntries(DICT.languages.map((l) => [l.code, l]));
  const FIRST = DICT.languages[0]?.code;
  const DEFAULTS = { lang: FIRST, sites: { "safinum.cm": true }, ai: false, tooltip: true, voice: true, rate: 1 };

  let settings = { ...DEFAULTS };
  let active = false;

  // Après un rechargement de l'extension, ce script reste dans les pages déjà ouvertes
  // mais n'a plus accès à chrome.* (« Extension context invalidated »).
  // On le détecte au lieu de planter : la traduction affichée reste, le reste est désactivé.
  let orphan = false;
  const alive = () => {
    try {
      return !orphan && !!chrome.runtime?.id;
    } catch {
      return false;
    }
  };
  function becomeOrphan() {
    if (orphan) return;
    orphan = true;
    stopSpeaking();
    if (widget) {
      widget.spk.hidden = true;
      widget.select.disabled = true;
      widgetStatus("Extension mise à jour : rechargez la page (F5)");
    }
  }
  function saveSettings(values) {
    if (!alive()) return becomeOrphan();
    try {
      chrome.storage.sync.set(values);
    } catch {
      becomeOrphan();
    }
  }

  // ---------- Normalisation (doit rester identique à tools/build_dictionary.py) ----------
  const norm = (s) =>
    s.normalize("NFC").replace(/[’‘]/g, "'").replace(/[\s  ]+/g, " ").trim().toLowerCase();

  // ---------- Détection des valeurs à protéger ----------
  const PROTECTED = [
    /^[+\-−]?\s*\d[\d\s  .,]*\s*(FCFA|XAF|F\s?CFA)$/i, // montants
    /^\+?\d[\d\s ().-]{6,}$/, // téléphones
    /^[A-Z]{2,6}-\d{4}-[A-Z0-9]{4,}$/, // références SAF-2026-XXXXXX
    /^[A-Z]{2}(\s?\d{2,5}){3,}$/, // numéros de compte CM 001 2345…
    /^[A-Z]+_\d{3}$/, // codes d'erreur
    /^\d{1,2}\s+\p{L}+\.?\s+\d{4}$/u, // 05 nov. 2026
    /^\p{L}{3,9}\.?\s+\d{1,2},\s+\d{4}$/u, // Nov 5, 2026
  ];
  const PROPER_NAME = /^\p{Lu}[\p{L}'’-]*(\s+\p{Lu}[\p{L}'’-]*)*$/u;
  const SKIP_SELECTOR =
    "script,style,noscript,textarea,input,code,pre,svg,[contenteditable=''],[contenteditable='true'],[translate='no'],.notranslate,#safinum-lingua-host";

  const isProtected = (text) => {
    const t = text.trim();
    if (!/\p{L}/u.test(t)) return true; // que des chiffres / symboles
    return PROTECTED.some((re) => re.test(t));
  };

  // ---------- Recherche dans le dictionaire ----------
  // Renvoie { text, id, rest } : id = ligne du CSV (pour l'enregistrement audio),
  // rest = partie laissée intacte (ponctuation, valeur après « : »).
  function lookup(text) {
    const e = DICT.entries[norm(text)];
    return e && e[settings.lang] ? { t: e[settings.lang], id: e.id } : null;
  }

  function translateKnown(text) {
    const direct = lookup(text);
    if (direct) return { text: direct.t, id: direct.id, rest: "" };
    // Ponctuation finale absente du dictionnaire (« Frais : » …)
    const m = text.match(/^(.*?)(\s*[:.!?]\s*)$/s);
    if (m && m[1].trim()) {
      const r = lookup(m[1]);
      if (r) return { text: r.t + m[2], id: r.id, rest: m[2] };
    }
    // Libellé composé : « Numéro de compte : CM 001… », « Bonjour, Amina »
    for (const sep of [" : ", ": ", ", "]) {
      const i = text.indexOf(sep);
      if (i > 0) {
        const r = lookup(text.slice(0, i));
        if (r) return { text: r.t + text.slice(i), id: r.id, rest: text.slice(i) }; // la partie droite reste intacte
      }
    }
    return null;
  }

  // ---------- État des nœuds traduits ----------
  // node -> { orig, applied, id, rest, label }  (label : mention « Non traduit » d'un texte inédit)
  const state = new WeakMap();
  const touched = new Set();
  const titled = new Set();

  function setText(node, orig, translated, id = null, rest = "", label = null) {
    const lead = orig.match(/^\s*/)[0];
    const trail = orig.match(/\s*$/)[0];
    const applied = lead + translated.trim() + trail;
    state.set(node, { orig, applied, id, rest, label });
    touched.add(node);
    if (node.nodeValue !== applied) node.nodeValue = applied;
    const parent = node.parentElement;
    if (parent && parent.childNodes.length === 1) {
      // Un texte inédit annoté reste surtout en français : on ne change pas sa langue.
      if (!label && LANGS[settings.lang].htmlLang) parent.setAttribute("lang", LANGS[settings.lang].htmlLang);
      if (settings.tooltip && !parent.hasAttribute("title")) {
        parent.setAttribute("title", orig.trim());
        parent.dataset.slTitle = "1";
        titled.add(parent);
      }
    }
  }

  function originalOf(node) {
    const s = state.get(node);
    // Si l'application a changé le texte entre-temps, c'est le nouveau texte source.
    if (s && node.nodeValue === s.applied) return s.orig;
    return node.nodeValue;
  }

  function processTextNode(node) {
    const parent = node.parentElement;
    if (!parent || parent.closest(SKIP_SELECTOR)) return;
    const orig = originalOf(node);
    if (!orig || !orig.trim() || isProtected(orig)) return;
    const language = LANGS[settings.lang];
    // Les langues sans entrées approuvées restent en mode aperçu : conserver le texte source.
    if (!language || language.translationStatus === "pending" || !language.entryCount) return;

    const known = translateKnown(orig);
    if (known) return setText(node, orig, known.text, known.id, known.rest);

    // Texte inconnu : nom propre -> jamais traduit
    if (PROPER_NAME.test(orig.trim())) return;

    // Texte inédit (message ajouté par le service ou par le jury) : aide hors ligne
    const unseen = orig.trim().split(/\s+/).length >= 3 ? translateUnseen(orig.trim()) : null;
    if (unseen) setText(node, orig, unseen.text, null, "", unseen.label);
    if (settings.ai) queueAI(node, orig);
  }

  // ---------- Contenu inédit, sans IA ni réseau ----------
  // 1) les phrases déjà connues du dictionnaire sont traduites ;
  // 2) dans les autres, chaque terme du glossaire reçoit sa traduction entre parenthèses ;
  // 3) le texte est précédé d'une mention honnête « Non traduit » (U01), ou d'un
  //    avertissement (U02) s'il parle de code, mot de passe, fraude, compte bloqué…
  const uiText = (id) => {
    const u = DICT.ui?.[id];
    return u ? u[settings.lang] || u.fr : "";
  };
  const B = "(?<![\\p{L}\\d])"; // début de mot (lettres accentuées comprises)
  const E = "(?![\\p{L}\\d])"; // fin de mot
  const SECURITY_HINT = new RegExp(
    B +
      "(fraud\\p{L}*|arnaque\\p{L}*|escroc\\p{L}*|code secret|code pin|pin|otp|mot de passe|password|" +
      "ne (communiquez|partagez|donnez) jamais|never (share|give)|suspendu\\p{L}*|suspended|bloqu\\p{L}*|blocked|" +
      "piratage|phishing|hack\\p{L}*|s[ée]curit[ée]|security|urgent\\p{L}*)" +
      E,
    "iu"
  );
  const escapeRe = (t) => t.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const glossCache = new Map(); // langue -> { re, map }
  function glossFor(lang) {
    if (glossCache.has(lang)) return glossCache.get(lang);
    const map = new Map();
    for (const g of DICT.glossary) {
      if (!g[lang]) continue;
      const target = g[lang].split(" / ")[0];
      for (const src of [...g.fr.split(" / "), ...g.en.split(" / ")]) {
        const term = norm(src.replace(/\(s\)$/, ""));
        if (term.length > 2 && !map.has(term)) map.set(term, target);
      }
    }
    const terms = [...map.keys()].sort((a, b) => b.length - a.length).map(escapeRe);
    const re = terms.length ? new RegExp(B + "(" + terms.join("|") + ")s?" + E, "giu") : null;
    const g = { re, map };
    glossCache.set(lang, g);
    return g;
  }
  function gloss(sentence) {
    const { re, map } = glossFor(settings.lang);
    if (!re) return { text: sentence, n: 0 };
    const seen = new Set();
    let n = 0;
    const text = sentence.replace(re, (m, term) => {
      const key = norm(term);
      const t = map.get(key);
      if (!t || seen.has(key) || norm(m).includes(norm(t))) return m; // une seule explication, et rien si le mot la contient déjà
      seen.add(key);
      n++;
      return `${m} (${t})`;
    });
    return { text, n };
  }
  // Une voix source est choisie seulement si la langue du texte est identifiable.
  // Si elle ne l'est pas, on reste silencieux plutôt que d'employer une voix étrangère.
  function sourceLanguage(text) {
    const page = (document.documentElement.lang || "").toLowerCase().split(/[-_]/)[0];
    if (page === "fr" || page === "en") return page;
    const value = norm(text);
    const en = (value.match(/\b(the|your|you|will|is|are|and|to|of|if|not|please|this|transfer|amount|recipient)\b/g) || []).length;
    const fr = (value.match(/\b(le|la|les|un|une|des|du|de|votre|vous|avec|pour|avant|montant|bénéficiaire|transfert|confirmer|merci|bonjour)\b/g) || []).length;
    if (en >= 2 && en > fr) return "en";
    if (fr >= 2 && fr > en) return "fr";
    return null;
  }

  function translateUnseen(text) {
    const parts = text.split(/(?<=[.!?])\s+/);
    let unknown = 0;
    let glossed = 0;
    const out = parts.map((sentence) => {
      const k = translateKnown(sentence);
      if (k) return k.text;
      unknown++;
      const g = gloss(sentence);
      glossed += g.n;
      return g.text;
    });
    if (!unknown) return { text: out.join(" "), label: null }; // tout était connu
    const security = SECURITY_HINT.test(text);
    if (!security && !glossed && unknown === parts.length) return null; // rien pour aider
    const label = uiText(security ? "U02" : "U01");
    return label ? { text: `${label} ${out.join(" ")}`, label } : null;
  }

  function processAttributes(el) {
    for (const attr of ["aria-label", "placeholder"]) {
      if (!el.hasAttribute(attr)) continue;
      const key = `slOrig_${attr.replace("-", "_")}`;
      const current = el.getAttribute(attr);
      const orig = el.dataset[key] && el.dataset[`${key}_applied`] === current ? el.dataset[key] : current;
      const t = translateKnown(orig)?.text;
      if (t) {
        el.dataset[key] = orig;
        el.dataset[`${key}_applied`] = t;
        if (current !== t) el.setAttribute(attr, t);
        touched.add(el);
      }
    }
  }

  function walk(root) {
    if (!active || !root) return;
    if (root.nodeType === Node.TEXT_NODE) return processTextNode(root);
    if (root.nodeType !== Node.ELEMENT_NODE && root.nodeType !== Node.DOCUMENT_NODE) return;
    if (root.nodeType === Node.ELEMENT_NODE) {
      if (root.closest(SKIP_SELECTOR)) return;
      processAttributes(root);
    }
    const tw = document.createTreeWalker(root, NodeFilter.SHOW_TEXT | NodeFilter.SHOW_ELEMENT);
    let n;
    while ((n = tw.nextNode())) {
      if (n.nodeType === Node.TEXT_NODE) processTextNode(n);
      else processAttributes(n);
    }
  }

  function restoreAll() {
    for (const node of touched) {
      if (node.nodeType === Node.TEXT_NODE) {
        const s = state.get(node);
        if (s && node.isConnected && node.nodeValue === s.applied) node.nodeValue = s.orig;
        state.delete(node);
        const p = node.parentElement;
        if (p) p.removeAttribute("lang");
      } else {
        for (const attr of ["aria-label", "placeholder"]) {
          const key = `slOrig_${attr.replace("-", "_")}`;
          if (node.dataset && node.dataset[key]) {
            if (node.getAttribute(attr) === node.dataset[`${key}_applied`]) node.setAttribute(attr, node.dataset[key]);
            delete node.dataset[key];
            delete node.dataset[`${key}_applied`];
          }
        }
      }
    }
    for (const el of titled) {
      if (el.dataset.slTitle) {
        el.removeAttribute("title");
        delete el.dataset.slTitle;
      }
    }
    touched.clear();
    titled.clear();
  }

  // ---------- Observation du contenu dynamique ----------
  const dirty = new Set();
  let scheduled = false;
  const observer = new MutationObserver((records) => {
    for (const r of records) {
      if (r.type === "characterData") {
        const s = state.get(r.target);
        if (s && r.target.nodeValue === s.applied) continue; // notre propre écriture
        dirty.add(r.target);
      } else if (r.type === "attributes") {
        dirty.add(r.target);
      } else {
        r.addedNodes.forEach((n) => dirty.add(n));
      }
    }
    if (!scheduled && dirty.size) {
      scheduled = true;
      requestAnimationFrame(() => {
        scheduled = false;
        const batch = [...dirty];
        dirty.clear();
        batch.forEach((n) => n.isConnected && walk(n));
      });
    }
  });

  function start() {
    if (active) return;
    active = true;
    walk(document.body);
    observer.observe(document.body, {
      childList: true,
      subtree: true,
      characterData: true,
      attributes: true,
      attributeFilter: ["aria-label", "placeholder"],
    });
  }

  function stop() {
    if (!active) return;
    active = false;
    observer.disconnect();
    dirty.clear();
    restoreAll();
  }

  // ---------- Traduction IA (facultative) des contenus inédits ----------
  const aiCache = new Map(); // `${lang}|${texte}` -> traduction | null (échec)
  const aiQueue = new Map(); // texte -> Set(nodes)
  let aiTimer = null;

  function queueAI(node, orig) {
    if (!LANGS[settings.lang]?.allowAI) return;
    const text = orig.trim();
    if (text.split(/\s+/).length < 2 || text.length < 8) return;
    const cached = aiCache.get(`${settings.lang}|${text}`);
    if (cached) return setText(node, orig, cached);
    if (cached === null) return;
    if (!aiQueue.has(text)) aiQueue.set(text, new Set());
    aiQueue.get(text).add(node);
    clearTimeout(aiTimer);
    aiTimer = setTimeout(flushAI, 400);
  }

  // Remplace chiffres, montants, références, codes et noms par ⟦n⟧ avant l'envoi.
  function mask(text) {
    const kept = [];
    const put = (m) => {
      kept.push(m);
      return `⟦${kept.length - 1}⟧`;
    };
    let out = text
      .replace(/\b[A-Z]{2,6}-\d{4}-[A-Z0-9]{4,}\b/g, put)
      .replace(/\b[A-Z]+_\d{3}\b/g, put)
      .replace(/\+?\d(?:[\d.,]|[\s  ](?=\d))*(?:\s?(?:FCFA|XAF))?(?:\s?%)?/g, put)
      .replace(/\b[A-Z]{2,}\b/g, put)
      .replace(/\p{Lu}[\p{Ll}'’-]+(?:[\s-]\p{Lu}[\p{Ll}'’-]+)+/gu, put);
    // Mot à majuscule au milieu d'une phrase = nom propre probable
    out = out.replace(/(?<=[\p{Ll},;]\s)\p{Lu}[\p{L}'’-]+/gu, put);
    return { masked: out, kept };
  }

  function unmask(translated, kept) {
    for (let i = 0; i < kept.length; i++) {
      const tag = `⟦${i}⟧`;
      if (translated.split(tag).length !== 2) return null; // marqueur perdu ou dupliqué -> rejet
      translated = translated.replace(tag, () => kept[i]);
    }
    return /⟦\d+⟧/.test(translated) ? null : translated;
  }

  async function flushAI() {
    const lang = settings.lang;
    const items = [...aiQueue.entries()].slice(0, 20);
    items.forEach(([t]) => aiQueue.delete(t));
    if (aiQueue.size) aiTimer = setTimeout(flushAI, 400);
    if (!items.length) return;

    const masked = items.map(([t]) => mask(t));
    const glossary = DICT.glossary.filter((g) => g[lang]).map((g) => `${g.fr} / ${g.en} = ${g[lang]}`);
    widgetStatus("Traduction IA…");
    let res;
    if (!alive()) return becomeOrphan();
    try {
      res = await chrome.runtime.sendMessage({
        type: "sl-translate",
        lang,
        langDescription: LANGS[lang].description,
        texts: masked.map((m) => m.masked),
        glossary,
      });
    } catch (e) {
      res = { error: String(e) };
    }
    if (!res || res.error || !Array.isArray(res.translations) || res.translations.length !== items.length) {
      widgetStatus(res && res.error === "no-key" ? "IA : clé API manquante" : "IA indisponible");
      items.forEach(([t]) => aiCache.set(`${lang}|${t}`, null));
      return;
    }
    widgetStatus("Traduction IA provisoire — validation locale requise");
    items.forEach(([text, nodes], i) => {
      const t = unmask(res.translations[i], masked[i].kept);
      aiCache.set(`${lang}|${text}`, t);
      if (!t || lang !== settings.lang || !active) return;
      nodes.forEach((node) => {
        if (node.isConnected && originalOf(node).trim() === text) setText(node, originalOf(node), t);
      });
    });
  }

  // ---------- Petit sélecteur flottant (Shadow DOM : invisible pour la page) ----------
  let widget = null;
  function buildWidget() {
    const host = document.createElement("div");
    host.id = "safinum-lingua-host";
    host.setAttribute("translate", "no");
    const root = host.attachShadow({ mode: "open" });
    root.innerHTML = `
      <style>
        :host { all: initial; }
        .box { position: fixed; left: 16px; bottom: 16px; z-index: 2147483646;
          display: flex; align-items: center; gap: 8px; padding: 8px 12px;
          background: #111827; color: #fff; border: 2px solid #FFEB3B; border-radius: 999px;
          font: 600 14px/1.2 system-ui, sans-serif; box-shadow: 0 4px 16px rgba(0,0,0,.35); }
        select { font: inherit; color: #111827; background: #fff; border: 0; border-radius: 6px; padding: 4px 6px; }
        select:focus-visible { outline: 3px solid #00BFFF; outline-offset: 2px; }
        .st { font-weight: 400; font-size: 12px; color: #FFEB3B; }
        .st:empty { display: none; }
        .spk { position: fixed; z-index: 2147483647; width: 32px; height: 32px; padding: 0;
          border: 2px solid #FFEB3B; border-radius: 50%; background: #111827; color: #fff;
          font-size: 16px; line-height: 1; cursor: pointer; box-shadow: 0 2px 8px rgba(0,0,0,.35); }
        .spk:focus-visible { outline: 3px solid #00BFFF; outline-offset: 2px; }
        .spk[hidden], .hl[hidden] { display: none; }
        .hl { position: fixed; z-index: 2147483645; pointer-events: none;
          border: 3px solid #FFEB3B; border-radius: 6px; background: rgba(255,235,59,.18); }
      </style>
      <div class="hl" hidden></div>
      <button class="spk" type="button" hidden aria-label="Écouter ce texte (Alt+L)" title="Écouter (Alt+L)">🔊</button>
      <div class="box" role="region" aria-label="Langue de l'interface">
        <span aria-hidden="true">🌍</span>
        <select aria-label="Choisir la langue"></select>
        <span class="st" role="status" aria-live="polite"></span>
      </div>`;
    const select = root.querySelector("select");
    for (const [value, label] of [...DICT.languages.map((l) => [l.code, l.selectorLabel || l.label]), ["off", "Original"]]) {
      select.append(new Option(label, value));
    }
    select.addEventListener("change", () => {
      const v = select.value;
      const h = location.hostname;
      const sites = { ...settings.sites };
      if (v === "off") {
        for (const d of Object.keys(sites)) if (h === d || h.endsWith("." + d)) sites[d] = false;
        sites[h] = false;
        saveSettings({ sites });
      } else saveSettings({ lang: v, sites: { ...sites, [h]: true } });
    });
    const spk = root.querySelector(".spk");
    spk.addEventListener("click", () => readElement(voiceTarget));
    spk.addEventListener("mouseenter", () => clearTimeout(hideTimer));
    spk.addEventListener("mouseleave", scheduleHide);
    document.documentElement.appendChild(host);
    widget = { host, select, status: root.querySelector(".st"), spk, hl: root.querySelector(".hl") };
  }
  function widgetStatus(msg) {
    if (widget) widget.status.textContent = msg;
  }
  function syncWidget() {
    if (!widget) buildWidget();
    const enabled = siteEnabled();
    widget.select.value = enabled ? settings.lang : "off";
    const language = LANGS[settings.lang];
    if (!enabled || !language) widgetStatus("");
    else if (language.translationStatus === "pending" || !language.entryCount) {
      widgetStatus("Aucune traduction chargée — texte original conservé");
    } else if (language.translationStatus === "draft") {
      widgetStatus("Traductions provisoires — validation locale requise");
    }
  }

  // ---------- Lecture vocale ----------
  // 1) enregistrement d'un locuteur natif (extension/audio/<langue>/<id>.*) s'il existe ;
  // 2) sinon voix système locale correspondant exactement au code de la langue choisie.
  // Aucune substitution par une voix française/anglaise n'est permise pour une langue locale.
  // Seules les voix LOCALES sont utilisées : les voix « en ligne » de Chrome envoient
  // le texte à un serveur, ce que la règle de l'épreuve interdit. Rien n'est stocké.
  const AUDIO = DICT.audio || {};
  const TTS = "speechSynthesis" in globalThis ? globalThis.speechSynthesis : null;
  let localVoices = [];
  // Firefox marque à tort ses voix système (speech-dispatcher, SAPI…) comme non locales,
  // mais il ne propose aucune voix en ligne : on les accepte toutes. Chrome et Edge, eux,
  // ont des voix en ligne (« Google… », « … Online (Natural) ») qu'on exclut.
  const IS_FIREFOX = /\bFirefox\//.test(navigator.userAgent);
  const isLocalVoice = (v) => v.localService || IS_FIREFOX;
  const loadVoices = () => (localVoices = TTS ? TTS.getVoices().filter(isLocalVoice) : []);
  if (TTS) {
    loadVoices();
    TTS.addEventListener("voiceschanged", loadVoices);
  }
  const normalizeVoiceLang = (value) => (value || "").toLowerCase().replace("_", "-");
  function exactVoice(want) {
    const expected = normalizeVoiceLang(want);
    return localVoices.find((v) => normalizeVoiceLang(v.lang) === expected) || null;
  }
  function sourceVoice(want) {
    if (want !== "fr" && want !== "en") return null;
    return localVoices.find((v) => {
      const actual = normalizeVoiceLang(v.lang);
      return actual === want || actual.startsWith(`${want}-`);
    }) || null;
  }

  const READABLE = "button,a,label,li,tr,p,h1,h2,h3,h4,h5,h6,[role=alert],[role=status],[role=button]";
  let voiceTarget = null;
  let hideTimer = null;
  let playToken = 0;
  let currentAudio = null;

  const hasTranslatedText = (el) =>
    [...el.childNodes].some((n) => n.nodeType === Node.TEXT_NODE && state.get(n)?.applied === n.nodeValue);

  // Élément « lisible » sous le pointeur ou le focus : il doit contenir un texte traduit.
  function readableFrom(start) {
    let el = start?.nodeType === Node.ELEMENT_NODE ? start : start?.parentElement;
    for (let i = 0; el && i < 4; i++, el = el.parentElement) {
      if (el === widget?.host || el === document.body) return null;
      if (hasTranslatedText(el)) {
        const block = el.closest(READABLE);
        return block && block !== document.body && block.textContent.length < 300 ? block : el;
      }
    }
    return null;
  }

  // Découpe le texte de l'élément en morceaux : enregistrement audio ou synthèse.
  function segmentsOf(el) {
    const segs = [];
    const files = AUDIO[settings.lang] || {};
    const pushTTS = (text, translated, lang = null) => {
      // « 250 000 » -> « 250000 » pour que la voix lise le nombre entier
      const t = text.replace(/(\d)[\s  ](?=\d{3}\b)/g, "$1").trim();
      if (!/[\p{L}\d]/u.test(t)) return;
      const last = segs[segs.length - 1];
      if (last && last.tts && last.translated === translated && last.lang === lang) last.tts += ", " + t;
      else segs.push({ tts: t, translated, lang });
    };
    const tw = document.createTreeWalker(el, NodeFilter.SHOW_TEXT);
    let n;
    while ((n = tw.nextNode())) {
      if (!n.nodeValue.trim() || n.parentElement.closest("script,style,noscript")) continue;
      const s = state.get(n);
      const mine = s && s.applied === n.nodeValue;
      if (mine && s.label) {
        // Texte inédit : la mention dans la langue choisie, puis la source si son code est connu.
        pushTTS(s.label, true, LANGS[settings.lang]?.htmlLang || null);
        pushTTS(s.orig, false, sourceLanguage(s.orig));
      } else if (mine && s.id && files[s.id] && alive()) {
        segs.push({ audio: chrome.runtime.getURL(`audio/${settings.lang}/${files[s.id]}`) });
        pushTTS(s.rest, false, sourceLanguage(s.orig)); // texte source annexe; jamais de voix étrangère
      } else {
        const speechLang = mine ? LANGS[settings.lang]?.htmlLang : sourceLanguage(n.nodeValue);
        pushTTS(n.nodeValue, !!mine, speechLang || null);
      }
    }
    return segs;
  }

  function stopSpeaking() {
    playToken++;
    if (TTS) TTS.cancel();
    if (currentAudio) currentAudio.pause();
    currentAudio = null;
    if (widget) widget.hl.hidden = true;
  }

  const playAudio = (url) =>
    new Promise((resolve) => {
      const a = new Audio(url);
      currentAudio = a;
      a.onended = a.onerror = () => resolve();
      a.play().catch(resolve);
    });

  const say = (text, voice) =>
    new Promise((resolve) => {
      const u = new SpeechSynthesisUtterance(text);
      u.voice = voice;
      u.lang = voice.lang;
      u.rate = Number(settings.rate) || 1;
      u.pitch = 1;
      u.onend = u.onerror = () => resolve();
      TTS.speak(u);
    });

  async function readElement(el) {
    if (!el || !el.isConnected) return;
    stopSpeaking();
    const token = playToken;
    const segs = segmentsOf(el);
    if (!segs.length) return;
    const lang = LANGS[settings.lang];
    const vTranslated = exactVoice(lang.htmlLang);
    const r = el.getBoundingClientRect();
    Object.assign(widget.hl.style, { left: r.left - 4 + "px", top: r.top - 4 + "px", width: r.width + 8 + "px", height: r.height + 8 + "px" });
    widget.hl.hidden = false;
    let silent = false;
    for (const seg of segs) {
      if (token !== playToken) return;
      if (seg.audio) await playAudio(seg.audio);
      else {
        const v = seg.translated ? vTranslated : sourceVoice(seg.lang);
        if (!v) {
          silent = true;
          continue;
        }
        await say(seg.tts, v);
      }
    }
    if (token !== playToken) return;
    widget.hl.hidden = true;
    if (silent) {
      widgetStatus(TTS ? `Voix locale correspondante indisponible pour un ou plusieurs segments; enregistrement natif nécessaire (${lang.htmlLang}).` : "Pas de synthèse vocale locale dans ce navigateur : enregistrement natif nécessaire.");
    }
    else widgetStatus("");
  }

  function showSpeaker(el) {
    clearTimeout(hideTimer);
    voiceTarget = el;
    const r = el.getBoundingClientRect();
    const left = Math.min(r.right + 6, innerWidth - 38);
    const top = Math.max(4, Math.min(r.top + r.height / 2 - 16, innerHeight - 38));
    Object.assign(widget.spk.style, { left: left + "px", top: top + "px" });
    widget.spk.hidden = false;
  }

  function scheduleHide() {
    clearTimeout(hideTimer);
    hideTimer = setTimeout(() => {
      if (widget) widget.spk.hidden = true;
      voiceTarget = null;
    }, 1500);
  }

  const voiceOn = () => {
    if (!active || !settings.voice || !widget) return false;
    if (alive()) return true;
    becomeOrphan();
    return false;
  };

  document.addEventListener(
    "mouseover",
    (e) => {
      if (!voiceOn() || e.target === widget.host) return;
      const el = readableFrom(e.target);
      if (el) showSpeaker(el);
      else if (voiceTarget && !voiceTarget.contains(e.target)) scheduleHide();
    },
    { passive: true, capture: true }
  );
  document.addEventListener(
    "focusin",
    (e) => {
      if (!voiceOn() || e.target === widget.host) return;
      const el = readableFrom(e.target);
      if (el) showSpeaker(el);
    },
    { capture: true }
  );
  // Alt+L : lire l'élément qui a le focus (ou celui sous le pointeur). Échap : arrêter.
  document.addEventListener(
    "keydown",
    (e) => {
      if (!voiceOn()) return;
      if (e.altKey && !e.ctrlKey && !e.metaKey && e.code === "KeyL") {
        const el = readableFrom(document.activeElement) || voiceTarget;
        if (el) {
          e.preventDefault();
          readElement(el);
        }
      } else if (e.key === "Escape" && (TTS?.speaking || currentAudio)) stopSpeaking();
    },
    { capture: true }
  );
  addEventListener("scroll", () => widget && !widget.spk.hidden && scheduleHide(), { passive: true, capture: true });

  // ---------- Réglages ----------
  function siteEnabled() {
    const h = location.hostname;
    return Object.entries(settings.sites).some(([s, on]) => on && (h === s || h.endsWith("." + s)));
  }

  function apply(prevLang) {
    if (!LANGS[settings.lang]) settings.lang = FIRST; // langue retirée du CSV
    if (siteEnabled() && FIRST) {
      if (active && prevLang && prevLang !== settings.lang) {
        stop();
        aiQueue.clear();
      }
      start();
    } else stop();
    syncWidget();
    if (!active || !settings.voice) {
      stopSpeaking();
      if (widget) widget.spk.hidden = true;
    }
  }

  chrome.storage.sync.get(DEFAULTS, (s) => {
    settings = { ...DEFAULTS, ...s };
    apply();
  });
  chrome.storage.onChanged.addListener((changes, area) => {
    if (area !== "sync") return;
    const prevLang = settings.lang;
    for (const [k, { newValue }] of Object.entries(changes)) settings[k] = newValue;
    apply(prevLang);
  });
})();
