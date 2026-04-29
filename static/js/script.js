'use strict';

const CONFIG = {
  pollInterval: 1000,
  listenTimeout: 90000,
  wakeWords: ['hey aura', 'hi aura', 'aura', 'ok aura', 'okay aura', 'wake up aura'],
  ttsRate: 1.05,
  ttsPitch: 1.0,
};

const Particles = (() => {
  const canvas = document.getElementById('particles');
  const ctx = canvas.getContext('2d');
  let items = [];

  function resize() {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
  }

  class Particle {
    constructor() { this.reset(); }
    reset() {
      this.x = Math.random() * canvas.width;
      this.y = Math.random() * canvas.height;
      this.size = Math.random() * 1.4 + 0.4;
      this.vx = (Math.random() - 0.5) * 0.22;
      this.vy = (Math.random() - 0.5) * 0.22;
      this.opacity = Math.random() * 0.35 + 0.08;
      this.hue = Math.random() > 0.5 ? `249,115,22` : `192,132,252`;
    }
    update() {
      this.x += this.vx;
      this.y += this.vy;
      if (this.x < 0 || this.x > canvas.width || this.y < 0 || this.y > canvas.height) {
        this.reset();
      }
    }
    draw() {
      ctx.beginPath();
      ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(${this.hue},${this.opacity})`;
      ctx.fill();
    }
  }

  function init() {
    resize();
    for (let i = 0; i < 55; i++) items.push(new Particle());
    window.addEventListener('resize', resize);
    animate();
  }

  function animate() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    items.forEach(p => { p.update(); p.draw(); });

    for (let i = 0; i < items.length; i++) {
      for (let j = i + 1; j < items.length; j++) {
        const dx = items[i].x - items[j].x;
        const dy = items[i].y - items[j].y;
        const dist = Math.hypot(dx, dy);
        if (dist < 110) {
          ctx.beginPath();
          ctx.strokeStyle = `rgba(249,115,22,${0.055 * (1 - dist / 110)})`;
          ctx.lineWidth = 0.5;
          ctx.moveTo(items[i].x, items[i].y);
          ctx.lineTo(items[j].x, items[j].y);
          ctx.stroke();
        }
      }
    }
    requestAnimationFrame(animate);
  }

  return { init };
})();

const Robot = (() => {
  const wrapper   = document.getElementById('talk-btn');
  const robotEl   = document.getElementById('robot-state');
  const statusEl  = document.getElementById('instruction');
  const waveform  = document.getElementById('waveform');
  let currentState = 'idle';

  const eyeLeft  = document.getElementById('eye-left');
  const eyeRight = document.getElementById('eye-right');

  document.addEventListener('mousemove', (e) => {
    if (currentState !== 'idle') return;
    [eyeLeft, eyeRight].forEach(eye => {
      if (!eye) return;
      const rect = eye.getBoundingClientRect();
      const cx = rect.left + rect.width / 2;
      const cy = rect.top + rect.height / 2;
      const angle = Math.atan2(e.clientY - cy, e.clientX - cx);
      const dist = Math.min(5, Math.hypot(e.clientX - cx, e.clientY - cy) * 0.08);
      const pupil = eye.querySelector('.pupil');
      if (pupil) {
        pupil.style.transform = `translate(${Math.cos(angle) * dist}px, ${Math.sin(angle) * dist}px)`;
      }
    });
  });

  function setState(state) {
    currentState = state;
    robotEl.className = 'dog-robot';
    wrapper.setAttribute('aria-pressed', state === 'listening' ? 'true' : 'false');

    switch (state) {
      case 'listening':
        robotEl.classList.add('listening');
        statusEl.textContent = '🎙️ Listening…';
        wrapper.classList.add('listening');
        wrapper.classList.remove('thinking');
        waveform.classList.remove('active');
        break;
      case 'thinking':
        robotEl.classList.add('thinking');
        wrapper.classList.add('thinking');
        wrapper.classList.remove('listening');
        statusEl.textContent = '⚡ Processing…';
        waveform.classList.remove('active');
        break;
      case 'speaking':
        robotEl.classList.add('speaking');
        wrapper.classList.remove('listening', 'thinking');
        statusEl.textContent = '🔊 Speaking…';
        waveform.classList.add('active');
        break;
      default:
        wrapper.classList.remove('listening', 'thinking');
        statusEl.innerHTML = 'Tap the dog or press <kbd class="kbd">Space</kbd>';
        waveform.classList.remove('active');
        [eyeLeft, eyeRight].forEach(eye => {
          if (eye) {
            const p = eye.querySelector('.pupil');
            if (p) p.style.transform = '';
          }
        });
        break;
    }
  }

  return { setState, wrapper };
})();

const Chat = (() => {
  const body = document.getElementById('chat-body');

  function addMessage(text, role) {
    const welcome = body.querySelector('.welcome-msg');
    if (welcome) welcome.remove();

    const msg = document.createElement('div');
    msg.className = `msg ${role}`;

    const label = document.createElement('div');
    label.className = 'label';
    label.textContent = role === 'user' ? 'You' : 'AURA';

    const content = document.createElement('span');
    content.textContent = text;

    msg.appendChild(label);
    msg.appendChild(content);
    body.appendChild(msg);
    body.scrollTop = body.scrollHeight;
  }

  function addPlaceholder(role) {
    const welcome = body.querySelector('.welcome-msg');
    if (welcome) welcome.remove();

    const msg = document.createElement('div');
    msg.className = `msg ${role} placeholder`;

    const label = document.createElement('div');
    label.className = 'label';
    label.textContent = role === 'user' ? 'You' : 'AURA';

    const content = document.createElement('span');
    content.innerHTML = '<span class="typing-dots"><span>.</span><span>.</span><span>.</span></span>';

    msg.appendChild(label);
    msg.appendChild(content);
    body.appendChild(msg);
    body.scrollTop = body.scrollHeight;
    return msg;
  }

  function updatePlaceholder(placeholder, text) {
    if (!placeholder) return;
    const content = placeholder.querySelector('span');
    if (content) {
      content.textContent = text;
      placeholder.classList.remove('placeholder');
    }
  }

  function clear() {
    body.innerHTML = `
      <div class="welcome-msg">
        <div class="welcome-icon">🐶</div>
        <strong>Chat cleared.</strong><br />
        Tap me or say <strong>"Hey AURA"</strong> to start again.
      </div>`;
  }

  function isDuplicate(text) {
    const msgs = Array.from(body.querySelectorAll('.msg.assistant span'));
    return msgs.some(m => m.textContent.trim() === text.trim());
  }

  return { addMessage, addPlaceholder, updatePlaceholder, clear, isDuplicate };
})();

const Voice = (() => {
  let speaking = false;

  function _getBestVoice(lang) {
    const voices = window.speechSynthesis.getVoices();
    const langCode = (lang || 'en').split('-')[0];
    return voices.find(v => v.lang.startsWith(langCode)) || null;
  }

  function speak(text, lang) {
    if (!text) return;
    try {
      window.speechSynthesis.cancel();
      speaking = true;
      Robot.setState('speaking');

      const utt = new SpeechSynthesisUtterance(text);
      utt.lang  = lang || 'en-US';
      utt.rate  = CONFIG.ttsRate;
      utt.pitch = CONFIG.ttsPitch;
      const voice = _getBestVoice(utt.lang);
      if (voice) utt.voice = voice;

      utt.onend = () => {
        speaking = false;
        if (!isProcessing) {
          Robot.setState('idle');
          WakeWord.safeStart();
        }
      };
      
      utt.onerror = (e) => {
        console.error('[Voice] Error:', e);
        speaking = false;
        if (!isProcessing) Robot.setState('idle');
      };

      setTimeout(() => window.speechSynthesis.speak(utt), 50);
    } catch (err) {
      console.error('[Voice] critical error:', err);
    }
  }

  function speakAndWait(text, lang) {
    return new Promise(resolve => {
      window.speechSynthesis.cancel();
      const utt = new SpeechSynthesisUtterance(text);
      utt.lang  = lang || 'en-US';
      utt.rate  = CONFIG.ttsRate;
      const voice = _getBestVoice(utt.lang);
      if (voice) utt.voice = voice;
      utt.onend = utt.onerror = resolve;
      setTimeout(resolve, 5000);
      window.speechSynthesis.speak(utt);
    });
  }

  function isSpeaking() { return speaking || window.speechSynthesis.speaking; }

  return { speak, speakAndWait, isSpeaking };
})();

const API = (() => {
  async function listen(signal) {
    let coords = null;
    if ("geolocation" in navigator) {
      try {
        coords = await new Promise((resolve) => {
          navigator.geolocation.getCurrentPosition(
            p => resolve({ lat: p.coords.latitude, lon: p.coords.longitude }),
            () => resolve(null),
            { timeout: 5000, maximumAge: 60000 }
          );
        });
      } catch (e) {}
    }

    const payload = coords ? JSON.stringify(coords) : '{}';

    const resp = await fetch('/listen', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: payload,
      signal,
    });
    return resp;
  }

  async function reset() {
    return fetch('/reset', { method: 'POST' });
  }

  async function updates() {
    const resp = await fetch('/updates');
    return resp.json();
  }

  async function status() {
    try {
      const resp = await fetch('/status');
      return resp.json();
    } catch { return { db: 'disconnected' }; }
  }

  async function flushUpdates() {
    try {
      const { messages } = await updates();
      if (messages?.length) {
        messages.forEach(m => {
          Chat.addMessage(m, 'assistant');
          Voice.speak(m);
        });
      }
    } catch (_) { }
  }

  async function command(text, coords) {
    const payload = { command: text };
    if (coords) {
      payload.lat = coords.lat;
      payload.lon = coords.lon;
    }
    const resp = await fetch('/command', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    return resp.json();
  }

  async function triggerSOS(coords) {
    const opts = { method: 'POST', headers: { 'Content-Type': 'application/json' } };
    if (coords) opts.body = JSON.stringify(coords);
    const resp = await fetch('/sos', opts);
    return resp.json();
  }

  return { listen, reset, updates, status, command, triggerSOS, flushUpdates };
})();

const WakeWord = (() => {
  let recognizer = null;

  function init() {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) return;

    recognizer = new SR();
    recognizer.continuous = true;
    recognizer.interimResults = false;
    recognizer.lang = 'en-US';

    recognizer.onresult = (e) => {
      if (isProcessing || Voice.isSpeaking()) return;
      const t = e.results[e.results.length - 1][0].transcript.toLowerCase().trim();
      const isWake = CONFIG.wakeWords.some(w => t.includes(w));
      if (isWake) {
        recognizer.stop();
        _beep();
        Robot.wrapper.click();
      }
    };

    recognizer.onend = () => {
      if (!isProcessing && !Voice.isSpeaking()) safeStart();
    };

    recognizer.onerror = (e) => {
      if (e.error !== 'aborted') console.warn('[Wake]', e.error);
    };

    safeStart();
  }

  function safeStart() {
    if (!recognizer) return;
    try { recognizer.start(); } catch (_) { }
  }

  function safeStop() {
    if (!recognizer) return;
    try { recognizer.stop(); } catch (_) { }
  }

  function _beep() {
    try {
      const ac = new (window.AudioContext || window.webkitAudioContext)();
      const osc = ac.createOscillator();
      const gain = ac.createGain();
      osc.connect(gain);
      gain.connect(ac.destination);
      osc.frequency.value = 880;
      gain.gain.setValueAtTime(0.4, ac.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, ac.currentTime + 0.15);
      osc.start();
      osc.stop(ac.currentTime + 0.15);
    } catch (_) { }
  }

  return { init, safeStart, safeStop };
})();

const A11y = (() => {
  const body = document.body;
  const fontBtns = {
    sm: document.getElementById('font-sm-btn'),
    md: document.getElementById('font-md-btn'),
    lg: document.getElementById('font-lg-btn'),
  };
  const contrastBtn = document.getElementById('contrast-btn');

  function setFont(size) {
    body.dataset.fontSize = size;
    Object.values(fontBtns).forEach(b => b?.classList.remove('active'));
    const map = { normal: fontBtns.sm, large: fontBtns.md, xlarge: fontBtns.lg };
    map[size]?.classList.add('active');
    localStorage.setItem('aura-font', size);
  }

  function toggleContrast() {
    const high = body.dataset.contrast === 'high';
    body.dataset.contrast = high ? 'normal' : 'high';
    contrastBtn?.classList.toggle('active', !high);
    localStorage.setItem('aura-contrast', body.dataset.contrast);
  }

  function restore() {
    setFont(localStorage.getItem('aura-font') || 'normal');
    if (localStorage.getItem('aura-contrast') === 'high') toggleContrast();
  }

  function init() {
    restore();
  }

  return { init };
})();

let isProcessing = false;
let hasGreeted   = false;
let pollTimer    = null;

async function startListening() {
  if (isProcessing) return;
  isProcessing = true;
  WakeWord.safeStop();

  if (!hasGreeted) {
    hasGreeted = true;
    Robot.setState('speaking');
    await Voice.speakAndWait("Hello! I'm AURA, your voice assistant. How can I help you today?");
  }

  Robot.setState('listening');
  const userPlaceholder = Chat.addPlaceholder('user');

  pollTimer = setInterval(async () => {
    if (!isProcessing) { clearInterval(pollTimer); return; }
    try {
      const { messages } = await API.updates();
      if (messages?.length) {
        messages.forEach(m => {
          Chat.addMessage(m, 'assistant');
          Voice.speak(m);
        });
        Robot.setState('listening');
      }
    } catch (_) { }
  }, CONFIG.pollInterval);

  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), CONFIG.listenTimeout);

  try {
    const resp = await API.listen(controller.signal);
    clearInterval(pollTimer);
    await API.flushUpdates();

    if (resp.status === 429) {
      const d = await resp.json();
      Chat.updatePlaceholder(userPlaceholder, '...');
      Chat.addMessage(d.message, 'assistant');
      done();
      return;
    }

    Robot.setState('thinking');
    const data = await resp.json();
    clearTimeout(timeout);

    if (data.status === 'success') {
      if (data.command) {
        Chat.updatePlaceholder(userPlaceholder, data.command);
      } else {
        Chat.updatePlaceholder(userPlaceholder, '...');
      }

      const response = data.response;
      if (response && response !== 'Command processed.') {
        if (!Chat.isDuplicate(response)) {
          Chat.addMessage(response, 'assistant');
          Voice.speak(response, data.lang_code);
          done();
          return;
        }
      }
    } else {
      Chat.updatePlaceholder(userPlaceholder, '...');
      if (data.message) Chat.addMessage('Error: ' + data.message, 'assistant');
    }

  } catch (err) {
    clearInterval(pollTimer);
    await API.flushUpdates();
    Chat.updatePlaceholder(userPlaceholder, '...');
    if (err.name === 'AbortError') {
      Chat.addMessage('Connection timed out. Please try again.', 'assistant');
    } else {
      Chat.addMessage('Something went wrong. Please try again.', 'assistant');
      console.error('[AURA]', err);
    }
  }

  done();
}

function done() {
  isProcessing = false;
  if (!Voice.isSpeaking()) Robot.setState('idle');
  WakeWord.safeStart();
}

async function sendTextCommand(cmdText, labelText) {
  if (isProcessing) return;
  isProcessing = true;
  WakeWord.safeStop();
  Chat.addMessage(labelText || cmdText, 'user');
  Robot.setState('thinking');

  let coords = null;
  if ("geolocation" in navigator) {
    try {
      coords = await new Promise((resolve) => {
        navigator.geolocation.getCurrentPosition(
          p => resolve({ lat: p.coords.latitude, lon: p.coords.longitude }),
          () => resolve(null),
          { timeout: 5000, maximumAge: 60000 }
        );
      });
    } catch (e) {}
  }

  let pollTimer;
  pollTimer = setInterval(async () => {
    if (!isProcessing) { clearInterval(pollTimer); return; }
    try {
      const { messages } = await API.updates();
      if (messages?.length) {
        messages.forEach(m => {
          Chat.addMessage(m, 'assistant');
          Voice.speak(m);
        });
        Robot.setState('listening');
      }
    } catch (_) { }
  }, CONFIG.pollInterval);

  try {
    const data = await API.command(cmdText, coords);
    clearInterval(pollTimer);
    await API.flushUpdates();
    if (data.status === 'success' && data.response) {
      const response = data.response;
      if (response && response !== 'Command processed.') {
        if (!Chat.isDuplicate(response)) {
          Chat.addMessage(response, 'assistant');
          Voice.speak(response, data.lang_code);
        }
      }
    }
  } catch (err) {
    clearInterval(pollTimer);
    await API.flushUpdates();
    Chat.addMessage('Command failed. Please try again.', 'assistant');
    console.error('[AURA chip]', err);
  }
  done();
}

document.querySelectorAll('.chip').forEach(chip => {
  chip.addEventListener('click', () => {
    const cmd = chip.dataset.cmd;
    if (cmd) sendTextCommand(cmd);
  });
});

document.getElementById('sos-btn')?.addEventListener('click', async () => {
  if (isProcessing) return;
  isProcessing = true;
  WakeWord.safeStop();
  Chat.addMessage('🚨 Emergency SOS activated! Locating...', 'user');
  Robot.setState('thinking');

  let coords = null;
  if ('geolocation' in navigator) {
    try {
      coords = await new Promise((resolve, reject) => {
        navigator.geolocation.getCurrentPosition(
          pos => resolve({ lat: pos.coords.latitude, lon: pos.coords.longitude }),
          err => resolve(null),
          { timeout: 5000, maximumAge: 0, enableHighAccuracy: true }
        );
      });
    } catch (_) {}
  }

  try {
    const data = await API.triggerSOS(coords);
    const msg = data.response || 'SOS sent to your emergency contact.';
    Chat.addMessage(msg, 'assistant');
    Voice.speak(msg);
    done();
    return;
  } catch (err) {
    Chat.addMessage('SOS failed. Please check your connection.', 'assistant');
    console.error('[AURA SOS]', err);
  }
  done();
});

Robot.wrapper.addEventListener('click', startListening);
Robot.wrapper.addEventListener('keydown', e => {
  if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); startListening(); }
});

document.addEventListener('keydown', (e) => {
  if (e.code === 'Space' && !isProcessing &&
      document.activeElement.tagName !== 'INPUT' &&
      document.activeElement.tagName !== 'TEXTAREA') {
    e.preventDefault();
    startListening();
  }
});

document.getElementById('reset-btn')?.addEventListener('click', async () => {
  const btn = document.getElementById('reset-btn');
  if (btn) btn.textContent = '⟳ …';
  try {
    await API.reset();
    isProcessing = false;
    Robot.setState('idle');
  } catch (_) { }
  if (btn) btn.innerHTML = '⟳ Reset';
});

document.getElementById('clear-btn')?.addEventListener('click', () => Chat.clear());

(function init() {
  Particles.init();
  A11y.init();
  WakeWord.init();
  window.speechSynthesis.getVoices();
  window.speechSynthesis.addEventListener?.('voiceschanged', () => window.speechSynthesis.getVoices());
  console.info('%c🐾 AURA v2.0 — Voice Assistant for Visually Impaired', 'color:#f97316;font-weight:bold;font-size:14px;');
})();
