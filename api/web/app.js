const API = '/api/v1';
const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => [...document.querySelectorAll(selector)];
const demoPhraseKeys = ['balance_label', 'balance_account', 'welcome_subtitle', 'send_money', 'transfer_confirmation'];
let currentLocale = 'fr';
let catalog = {};
let languages = [];
let recorder = null;
let recordingBlob = null;
let recordingStream = null;
let toastTimer = null;

async function apiFetch(url, options = {}) {
  const response = await fetch(url, options);
  const contentType = response.headers.get('content-type') || '';
  const data = contentType.includes('application/json') ? await response.json() : null;
  if (!response.ok) {
    const detail = data?.detail;
    throw new Error(typeof detail === 'string' ? detail : detail?.message || `HTTP ${response.status}`);
  }
  return data;
}

function showToast(message) {
  const toast = $('#toast');
  toast.textContent = message;
  toast.classList.add('is-visible');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toast.classList.remove('is-visible'), 3400);
}

function text(key, fallback = '') {
  return catalog[key] || fallback || key;
}

async function applyLocale(locale) {
  const data = await apiFetch(`${API}/catalog/${locale}`);
  if (!data.supported) return;
  currentLocale = locale;
  catalog = data.items;
  document.documentElement.lang = locale;
  document.title = catalog.app_name || document.title;
  $$('[data-i18n]').forEach((node) => {
    const value = text(node.dataset.i18n);
    if (value) node.textContent = value;
  });
  $$('[data-i18n-aria-label]').forEach((node) => {
    const value = text(node.dataset.i18nAriaLabel);
    if (value) node.setAttribute('aria-label', value);
  });
  $$('[data-i18n-placeholder]').forEach((node) => {
    const value = text(node.dataset.i18nPlaceholder);
    if (value) node.placeholder = value;
  });
  $$('.lang-button').forEach((button) => {
    const selected = button.dataset.locale === locale;
    button.classList.toggle('is-selected', selected);
    button.setAttribute('aria-pressed', String(selected));
  });
  renderPhraseOptions();
  updateLocalStatus();
  updateVoiceSource();
  const output = $('#api-output');
  if (output && !output.dataset.hasResult) output.textContent = locale === 'fr' ? 'Sélectionnez une phrase puis lancez le test.' : 'Choose a phrase and run the test.';
}

function renderPhraseOptions() {
  const selects = [$('#test-phrase'), $('#contribution-phrase')];
  for (const select of selects) {
    const previous = select.value;
    select.replaceChildren();
    demoPhraseKeys.forEach((key) => {
      if (!catalog[key]) return;
      const option = document.createElement('option');
      option.value = key;
      option.textContent = catalog[key];
      select.append(option);
    });
    if (demoPhraseKeys.includes(previous)) select.value = previous;
  }
}

function selectedLanguage() {
  return languages.find((item) => item.code === $('#local-language').value);
}

function updateLocalStatus() {
  const item = selectedLanguage();
  if (!item) return;
  const prefix = currentLocale === 'fr'
    ? `Langue pilote : ${item.name}. `
    : `Pilot language: ${item.name}. `;
  const line = currentLocale === 'fr'
    ? 'Les propositions restent en revue et ne sont pas encore servies comme traductions bancaires.'
    : 'Suggestions remain under review and are not yet served as banking translations.';
  $('#local-status').lastElementChild.textContent = prefix + line;
  $('#api-status').textContent = '';
}

function updateVoiceSource() {
  const key = $('#test-phrase')?.value || 'welcome_subtitle';
  $('#voice-source-text').textContent = catalog[key] || catalog.welcome_subtitle || '';
}

async function loadLanguages() {
  const response = await apiFetch(`${API}/languages`);
  languages = response.items;
  const select = $('#local-language');
  languages.forEach((item) => {
    const option = document.createElement('option');
    option.value = item.code;
    option.textContent = `${item.name} · ${item.regions.join(', ')}`;
    select.append(option);
  });
  updateLocalStatus();
}

