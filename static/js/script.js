/* ─── PARTICLE BACKGROUND ─── */
const canvas = document.getElementById('particles');
const ctx = canvas.getContext('2d');
let particles = [];

function resizeCanvas() {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
}
resizeCanvas();
window.addEventListener('resize', resizeCanvas);

class Particle {
    constructor() { this.reset(); }
    reset() {
        this.x = Math.random() * canvas.width;
        this.y = Math.random() * canvas.height;
        this.size = Math.random() * 1.5 + 0.5;
        this.speedX = (Math.random() - 0.5) * 0.3;
        this.speedY = (Math.random() - 0.5) * 0.3;
        this.opacity = Math.random() * 0.4 + 0.1;
    }
    update() {
        this.x += this.speedX;
        this.y += this.speedY;
        if (this.x < 0 || this.x > canvas.width || this.y < 0 || this.y > canvas.height) this.reset();
    }
    draw() {
        ctx.beginPath();
        ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(56, 189, 248, ${this.opacity})`;
        ctx.fill();
    }
}

for (let i = 0; i < 60; i++) particles.push(new Particle());

function animateParticles() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    particles.forEach(p => { p.update(); p.draw(); });

    for (let i = 0; i < particles.length; i++) {
        for (let j = i + 1; j < particles.length; j++) {
            const dx = particles[i].x - particles[j].x;
            const dy = particles[i].y - particles[j].y;
            const dist = Math.sqrt(dx * dx + dy * dy);
            if (dist < 120) {
                ctx.beginPath();
                ctx.strokeStyle = `rgba(56, 189, 248, ${0.06 * (1 - dist / 120)})`;
                ctx.lineWidth = 0.5;
                ctx.moveTo(particles[i].x, particles[i].y);
                ctx.lineTo(particles[j].x, particles[j].y);
                ctx.stroke();
            }
        }
    }
    requestAnimationFrame(animateParticles);
}
animateParticles();

/* ─── DOM REFS ─── */
const btn = document.getElementById('talk-btn');
const robot = document.getElementById('robot-state');
const instruction = document.getElementById('instruction');
const chatBody = document.getElementById('chat-body');
const resetBtn = document.getElementById('reset-btn');
const clearBtn = document.getElementById('clear-btn');
let isProcessing = false;
let hasGreeted = false;

function addMessage(text, role) {
    const welcomeMsg = chatBody.querySelector('.welcome-msg');
    if (welcomeMsg) welcomeMsg.remove();

    const msg = document.createElement('div');
    msg.className = `msg ${role}`;
    const label = document.createElement('div');
    label.className = 'label';
    label.textContent = role === 'user' ? 'You' : 'AURA';
    msg.appendChild(label);
    msg.appendChild(document.createTextNode(text));
    chatBody.appendChild(msg);
    chatBody.scrollTop = chatBody.scrollHeight;
}

function speak(text, langCode) {
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = langCode || 'en-US';
    utterance.rate = 1.0;
    utterance.pitch = 1.0;
    const voices = window.speechSynthesis.getVoices();
    if (voices.length > 0) {
        const voice = voices.find(v => v.lang.startsWith(utterance.lang.split('-')[0]));
        if (voice) utterance.voice = voice;
    }
    utterance.onend = () => {
        if (window.wakeWordRecognizer && !isProcessing) {
            try { window.wakeWordRecognizer.start(); } catch (e) { }
        }
    };
    window.speechSynthesis.speak(utterance);
}

function speakAndWait(text, langCode) {
    return new Promise(resolve => {
        window.speechSynthesis.cancel();
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.lang = langCode || 'en-US';
        const voices = window.speechSynthesis.getVoices();
        if (voices.length > 0) {
            const voice = voices.find(v => v.lang.startsWith(utterance.lang.split('-')[0]));
            if (voice) utterance.voice = voice;
        }

        utterance.onend = resolve;
        utterance.onerror = resolve;
        setTimeout(resolve, 4000); // Fallback
        window.speechSynthesis.speak(utterance);
    });
}

function setUIState(state) {
    btn.classList.remove('listening', 'thinking');
    if (state === 'listening') {
        btn.classList.add('listening');
        instruction.textContent = '🎙️ Listening...';
    } else if (state === 'thinking') {
        btn.classList.add('thinking');
        instruction.textContent = '⚡ Processing...';
    } else {
        instruction.innerHTML = 'Say "Hey AURA" or Tap · <span class="kbd">Space</span>';
    }
}

/* ─── WAKE WORD ─── */
function initWakeWord() {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) return;

    const wk = new SR();
    wk.continuous = true;
    wk.interimResults = false;
    wk.lang = 'en-US';

    wk.onresult = (e) => {
        if (isProcessing || window.speechSynthesis.speaking) return;
        const t = e.results[e.results.length - 1][0].transcript.toLowerCase().trim();
        console.log("[Wake Word Heard]:", t);

        const wakeWords = ["hey aura", "hi aura", "aura", "ok aura", "okay aura", "wake up aura", "hey bobby"];
        const isWakeWord = wakeWords.some(w => t.includes(w) || t === w);

        if (isWakeWord) {
            wk.stop();
            try {
                const actx = new (window.AudioContext || window.webkitAudioContext)();
                const osc = actx.createOscillator();
                osc.connect(actx.destination);
                osc.frequency.setValueAtTime(800, actx.currentTime);
                osc.start();
                osc.stop(actx.currentTime + 0.1);
            } catch (e) { }
            btn.click();
        }
    };
    wk.onend = () => { if (!isProcessing && !window.speechSynthesis.speaking) { try { wk.start(); } catch (e) { } } };
    wk.onerror = (e) => { if (e.error !== 'aborted') console.log("Wake:", e.error); };
    try { wk.start(); } catch (e) { }
    window.wakeWordRecognizer = wk;
}
initWakeWord();
window.speechSynthesis.getVoices();

/* ─── KEYBOARD ─── */
document.addEventListener('keydown', (e) => {
    if (e.code === 'Space' && !isProcessing && document.activeElement.tagName !== 'INPUT') {
        e.preventDefault();
        btn.click();
    }
});

/* ─── RESET & CLEAR ─── */
resetBtn.addEventListener('click', async () => {
    resetBtn.textContent = '⟳ ...';
    try {
        await fetch('/reset', { method: 'POST' });
        isProcessing = false;
        setUIState('idle');
    } catch (e) { console.error(e); }
    finally { resetBtn.textContent = '⟳ Reset'; }
});

clearBtn.addEventListener('click', () => {
    chatBody.innerHTML = '<div class="welcome-msg">👋 Chat cleared. Tap the robot or say <strong>"Hey AURA"</strong> to start.</div>';
});

/* ─── MAIN INTERACTION ─── */
btn.addEventListener('click', async () => {
    if (isProcessing) return;
    isProcessing = true;

    if (!hasGreeted) {
        hasGreeted = true;
        setUIState('listening');
        instruction.textContent = '🔊 Greeting...';
        await speakAndWait("Hello! Welcome to AURA. How can I assist you today?", 'en-US');
    }

    setUIState('listening');

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 60000);

    // POLL FOR LIVE SPEECH UPDATES (MULTI-TURN SUPPORT)
    const pollInterval = setInterval(async () => {
        if (!isProcessing) {
            clearInterval(pollInterval);
            return;
        }
        try {
            const upResp = await fetch('/updates');
            const upData = await upResp.json();
            if (upData.messages && upData.messages.length > 0) {
                upData.messages.forEach(m => {
                    addMessage(m, 'assistant');
                    speak(m);
                });
                setUIState('listening');
            }
        } catch (e) { }
    }, 1000);

    try {
        const resp = await fetch('/listen', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            signal: controller.signal
        });

        clearInterval(pollInterval);

        if (resp.status === 400) {
            const d = await resp.json();
            addMessage(d.message, 'assistant');
            isProcessing = false;
            setUIState('idle');
            return;
        }

        setUIState('thinking');
        const data = await resp.json();
        clearTimeout(timeoutId);

        if (data.status === 'success') {
            if (data.command) addMessage(data.command, 'user');

            if (data.response && data.response !== "Command processed.") {
                const existingMsgs = Array.from(chatBody.querySelectorAll('.msg.assistant')).map(m => m.textContent.replace('AURA', '').trim());
                if (!existingMsgs.includes(data.response.trim())) {
                    addMessage(data.response, 'assistant');
                    speak(data.response, data.lang_code);
                }
            }
        } else {
            addMessage("Error: " + data.message, 'assistant');
        }
    } catch (err) {
        addMessage(err.name === 'AbortError' ? 'Connection timed out.' : 'System error. Please try again.', 'assistant');
    } finally {
        isProcessing = false;
        setUIState('idle');
        if (window.wakeWordRecognizer && !window.speechSynthesis.speaking) {
            try { window.wakeWordRecognizer.start(); } catch (e) { }
        }
    }
});
