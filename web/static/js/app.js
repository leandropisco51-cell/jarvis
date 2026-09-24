/**
 * J.A.R.V.I.S. Core Front-End Controller
 * Gerencia comunicação com a API FastAPI, streaming SSE, Reconhecimento de Voz (STT) e Síntese de Voz (TTS).
 */

document.addEventListener('DOMContentLoaded', () => {
  const reactor = new ArcReactor('reactorCanvas');
  const chatMessages = document.getElementById('chatMessages');
  const chatInput = document.getElementById('chatInput');
  const sendBtn = document.getElementById('sendBtn');
  const micBtn = document.getElementById('micBtn');
  const voiceToggle = document.getElementById('voiceToggle');
  const modelSelect = document.getElementById('modelSelect');

  let isVoiceEnabled = true;
  let isListening = false;
  let recognition = null;
  let synth = window.speechSynthesis;
  let ptVoice = null;

  // 1. Configurar Síntese de Voz (TTS)
  function initTTS() {
    function loadVoices() {
      const voices = synth.getVoices();
      // Prioriza vozes em português brasileiro
      ptVoice = voices.find(v => v.lang === 'pt-BR' && (v.name.includes('Google') || v.name.includes('Daniel') || v.name.includes('Natural'))) ||
                voices.find(v => v.lang === 'pt-BR') ||
                voices.find(v => v.lang.startsWith('pt')) ||
                null;
    }

    loadVoices();
    if (speechSynthesis.onvoiceschanged !== undefined) {
      speechSynthesis.onvoiceschanged = loadVoices;
    }
  }

  function speakText(text) {
    if (!isVoiceEnabled || !synth) return;

    // Cancela falas anteriores
    synth.cancel();

    // Remove tags markdown básicas para leitura mais fluida
    const cleanText = text
      .replace(/[*#_`]/g, '')
      .replace(/\[.*?\]\(.*?\)/g, '')
      .trim();

    if (!cleanText) return;

    const utterance = new SpeechSynthesisUtterance(cleanText);
    utterance.lang = 'pt-BR';
    if (ptVoice) utterance.voice = ptVoice;
    utterance.rate = 1.05; // Levemente acelerado e articulado
    utterance.pitch = 0.95; // Tom ligeiramente grave sofisticado

    utterance.onstart = () => {
      reactor.setState('SPEAKING');
    };

    utterance.onboundary = (event) => {
      if (reactor && reactor.pulseSpeech) {
        reactor.pulseSpeech();
      }
    };

    utterance.onend = () => {
      reactor.setState('STANDBY');
    };

    utterance.onerror = () => {
      reactor.setState('STANDBY');
    };

    synth.speak(utterance);
  }

  // 2. Configurar Reconhecimento de Voz (STT)
  function initSTT() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      console.warn('Reconhecimento de voz não suportado neste navegador.');
      micBtn.title = 'Reconhecimento de voz não suportado neste navegador';
      micBtn.style.opacity = '0.5';
      return;
    }

    recognition = new SpeechRecognition();
    recognition.lang = 'pt-BR';
    recognition.continuous = false;
    recognition.interimResults = false;

    recognition.onstart = () => {
      isListening = true;
      micBtn.classList.add('active');
      reactor.setState('LISTENING');
    };

    recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript;
      if (transcript && transcript.trim()) {
        chatInput.value = transcript.trim();
        sendMessage();
      }
    };

    recognition.onerror = (event) => {
      console.error('Erro de reconhecimento de voz:', event.error);
      stopListening();
    };

    recognition.onend = () => {
      stopListening();
    };
  }

  function toggleListening() {
    if (!recognition) {
      alert('Seu navegador não suporta a Web Speech API ou o microfone foi negado.');
      return;
    }
    if (isListening) {
      recognition.stop();
    } else {
      try {
        recognition.start();
      } catch (e) {
        console.error(e);
      }
    }
  }

  function stopListening() {
    isListening = false;
    micBtn.classList.remove('active');
    if (reactor.state === 'LISTENING') {
      reactor.setState('STANDBY');
    }
  }

  // 3. Adicionar mensagens à tela
  function appendMessage(sender, text, isStreaming = false) {
    const msgDiv = document.createElement('div');
    msgDiv.className = `msg ${sender}`;

    const header = document.createElement('div');
    header.className = 'msg-header';
    header.textContent = sender === 'user' ? 'VOCÊ' : 'J.A.R.V.I.S.';

    const bubble = document.createElement('div');
    bubble.className = 'msg-bubble';
    bubble.innerHTML = text;

    if (isStreaming) {
      const cursor = document.createElement('span');
      cursor.className = 'cursor-blink';
      bubble.appendChild(cursor);
    }

    msgDiv.appendChild(header);
    msgDiv.appendChild(bubble);
    chatMessages.appendChild(msgDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;

    return bubble;
  }

  // 4. Enviar mensagem e streaming da resposta
  async function sendMessage() {
    const text = chatInput.value.trim();
    if (!text) return;

    chatInput.value = '';
    appendMessage('user', text);

    reactor.setState('THINKING');

    // Cria a bolha onde o Jarvis vai responder por streaming
    const jarvisBubble = appendMessage('jarvis', '', true);

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text })
      });

      if (!response.ok) {
        const errData = await response.json().catch(() => ({}));
        throw new Error(errData.detail || 'Falha ao comunicar com o servidor');
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder('utf-8');
      let fullResponse = '';

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        // Os chunks são linhas SSE: data: {"token": "..."}
        const lines = chunk.split('\n');
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const dataStr = line.slice(6).trim();
            if (dataStr === '[DONE]') break;
            try {
              const parsed = JSON.parse(dataStr);
              if (parsed.status) {
                if (parsed.state) reactor.setState(parsed.state);
                jarvisBubble.innerHTML = `<span style="color: #ffb700; font-family: var(--font-mono); font-size: 0.85rem;">⚡ [AUTO-EVOLUÇÃO]: ${parsed.status}</span><span class="cursor-blink"></span>`;
                chatMessages.scrollTop = chatMessages.scrollHeight;
              }
              if (parsed.memory_updated) {
                loadMemories();
              }
              if (parsed.hardware_optimized) {
                updateTelemetry();
              }
              if (parsed.token) {
                fullResponse += parsed.token;
                jarvisBubble.innerHTML = fullResponse.replace(/\n/g, '<br>') + '<span class="cursor-blink"></span>';
                chatMessages.scrollTop = chatMessages.scrollHeight;
              }
            } catch (e) {
              // chunk bruto
            }
          }
        }
      }

      // Remove o cursor piscante
      jarvisBubble.innerHTML = fullResponse.replace(/\n/g, '<br>');
      chatMessages.scrollTop = chatMessages.scrollHeight;

      // Fala o texto consolidado
      speakText(fullResponse);

    } catch (err) {
      jarvisBubble.innerHTML = `<span style="color: #ff3366;">[ERRO]: ${err.message}</span>`;
      reactor.setState('STANDBY');
    }
  }

  // 5. Telemetria em tempo real
  async function updateTelemetry() {
    try {
      const res = await fetch('/api/status');
      if (!res.ok) return;
      const data = await res.json();

      // Memória
      if (data.memory && data.memory.percent_used !== undefined) {
        const memPercent = data.memory.percent_used;
        document.getElementById('ramPercent').textContent = `${memPercent}%`;
        document.getElementById('ramBar').style.width = `${memPercent}%`;
        document.getElementById('ramDetail').textContent = `${data.memory.used_gb} GB / ${data.memory.total_gb} GB`;
      }

      // Disco Principal
      if (data.disk && data.disk.percent !== undefined) {
        const diskPercent = data.disk.percent;
        const diskElem = document.getElementById('diskPercent');
        const diskBar = document.getElementById('diskBar');
        const diskDetail = document.getElementById('diskDetail');
        if (diskElem) diskElem.textContent = `${diskPercent}%`;
        if (diskBar) diskBar.style.width = `${diskPercent}%`;
        if (diskDetail) diskDetail.textContent = `${data.disk.free_gb} GB livres / ${data.disk.total_gb} GB`;
      }

      // CPU e Info
      document.getElementById('cpuCores').textContent = `${data.cpu_count} Núcleos`;
      document.getElementById('osName').textContent = data.os || 'Windows';

      // Status Ollama
      const dot = document.getElementById('ollamaDot');
      const text = document.getElementById('ollamaText');
      if (data.ollama_online) {
        dot.className = 'status-dot';
        text.textContent = 'OLLAMA ONLINE (127.0.0.1:11434)';
      } else {
        dot.className = 'status-dot offline';
        text.textContent = 'OLLAMA OFFLINE';
      }

      // Relógio
      const timeElem = document.getElementById('hudTime');
      if (timeElem && data.datetime) {
        timeElem.textContent = data.datetime;
      }
    } catch (e) {
      console.warn('Falha ao atualizar telemetria:', e);
    }
  }

  // 6. Carregar lista de modelos
  async function loadModels() {
    try {
      const res = await fetch('/api/models');
      if (!res.ok) return;
      const data = await res.json();

      modelSelect.innerHTML = '';
      data.models.forEach(m => {
        const opt = document.createElement('option');
        opt.value = m;
        opt.textContent = m;
        if (m === data.current_model) opt.selected = true;
        modelSelect.appendChild(opt);
      });
    } catch (e) {
      console.warn('Falha ao listar modelos:', e);
    }
  }

  modelSelect.addEventListener('change', async () => {
    const selected = modelSelect.value;
    try {
      await fetch('/api/model', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ model: selected })
      });
      appendMessage('jarvis', `Pronto, troquei pro modelo <b>${selected}</b>!`);
      speakText(`Pronto, troquei pro modelo ${selected}!`);
    } catch (e) {
      alert('Falha ao alterar modelo: ' + e);
    }
  });

  // Event Listeners
  sendBtn.addEventListener('click', sendMessage);
  chatInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
      sendMessage();
    }
  });

  micBtn.addEventListener('click', toggleListening);

  voiceToggle.addEventListener('click', () => {
    isVoiceEnabled = !isVoiceEnabled;
    voiceToggle.classList.toggle('active', isVoiceEnabled);
    voiceToggle.querySelector('span').textContent = isVoiceEnabled ? 'VOZ DO JARVIS: ON' : 'VOZ DO JARVIS: OFF';
    if (!isVoiceEnabled) {
      synth.cancel();
      reactor.setState('STANDBY');
    }
  });

  // 7. Gerenciador de Memória Córtex
  async function loadMemories() {
    try {
      const res = await fetch('/api/memories');
      if (!res.ok) return;
      const data = await res.json();
      const container = document.getElementById('memoryListContainer');
      const badge = document.getElementById('memoryCountBadge');
      const memories = data.memories || [];

      if (badge) {
        badge.textContent = `${memories.length} ${memories.length === 1 ? 'FATO' : 'FATOS'}`;
      }

      if (!container) return;

      if (memories.length === 0) {
        container.innerHTML = '<div class="memory-empty">Nenhum fato memorizado ainda.<br>Diga: "Jarvis, lembre-se que..."</div>';
        return;
      }

      container.innerHTML = '';
      memories.forEach(mem => {
        const item = document.createElement('div');
        item.className = 'memory-item';
        item.innerHTML = `
          <div class="memory-body">
            <span class="memory-cat-tag">[${mem.category}]</span>
            <span class="memory-text">${escapeHtml(mem.content)}</span>
          </div>
          <button class="memory-del-btn" title="Excluir lembrança" data-id="${mem.id}">&times;</button>
        `;
        container.appendChild(item);
      });

      // Configura evento de exclusão
      container.querySelectorAll('.memory-del-btn').forEach(btn => {
        btn.addEventListener('click', async (e) => {
          e.stopPropagation();
          const id = btn.getAttribute('data-id');
          await deleteMemory(id);
        });
      });
    } catch (e) {
      console.warn('Falha ao carregar memórias:', e);
    }
  }

  async function deleteMemory(id) {
    try {
      const res = await fetch(`/api/memories/${id}`, { method: 'DELETE' });
      if (res.ok) {
        loadMemories();
      }
    } catch (e) {
      console.error('Falha ao deletar memória:', e);
    }
  }

  function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  // 8. Otimização Tática de Hardware
  async function runSystemOptimization() {
    const optBtn = document.getElementById('optimizeBtn');
    if (optBtn) {
      optBtn.classList.add('optimizing');
      optBtn.innerHTML = '<span>⚡ OTIMIZANDO SISTEMA...</span>';
    }

    appendMessage('user', 'Jarvis, otimize o sistema e acelere a máquina agora.');
    reactor.setState('THINKING');
    const jarvisBubble = appendMessage('jarvis', '', true);

    try {
      const res = await fetch('/api/hardware/optimize', { method: 'POST' });
      if (!res.ok) throw new Error('Falha ao acionar a rotina de otimização.');
      const data = await res.json();

      const msg = `Faxina feita com sucesso, chefe! Liberei <b>${data.freed_ram_mb} MB</b> de RAM e limpei <b>${data.deleted_temp_items}</b> arquivos temporários (<b>${data.freed_disk_mb} MB</b> de espaço recuperado). Agora a RAM tá em <b>${data.current_ram_percent}%</b> e a máquina tá tinindo!`;
      jarvisBubble.innerHTML = msg;
      speakText(`Faxina concluída, chefe! Liberei ${data.freed_ram_mb} megas de RAM e a máquina tá bem mais leve.`);
      await updateTelemetry();
    } catch (err) {
      jarvisBubble.innerHTML = `<span style="color: #ff3366;">[ERRO]: ${err.message}</span>`;
      reactor.setState('STANDBY');
    } finally {
      if (optBtn) {
        optBtn.classList.remove('optimizing');
        optBtn.innerHTML = '<span class="optimize-icon">⚡</span><span>OTIMIZAR SISTEMA</span>';
      }
    }
  }

  const optBtn = document.getElementById('optimizeBtn');
  if (optBtn) {
    optBtn.addEventListener('click', runSystemOptimization);
  }

  // Ações rápidas dos chips
  document.querySelectorAll('.chip-btn').forEach(chip => {
    chip.addEventListener('click', () => {
      chatInput.value = chip.getAttribute('data-cmd') || chip.textContent;
      sendMessage();
    });
  });

  // Inicializações
  initTTS();
  initSTT();
  loadModels();
  loadMemories();
  updateTelemetry();
  setInterval(updateTelemetry, 3500);

  // Mensagem inicial de boas-vindas do Jarvis
  setTimeout(() => {
    speakText('Opa, tudo pronto por aqui! Em que posso te ajudar hoje?');
  }, 1000);
});