async function testTranslation() {
  const targetLocale = $('#local-language').value;
  const phraseKey = $('#test-phrase').value;
  const sourceText = catalog[phraseKey];
  const output = $('#api-output');
  const status = $('#api-status');
  output.textContent = currentLocale === 'fr' ? 'Test en cours…' : 'Testing…';
  output.dataset.hasResult = 'true';
  status.textContent = '';
  try {
    const result = await apiFetch(`${API}/translate`, {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({source_locale: currentLocale, target_locale: targetLocale, phrase_key: phraseKey, source_text: sourceText})
    });
    output.textContent = result.translation || sourceText;
    status.textContent = result.translated
      ? text('api_ok')
      : `${text('api_review_needed')} ${result.warning || ''}`;
    status.classList.toggle('is-warning', !result.translated);
    status.classList.toggle('is-good', result.translated);
  } catch (error) {
    output.textContent = sourceText;
    status.textContent = error.message;
    status.classList.add('is-warning');
  }
}

async function submitTranslation(event) {
  event.preventDefault();
  const key = $('#contribution-phrase').value;
  const sourceText = catalog[key];
  const languageCode = $('#local-language').value;
  const output = $('#contribution-status');
  output.textContent = currentLocale === 'fr' ? 'Envoi en cours…' : 'Submitting…';
  try {
    const result = await apiFetch(`${API}/contributions/translations`, {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({
        phrase_key: key,
        source_locale: currentLocale,
        target_locale: languageCode,
        source_text: sourceText,
        translated_text: $('#translation-input').value.trim(),
        dialect: $('#dialect-input').value.trim(),
        speaker_role: $('#speaker-role').value,
        consent: $('#translation-consent').checked
      })
    });
    output.textContent = text('contribution_pending');
    $('#translation-input').value = '';
    $('#translation-consent').checked = false;
    showToast(result.message);
  } catch (error) {
    output.textContent = error.message;
    output.classList.add('is-warning');
  }
}

function stopTracks() {
  if (recordingStream) {
    recordingStream.getTracks().forEach((track) => track.stop());
    recordingStream = null;
  }
}

async function toggleRecording() {
  const button = $('#record-button');
  if (recorder && recorder.state === 'recording') {
    recorder.stop();
    return;
  }
  if (!navigator.mediaDevices?.getUserMedia || !window.MediaRecorder) {
    $('#voice-message').textContent = currentLocale === 'fr'
      ? 'L’enregistrement nécessite un navigateur compatible et un accès microphone.'
      : 'Recording requires a compatible browser and microphone access.';
    return;
  }
  try {
    recordingStream = await navigator.mediaDevices.getUserMedia({audio: true});
    const preferred = ['audio/webm;codecs=opus', 'audio/webm', 'audio/ogg;codecs=opus'].find((type) => MediaRecorder.isTypeSupported(type));
    recorder = preferred ? new MediaRecorder(recordingStream, {mimeType: preferred}) : new MediaRecorder(recordingStream);
    const chunks = [];
    recorder.ondataavailable = (event) => { if (event.data.size) chunks.push(event.data); };
    recorder.onstop = () => {
      recordingBlob = new Blob(chunks, {type: recorder.mimeType || 'audio/webm'});
      $('#audio-preview').src = URL.createObjectURL(recordingBlob);
      $('#audio-preview').hidden = false;
      $('#upload-audio').disabled = false;
      button.querySelector('span:first-child').textContent = text('record_start');
      stopTracks();
      $('#voice-message').textContent = currentLocale === 'fr' ? 'Écoutez votre extrait avant de l’envoyer.' : 'Preview your clip before submitting it.';
    };
    recorder.start();
    $('#upload-audio').disabled = true;
    button.querySelector('span:first-child').textContent = text('record_stop');
    $('#voice-message').textContent = currentLocale === 'fr' ? 'Enregistrement en cours… appuyez à nouveau pour terminer.' : 'Recording… press again to finish.';
  } catch (error) {
    stopTracks();
    $('#voice-message').textContent = text('audio_error');
  }
}

