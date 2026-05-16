const BACKEND = 'http://127.0.0.1:8000';

let modoEntrada = 'texto', modoRespuesta = 'texto';
let imagenSeleccionada = null;
let mediaRecorder = null, audioChunks = [], grabando = false;

function setModo(modo, btn) {
    modoEntrada = modo;
    btn.closest('.control-group').querySelectorAll('.mode-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
}

function setRespuesta(modo, btn) {
    modoRespuesta = modo;
    btn.closest('.control-group').querySelectorAll('.mode-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
}

function handleImageSelect(e) {
    const file = e.target.files[0];
    if (!file) return;
    imagenSeleccionada = file;
    const reader = new FileReader();
    reader.onload = ev => {
        document.getElementById('image-preview').src = ev.target.result;
        document.getElementById('image-name').textContent = file.name;
        document.getElementById('image-preview-wrap').style.display = 'flex';
    };
    reader.readAsDataURL(file);
}

function removeImage() {
    imagenSeleccionada = null;
    document.getElementById('file-input').value = '';
    document.getElementById('image-preview-wrap').style.display = 'none';
}

async function toggleRecording() {
    if (!grabando) {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            audioChunks = [];
            mediaRecorder = new MediaRecorder(stream);
            mediaRecorder.ondataavailable = e => audioChunks.push(e.data);
            mediaRecorder.onstop = async () => {
                const blob = new Blob(audioChunks, { type: 'audio/webm' });
                await procesarAudio(blob);
                stream.getTracks().forEach(t => t.stop());
            };
            mediaRecorder.start();
            grabando = true;
            document.getElementById('mic-btn').classList.add('recording');
            document.getElementById('recording-indicator').style.display = 'flex';
        } catch (e) { alert('Micrófono no disponible: ' + e.message); }
    } else {
        mediaRecorder.stop(); grabando = false;
        document.getElementById('mic-btn').classList.remove('recording');
        document.getElementById('recording-indicator').style.display = 'none';
    }
}

async function procesarAudio(blob) {
    const formData = new FormData();
    formData.append('audio', blob, 'audio.webm');
    showTyping();
    try {
        const res = await fetch(`${BACKEND}/voice/transcribe`, { method: 'POST', body: formData });
        const data = await res.json();
        removeTyping();
        addTranscripcion(data.texto);
        document.getElementById('msg-input').value = data.texto;
        autoResize(document.getElementById('msg-input'));
        await enviarTextoAlAgente(data.texto);
    } catch (e) {
        removeTyping();
        addMessage('bot', '⚠️ Error al transcribir el audio.');
    }
}

function handleKey(e) { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); enviar(); } }
function sendQuick(t) { document.getElementById('msg-input').value = t; enviar(); }

async function enviar() {
    const input = document.getElementById('msg-input');
    const texto = input.value.trim();
    if (!texto && !imagenSeleccionada) return;
    document.getElementById('welcome')?.remove();
    input.value = ''; autoResize(input);

    if (imagenSeleccionada) {
        addMessage('user', texto || '(imagen adjunta)', { imagen: imagenSeleccionada });
        await enviarConImagen(texto, imagenSeleccionada);
        removeImage(); return;
    }

    addMessage('user', texto);
    await enviarTextoAlAgente(texto);
}

async function enviarTextoAlAgente(texto) {
    showTyping();
    try {
        let respuesta, badge = null, badgeLabel = null, audioUrl = null;

        // 1. RAG primero — preguntas sobre la web de FinBot (nunca pasan por caché)
        if (esConsultaRAG(texto)) {
            const ragRes = await fetch(`${BACKEND}/rag`, {
                method: 'POST', headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ mensaje: texto })
            });
            const ragData = await ragRes.json();
            respuesta = ragData.respuesta;
            badge = 'rag';

        } else {
            // 2. Revisa caché
            const cacheRes = await fetch(`${BACKEND}/cache`, {
                method: 'POST', headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ mensaje: texto })
            });
            const cacheData = await cacheRes.json();

            if (cacheData.desde_cache) {
                respuesta = cacheData.respuesta;
                badge = 'cache';

            } else {
                // 3. Agente principal con tools
                const chatRes = await fetch(`${BACKEND}/chat`, {
                    method: 'POST', headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ mensaje: texto })
                });
                const chatData = await chatRes.json();
                respuesta = chatData.respuesta;
                // Badge de tool viene del BACKEND (no keywords)
                if (chatData.tool_used) {
                    badge = 'tool';
                    badgeLabel = chatData.tools?.length ? `⚡ ${chatData.tools[0]}` : '⚡ Tool';
                }
                // Guarda la respuesta real (con tools) en el caché para futuras consultas
                fetch(`${BACKEND}/cache/guardar`, {
                    method: 'POST', headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ pregunta: texto, respuesta: respuesta })
                }).catch(() => {}); // fire-and-forget, no bloquea la UI
            }
        }

        // 4. Sintetizar si modo audio
        if (modoRespuesta === 'audio') {
            const audioRes = await fetch(`${BACKEND}/voice/synthesize`, {
                method: 'POST', headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ mensaje: respuesta })
            });
            audioUrl = URL.createObjectURL(await audioRes.blob());
        }

        removeTyping();
        addMessage('bot', respuesta, { badge, badgeLabel, audioUrl });
    } catch (e) {
        removeTyping();
        addMessage('bot', `⚠️ Error: ${e.message}`);
    }
}

