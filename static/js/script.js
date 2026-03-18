console.log("NeuralFace AI Dashboard Loaded");
 
// ── Emotion metadata ──────────────────────────────────────────
const EMOTION_META = {
  "Happy":    { icon: "😄", detail: "You look happy and joyful! Keep smiling 😊", cls: "emo-happy" },
  "Sad":      { icon: "😢", detail: "You seem sad. It's okay — stay strong 💙", cls: "emo-sad" },
  "Angry":    { icon: "😠", detail: "You look angry. Take a deep breath 🌬️", cls: "emo-angry" },
  "Surprise": { icon: "😲", detail: "You look totally surprised!", cls: "emo-surprise" },
  "Fear":     { icon: "😨", detail: "You look a little scared. You're safe here 🛡️", cls: "emo-fear" },
  "Disgust":  { icon: "🤢", detail: "You look disgusted by something!", cls: "emo-disgust" },
  "Neutral":  { icon: "😐", detail: "You look calm and composed 🧘", cls: "emo-neutral" },
};
 
const EMOTION_LABELS = ["Angry","Disgust","Fear","Happy","Sad","Surprise","Neutral"];
 
// ── State ─────────────────────────────────────────────────────
let polling = null;
let frameCount = 0;
let active = false;
 
// ── Particles ─────────────────────────────────────────────────
function spawnParticles() {
  const container = document.getElementById('particles');
  for (let i = 0; i < 28; i++) {
    const p = document.createElement('div');
    p.className = 'particle';
    p.style.left = Math.random() * 100 + 'vw';
    p.style.bottom = '-4px';
    p.style.animationDuration = (6 + Math.random() * 12) + 's';
    p.style.animationDelay = (Math.random() * 10) + 's';
    p.style.width = p.style.height = (1 + Math.random() * 2) + 'px';
    p.style.opacity = (0.2 + Math.random() * 0.5);
    container.appendChild(p);
  }
}
spawnParticles();
 
// ── Camera control ────────────────────────────────────────────
function startCamera() {
  const videoFeed     = document.getElementById('videoFeed');
  const placeholder   = document.getElementById('placeholder');
  const btnStart      = document.getElementById('btnStart');
  const btnStop       = document.getElementById('btnStop');
  const statusDot     = document.getElementById('statusDot');
  const statusLabel   = document.getElementById('statusLabel');
  const feedScanline  = document.getElementById('feedScanline');
 
  videoFeed.src = '/video?' + Date.now();   // cache-bust
  videoFeed.style.display = 'block';
  placeholder.style.display = 'none';
  btnStart.style.display = 'none';
  btnStop.style.display = 'flex';
  feedScanline.style.display = 'block';
 
  statusDot.classList.add('online');
  statusLabel.textContent = 'LIVE';
  statusLabel.style.color = 'var(--green)';
 
  active = true;
  startPolling();
}
 
function stopCamera() {
  const videoFeed     = document.getElementById('videoFeed');
  const placeholder   = document.getElementById('placeholder');
  const btnStart      = document.getElementById('btnStart');
  const btnStop       = document.getElementById('btnStop');
  const statusDot     = document.getElementById('statusDot');
  const statusLabel   = document.getElementById('statusLabel');
  const feedScanline  = document.getElementById('feedScanline');
 
  videoFeed.src = '';
  videoFeed.style.display = 'none';
  placeholder.style.display = 'flex';
  btnStart.style.display = 'flex';
  btnStop.style.display = 'none';
  feedScanline.style.display = 'none';
 
  statusDot.classList.remove('online');
  statusLabel.textContent = 'OFFLINE';
  statusLabel.style.color = '';
 
  active = false;
  stopPolling();
  resetUI();
}
 
// ── Emotion polling ───────────────────────────────────────────
function startPolling() {
  if (polling) return;
  polling = setInterval(fetchEmotion, 300);
}
 
function stopPolling() {
  if (polling) { clearInterval(polling); polling = null; }
}
 
async function fetchEmotion() {
  if (!active) return;
  try {
    const res = await fetch('/emotion_data');
    if (!res.ok) return;
    const data = await res.json();
    updateEmotion(data);
    frameCount++;
    document.getElementById('frameCount').textContent = frameCount;
  } catch (e) {
    // Silently ignore — camera may be initializing
  }
}
 
// ── Update UI ─────────────────────────────────────────────────
function updateEmotion(data) {
  const emotion   = data.emotion;
  const scores    = data.scores;       // { Angry: 0.12, Happy: 0.75, … }
  const meta      = EMOTION_META[emotion] || {};
 
  // Icon & label
  const icon    = document.getElementById('emotionIcon');
  const label   = document.getElementById('emotionLabel');
  const detail  = document.getElementById('emotionDetail');
  const display = document.getElementById('emotionDisplay');
 
  // Bounce animation
  icon.style.transform = 'scale(1.4)';
  setTimeout(() => { icon.style.transform = ''; }, 300);
 
  icon.textContent   = meta.icon   || '🤖';
  label.textContent  = emotion.toUpperCase();
  detail.textContent = meta.detail || '';
 
  // Remove old emo class
  display.className = 'emotion-display ' + (meta.cls || '');
 
  // Confidence bars
  if (scores) {
    EMOTION_LABELS.forEach(em => {
      const row  = document.querySelector(`.bar-row[data-emotion="${em}"]`);
      if (!row) return;
      const pct  = Math.round((scores[em] || 0) * 100);
      const fill = row.querySelector('.bar-fill');
      const val  = row.querySelector('.bar-val');
      fill.style.width = pct + '%';
      val.textContent  = pct + '%';
 
      // Highlight the active bar
      fill.style.background = em === emotion
        ? 'linear-gradient(90deg, #00e5ff, #00ff9d)'
        : 'linear-gradient(90deg, #1a3a55, #1e4060)';
    });
  }
}
 
function resetUI() {
  document.getElementById('emotionIcon').textContent   = '—';
  document.getElementById('emotionLabel').textContent  = 'AWAITING INPUT';
  document.getElementById('emotionDetail').textContent = 'Start the camera to detect emotions in real time.';
  document.getElementById('emotionDisplay').className  = 'emotion-display';
  EMOTION_LABELS.forEach(em => {
    const row  = document.querySelector(`.bar-row[data-emotion="${em}"]`);
    if (!row) return;
    row.querySelector('.bar-fill').style.width  = '0%';
    row.querySelector('.bar-val').textContent   = '0%';
  });
  frameCount = 0;
  document.getElementById('frameCount').textContent = '0';
}