async function uploadRecording() {
  if (!recordingBlob) return;
  if (!$('#audio-consent').checked) {
    $('#voice-message').textContent = currentLocale === 'fr' ? 'Cochez le consentement avant l’envoi.' : 'Please provide consent before submitting.';
    return;
  }
  const locale = $('#local-language').value;
  const phraseKey = $('#test-phrase').value;
  const query = new URLSearchParams({
    language_code: locale,
    phrase_key: phraseKey,
    dialect: $('#dialect-input').value.trim(),
    speaker_role: $('#speaker-role').value,
    consent: 'true'
  });
  try {
    const result = await apiFetch(`${API}/contributions/audio?${query}`, {
      method: 'POST',
      headers: {'Content-Type': recordingBlob.type || 'audio/webm'},
      body: recordingBlob
    });
    $('#voice-message').textContent = text('audio_pending');
    $('#audio-consent').checked = false;
    recordingBlob = null;
    $('#upload-audio').disabled = true;
    showToast(result.message);
  } catch (error) {
    $('#voice-message').textContent = error.message;
  }
}

async function playApprovedPronunciation() {
  const locale = $('#local-language').value;
  const phraseKey = $('#test-phrase').value;
  try {
    const response = await fetch(`${API}/pronunciation/${locale}/${phraseKey}`);
    if (!response.ok) throw new Error('missing');
    const audio = new Audio(URL.createObjectURL(await response.blob()));
    await audio.play();
    $('#audio-status').textContent = currentLocale === 'fr' ? 'Extrait validé en cours de lecture.' : 'Approved sample is playing.';
  } catch {
    $('#audio-status').textContent = text('audio_waiting');
  }
}

function simulateTransfer(event) {
  event.preventDefault();
  const recipient = $('#recipient').value.trim();
  const amount = Number($('#amount').value);
  const message = $('#transfer-message');
  if (!recipient || !Number.isFinite(amount) || amount <= 0 || amount > 125000) {
    message.textContent = text('transfer_invalid');
    return;
  }
  message.textContent = text('transfer_success');
  showToast(text('transfer_success'));
  $('#transfer-form').reset();
}

function initNavigation() {
  $$('.rail-link').forEach((link) => link.addEventListener('click', () => {
    $$('.rail-link').forEach((item) => item.classList.toggle('is-active', item === link));
  }));
}

async function init() {
  try {
    await loadLanguages();
    await applyLocale('fr');
    $$('.lang-button').forEach((button) => button.addEventListener('click', () => applyLocale(button.dataset.locale)));
    $('#local-language').addEventListener('change', () => {
      updateLocalStatus();
      testTranslation();
      $('#contribution-status').textContent = '';
      $('#voice-message').textContent = '';
    });
    $('#test-phrase').addEventListener('change', updateVoiceSource);
    $('#contribution-phrase').addEventListener('change', () => {
      const key = $('#contribution-phrase').value;
      $('#test-phrase').value = key;
      updateVoiceSource();
    });
    $('#test-translate').addEventListener('click', testTranslation);
    $('#contribution-form').addEventListener('submit', submitTranslation);
    $('#record-button').addEventListener('click', toggleRecording);
    $('#upload-audio').addEventListener('click', uploadRecording);
    $('#play-approved').addEventListener('click', playApprovedPronunciation);
    $('#transfer-form').addEventListener('submit', simulateTransfer);
    initNavigation();
    testTranslation();
  } catch (error) {
    document.body.insertAdjacentHTML('afterbegin', `<div class="startup-error">${error.message.replace(/[<>]/g, '')}</div>`);
  }
}

document.addEventListener('DOMContentLoaded', init);