async function enviarConImagen(texto, imagen) {
    showTyping();
    try {
        const formData = new FormData();
        formData.append('mensaje', texto || 'Analiza esta imagen');
        formData.append('imagen', imagen);
        const res = await fetch(`${BACKEND}/vision`, { method: 'POST', body: formData });
        if (!res.ok) {
            const err = await res.text();
            console.error('Error vision endpoint:', err);
            throw new Error(`HTTP ${res.status}: ${err}`);
        }
        const data = await res.json();
        removeTyping();
        addMessage('bot', data.respuesta);
    } catch (e) {
        removeTyping();
        console.error('enviarConImagen error:', e);
        addMessage('bot', `⚠️ Error al analizar la imagen: ${e.message}`);
    }
}

function esConsultaRAG(texto) {
    const kw = ['según la web', 'según finbot', 'productos de finbot', 'cdt',
        'certificado de depósito', 'hipóteca', 'crédito hipotecario',
        'cuenta de ahorros finbot', 'portafolio finbot', 'inversiones finbot',
        'finbot ofrece', 'qué ofrece finbot', 'según la página'];
    return kw.some(k => texto.toLowerCase().includes(k));
}

function detectarTool(texto) {
    // Fallback: solo se usa si el backend no retorna tool_used
    const kw = ['dólar', 'dollar', 'usd', 'cop', 'tasa', 'bitcoin', 'btc', 'crypto',
        'invierto', 'inversión', 'interés', 'interest', 'rendimiento'];
    return kw.some(k => texto.toLowerCase().includes(k));
}

function addTranscripcion(texto) {
    const chat = document.getElementById('chat');
    const div = document.createElement('div');
    div.className = 'message user';
    div.innerHTML = `<div class="transcription">🎙 ${texto}</div>`;
    chat.appendChild(div);
    chat.scrollTop = chat.scrollHeight;
}

function addMessage(rol, texto, opts = {}) {
    const chat = document.getElementById('chat');
    const wrap = document.createElement('div');
    wrap.className = `message ${rol}`;

    if (opts.imagen) {
        const img = document.createElement('img');
        img.className = 'msg-image';
        img.src = URL.createObjectURL(opts.imagen);
        wrap.appendChild(img);
    }

    const bubble = document.createElement('div');
    bubble.className = 'bubble';
    bubble.textContent = texto;
    wrap.appendChild(bubble);

    if (opts.audioUrl) {
        const audio = document.createElement('audio');
        audio.controls = true; audio.autoplay = true; audio.src = opts.audioUrl;
        wrap.appendChild(audio);
    }

    const meta = document.createElement('div');
    meta.className = 'meta';
    const ts = document.createElement('span');
    ts.className = 'timestamp';
    ts.textContent = new Date().toLocaleTimeString('es-CO', { hour: '2-digit', minute: '2-digit' });
    meta.appendChild(ts);

    if (opts.badge === 'tool') {
        const b = document.createElement('span');
        b.className = 'badge badge-tool';
        b.textContent = opts.badgeLabel || '⚡ Tool';
        meta.appendChild(b);
    } else if (opts.badge === 'cache') {
        const b = document.createElement('span');
        b.className = 'badge badge-cache';
        b.textContent = '■ Caché';
        meta.appendChild(b);
    } else if (opts.badge === 'rag') {
        const b = document.createElement('span');
        b.className = 'badge badge-rag';
        b.textContent = '🔍 RAG';
        meta.appendChild(b);
    }

    wrap.appendChild(meta);
    chat.appendChild(wrap);
    chat.scrollTop = chat.scrollHeight;
}

function showTyping() {
    const chat = document.getElementById('chat');
    const t = document.createElement('div');
    t.className = 'message bot'; t.id = 'typing';
    t.innerHTML = '<div class="typing"><span></span><span></span><span></span></div>';
    chat.appendChild(t);
    chat.scrollTop = chat.scrollHeight;
}

function removeTyping() { document.getElementById('typing')?.remove(); }

function autoResize(el) {
    el.style.height = 'auto';
    el.style.height = Math.min(el.scrollHeight, 120) + 'px';
}
