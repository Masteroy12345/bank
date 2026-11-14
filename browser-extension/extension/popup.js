const LANGUAGES = globalThis.SAFINUM_DICT.languages;
// Firefox marque ses voix système comme non locales; il ne fournit pas de voix réseau ici.
const IS_FIREFOX = /\bFirefox\//.test(navigator.userAgent);
const DEFAULTS = {
  lang: LANGUAGES[0].code,
  sites: { "safinum.cm": true },
  ai: false,
  tooltip: true,
  voice: true,
  rate: 1,
};
const $ = (id) => document.getElementById(id);
let settings = { ...DEFAULTS };

const normalizeLang = (value) => (value || "").toLowerCase().replace("_", "-");
const localVoices = () =>
  typeof speechSynthesis === "undefined"
    ? []
    : speechSynthesis.getVoices().filter((voice) => voice.localService || IS_FIREFOX);
const exactLocalVoice = (code) => {
  const expected = normalizeLang(code);
  return localVoices().find((voice) => normalizeLang(voice.lang) === expected) || null;
};

(async () => {
  for (const language of LANGUAGES) {
    $("lang").append(new Option(language.selectorLabel || language.label, language.code));
  }
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  let host = "";
  try {
    host = new URL(tab.url).hostname;
  } catch {}
  $("host").textContent = host || "ce site";

  const saved = await chrome.storage.sync.get(DEFAULTS);
  settings = { ...DEFAULTS, ...saved };
  const { apiKey = "" } = await chrome.storage.local.get("apiKey");
  $("lang").value = LANGUAGES.some((language) => language.code === settings.lang)
    ? settings.lang
    : DEFAULTS.lang;
  $("site").checked = Object.entries(settings.sites).some(
    ([domain, enabled]) => enabled && (host === domain || host.endsWith("." + domain))
  );
  $("site").disabled = !host;
  $("tooltip").checked = settings.tooltip;
  $("ai").checked = settings.ai;
  $("key").value = apiKey;
  $("keybox").hidden = !settings.ai;
  $("voice").checked = settings.voice;
  $("voicebox").hidden = !settings.voice;
  $("rate").value = String(settings.rate);
  if (!$ ("rate").value) $("rate").value = "1";
  showVoiceInfo($("lang").value);

  $("lang").onchange = () => {
    chrome.storage.sync.set({ lang: $("lang").value });
    showVoiceInfo($("lang").value);
  };
  $("voice").onchange = () => {
    $("voicebox").hidden = !$("voice").checked;
    settings.voice = $("voice").checked;
    chrome.storage.sync.set({ voice: settings.voice });
  };
  $("rate").onchange = () => {
    settings.rate = Number($("rate").value);
    chrome.storage.sync.set({ rate: settings.rate });
  };
  $("tooltip").onchange = () => chrome.storage.sync.set({ tooltip: $("tooltip").checked });
  $("ai").onchange = () => {
    $("keybox").hidden = !$("ai").checked;
    chrome.storage.sync.set({ ai: $("ai").checked });
  };
  $("key").onchange = () => chrome.storage.local.set({ apiKey: $("key").value.trim() });
  $("site").onchange = async () => {
    const current = await chrome.storage.sync.get(DEFAULTS);
    const sites = { ...current.sites };
    for (const domain of Object.keys(sites)) {
      if (host === domain || host.endsWith("." + domain)) sites[domain] = false;
    }
    sites[host] = $("site").checked;
    chrome.storage.sync.set({ sites });
  };

  if (typeof speechSynthesis !== "undefined") {
    speechSynthesis.onvoiceschanged = () => showVoiceInfo($("lang").value);
  }
})();

function showVoiceInfo(code) {
  const language = LANGUAGES.find((item) => item.code === code);
  if (!language) return;
  const recorded = Object.keys(globalThis.SAFINUM_DICT.audio?.[code] || {}).length;
  const total = new Set(
    Object.values(globalThis.SAFINUM_DICT.entries)
      .filter((entry) => entry[code])
      .map((entry) => entry.id)
  ).size;
  const voice = exactLocalVoice(language.htmlLang);
  $("translationinfo").textContent = language.translationStatus === "pending" || !language.entryCount
    ? "Aucune traduction chargée pour cette langue : le texte d’origine est conservé."
    : `Brouillons présents (${language.entryCount} entrées), non validés par des locuteurs locaux.`;
  const voiceSummary = voice
    ? `Voix système locale au code exact détectée (${voice.lang}).`
    : `Aucune voix système locale au code exact (${language.htmlLang}) détectée; seules les prises natives déjà présentes peuvent être lues.`;
  $("voiceinfo").textContent =
    `${recorded} / ${total} textes ont un enregistrement natif pour ${language.label}. ${voiceSummary} ${language.ttsResourceInfo || ""}`;
}
