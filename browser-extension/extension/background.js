// Service worker : traduction IA facultative des textes inédits via l'API Claude.
// Le content script envoie des textes déjà masqués (chiffres, noms, références -> ⟦n⟧).
// Appel HTTP direct : une extension MV3 sans étape de build ne peut pas charger le SDK.

const API_URL = "https://api.anthropic.com/v1/messages";
const MODEL = "claude-opus-5-5";

chrome.runtime.onMessage.addListener((msg, _sender, sendResponse) => {
  if (msg?.type !== "sl-translate") return false;
  translate(msg)
    .then(sendResponse)
    .catch((e) => sendResponse({ error: String(e?.message || e) }));
  return true; // réponse asynchrone
});

async function translate({ langDescription, texts, glossary }) {
  const { apiKey } = await chrome.storage.local.get("apiKey");
  if (!apiKey) return { error: "no-key" };

  const target = langDescription;

  const system = [
    `Tu traduis des textes d'interface d'une application bancaire camerounaise vers le ${target}.`,
    "Le texte source est en français ou en anglais.",
    "Règles :",
    "- Conserve chaque marqueur ⟦n⟧ exactement une fois, sans le modifier : il remplace un montant, un numéro, un nom ou une référence.",
    "- Ne change jamais le sens d'une action financière (envoyer, confirmer, annuler) ni la force d'un avertissement de sécurité.",
    "- N'ajoute aucune information absente du texte source.",
    "- Garde un ton simple, compréhensible par une personne peu habituée au vocabulaire bancaire.",
    "- Utilise en priorité la terminologie du glossaire ci-dessous.",
    "",
    "Glossaire (français / anglais = traduction) :",
    ...glossary,
  ].join("\n");

  const body = {
    model: MODEL,
    max_tokens: 4000,
    fallbacks: "default",
    output_config: {
      effort: "low",
      format: {
        type: "json_schema",
        schema: {
          type: "object",
          properties: { translations: { type: "array", items: { type: "string" } } },
          required: ["translations"],
          additionalProperties: false,
        },
      },
    },
    system,
    messages: [
      {
        role: "user",
        content:
          `Traduis chaque élément de ce tableau JSON, dans le même ordre (${texts.length} éléments) :\n` +
          JSON.stringify(texts),
      },
    ],
  };

  const r = await fetch(API_URL, {
    method: "POST",
    headers: {
      "content-type": "application/json",
      "x-api-key": apiKey,
      "anthropic-version": "2023-06-01",
      "anthropic-beta": "server-side-fallback-2026-07-01",
      "anthropic-dangerous-direct-browser-access": "true",
    },
    body: JSON.stringify(body),
  });
  if (!r.ok) return { error: `HTTP ${r.status}` };
  const data = await r.json();
  if (data.stop_reason === "refusal") return { error: "refusal" };
  const text = (data.content || []).find((b) => b.type === "text")?.text;
  if (!text) return { error: "empty" };
  const parsed = JSON.parse(text);
  return { translations: parsed.translations };
}
