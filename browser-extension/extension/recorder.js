// Outil d'enregistrement pour locuteurs natifs. Tout reste local :
// micro -> MediaRecorder -> fichier téléchargé <id>.webm.
const DICT = globalThis.SAFINUM_DICT;
const ITEMS = globalThis.SAFINUM_ITEMS || [];
const $ = (id) => document.getElementById(id);
const takes = new Map(); // `${lang}|${id}` -> Blob
let recorder = null;
let recordingBtn = null;

for (const l of DICT.languages) $("lang").append(new Option(l.selectorLabel || l.label, l.code));
$("lang").onchange = render;
$("todo").onchange = render;
render();

function render() {
  const lang = $("lang").value;
  const existing = DICT.audio?.[lang] || {};
  const list = ITEMS.filter((it) => it[lang] && !($("todo").checked && existing[it.id]));
  const done = ITEMS.filter((it) => it[lang] && existing[it.id]).length;
  const total = ITEMS.filter((it) => it[lang]).length;
  $("count").textContent = `${done} / ${total} déjà dans l'extension`;
  const meta = DICT.languages.find((l) => l.code === lang);
  $("notice").textContent = total === 0
    ? `Aucun texte traduit n’est disponible pour ${meta?.label || lang}. Les traductions doivent d’abord être préparées puis validées localement.`
    : "Les traductions affichées sont des brouillons; faites-les vérifier par des locuteurs natifs avant d’enregistrer ou de diffuser la prononciation.";
  const tbody = $("rows");
  tbody.replaceChildren();
  for (const it of list) {
    const tr = document.createElement("tr");
    const cell = (cls, text) => {
      const td = document.createElement("td");
      td.className = cls;
      td.textContent = text;
      tr.append(td);
      return td;
    };
    cell("id", it.id);
    cell("fr", it.fr);
    const t = cell("tr", it[lang]);
    t.lang = DICT.languages.find((l) => l.code === lang)?.htmlLang || "";
    const act = cell("act", "");
    const key = `${lang}|${it.id}`;

    const rec = button("⏺ Enregistrer", "rec", () => toggleRecord(rec, key, play, dl));
    const play = button("▶", "", () => new Audio(URL.createObjectURL(takes.get(key))).play());
    play.setAttribute("aria-label", `Écouter ${it.id}`);
    const dl = button("⬇", "", () => download(takes.get(key), `${it.id}.webm`));
    dl.setAttribute("aria-label", `Télécharger ${it.id}.webm`);
    play.disabled = dl.disabled = !takes.has(key);
    act.append(rec, play, dl);
    if (existing[it.id]) {
      const ok = document.createElement("div");
      ok.className = "ok";
      ok.textContent = `✓ déjà dans l'extension (${existing[it.id]})`;
      act.append(ok);
    }
    tbody.append(tr);
  }
}

function button(label, cls, onclick) {
  const b = document.createElement("button");
  b.type = "button";
  b.textContent = label;
  b.className = cls;
  b.onclick = onclick;
  return b;
}

async function toggleRecord(btn, key, play, dl) {
  if (recorder && recordingBtn === btn) return recorder.stop();
  if (recorder) recorder.stop(); // une seule prise à la fois
  let stream;
  try {
    stream = await navigator.mediaDevices.getUserMedia({ audio: { echoCancellation: true, noiseSuppression: true } });
  } catch {
    alert("Micro inaccessible : autorisez le micro pour cette page.");
    return;
  }
  const chunks = [];
  const r = new MediaRecorder(stream, { mimeType: "audio/webm;codecs=opus" });
  r.ondataavailable = (e) => e.data.size && chunks.push(e.data);
  r.onstop = () => {
    stream.getTracks().forEach((t) => t.stop());
    takes.set(key, new Blob(chunks, { type: "audio/webm" }));
    btn.textContent = "⏺ Refaire";
    btn.classList.remove("on");
    play.disabled = dl.disabled = false;
    if (recorder === r) recorder = recordingBtn = null;
  };
  recorder = r;
  recordingBtn = btn;
  btn.textContent = "⏹ Arrêter";
  btn.classList.add("on");
  r.start();
}

function download(blob, name) {
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = name;
  a.click();
  setTimeout(() => URL.revokeObjectURL(a.href), 1000);
}
