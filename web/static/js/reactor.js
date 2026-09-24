/**
 * J.A.R.V.I.S. Cybernetic Holographic Face Visualizer (3D Particle Mesh)
 * Rosto mecânico futurista construído em nuvem de pontos 3D que flutuam no espaço,
 * com articulação dinâmica de boca e mandíbula em perfeita sincronia com a voz do Jarvis.
 */

class CyberFace {
  constructor(canvasId) {
    this.canvas = document.getElementById(canvasId);
    this.ctx = this.canvas.getContext('2d');
    this.state = 'STANDBY'; // 'STANDBY' | 'LISTENING' | 'THINKING' | 'SPEAKING' | 'CODING'

    // Dimensões do Canvas e Projeção 3D
    this.width = 440;
    this.height = 440;
    this.centerX = 220;
    this.centerY = 210;
    this.fov = 440;
    this.cameraDistance = 210;

    // Rotação 3D (Pitch, Yaw, Roll)
    this.rotX = 0;
    this.rotY = 0;
    this.rotZ = 0;
    this.targetRotX = 0;
    this.targetRotY = 0;

    // Articulação da Boca e Mandíbula
    this.mouthOpen = 0.0; // 0.0 (fechada) a 1.0 (totalmente aberta)
    this.targetMouthOpen = 0.0;
    this.lastSpeechPulse = 0;

    // Movimentação do Olhar / Mouse Parallax
    this.mouseX = 0;
    this.mouseY = 0;
    this.lookOffsetX = 0;
    this.lookOffsetY = 0;

    // Temporizador global
    this.time = 0;

    // Inicialização da Geometria do Rosto Robótico e Partículas
    this.initFaceGeometry();
    this.initAmbientParticles();

    this.resize();
    window.addEventListener('resize', () => this.resize());
    window.addEventListener('mousemove', (e) => this.handleMouseMove(e));

    this.animate();
  }

  resize() {
    const rect = this.canvas.getBoundingClientRect();
    const dpr = window.devicePixelRatio || 1;
    const size = Math.floor(Math.min(rect.width || 440, rect.height || 440)) || 440;
    
    this.canvas.width = size * dpr;
    this.canvas.height = size * dpr;
    if (this.ctx.resetTransform) {
      this.ctx.resetTransform();
    } else {
      this.ctx.setTransform(1, 0, 0, 1, 0, 0);
    }
    this.ctx.scale(dpr, dpr);
    this.width = size;
    this.height = size;
    this.centerX = size / 2;
    this.centerY = size / 2 - 10;
  }

  handleMouseMove(e) {
    const rect = this.canvas.getBoundingClientRect();
    const canvasCenterX = rect.left + rect.width / 2;
    const canvasCenterY = rect.top + rect.height / 2;

    const normX = Math.max(-1, Math.min(1, (e.clientX - canvasCenterX) / (window.innerWidth / 2)));
    const normY = Math.max(-1, Math.min(1, (e.clientY - canvasCenterY) / (window.innerHeight / 2)));

    // Rotação suave da cabeça acompanhando a atenção do usuário
    this.targetRotY = normX * 0.28; // Yaw (~16 graus)
    this.targetRotX = -normY * 0.20; // Pitch (~11 graus)

    // Deslocamento da pupila / sensores ópticos
    this.lookOffsetX = normX;
    this.lookOffsetY = normY;
  }

  pulseSpeech() {
    // Acionado a cada palavra/fonema pronunciado pelo TTS
    this.lastSpeechPulse = Date.now();
  }

  setState(newState) {
    this.state = newState;
    const label = document.getElementById('reactorStateText');
    if (label) {
      const stateMap = {
        STANDBY: 'SISTEMAS ONLINE // STANDBY',
        LISTENING: 'OUVINDO COMANDOS... // AUDIÇÃO',
        THINKING: 'PROCESSANDO REDE NEURAL...',
        SPEAKING: 'SÍNTESE DE VOZ // TRANSMITINDO',
        CODING: 'AUTO-EVOLUÇÃO // CODIFICANDO...',
      };
      label.textContent = stateMap[newState] || newState;
      const stateColor = newState === 'LISTENING' ? '#ff2a6d' : (newState === 'CODING' ? '#ffb700' : (newState === 'SPEAKING' ? '#00ffcc' : (newState === 'THINKING' ? '#a855f7' : '#00f0ff')));
      label.style.borderColor = stateColor;
      label.style.color = stateColor;
    }
  }

  initFaceGeometry() {
    this.nodes = [];
    this.edges = [];

    const nodeIndex = {};

    const addNode = (id, x, y, z, options = {}) => {
      const idx = this.nodes.length;
      nodeIndex[id] = idx;
      this.nodes.push({
        id,
        baseX: x,
        baseY: y,
        baseZ: z,
        x, y, z,
        projX: 0,
        projY: 0,
        projScale: 1,
        projZ: 0,
        ...options
      });
      return idx;
    };

    const addEdge = (id1, id2, edgeOptions = {}) => {
      const i1 = nodeIndex[id1];
      const i2 = nodeIndex[id2];
      if (i1 !== undefined && i2 !== undefined) {
        this.edges.push({ i1, i2, ...edgeOptions });
      }
    };

    // 1. COROA E ESTRUTURA DO CRÂNIO (Holographic Cranium)
    addNode('crown_top', 0, -148, 12, { isCrown: true });
    addNode('crown_tl1', -36, -142, 22);
    addNode('crown_tr1', 36, -142, 22);
    addNode('crown_tl2', -76, -126, 12);
    addNode('crown_tr2', 76, -126, 12);
    addNode('temple_l', -96, -96, -8);
    addNode('temple_r', 96, -96, -8);

    // 2. PLACAS DA TESTA E CHIPSET NEURAL
    addNode('forehead_c', 0, -114, 46);
    addNode('forehead_l', -42, -110, 44);
    addNode('forehead_r', 42, -110, 44);
    addNode('forehead_out_l', -72, -96, 26);
    addNode('forehead_out_r', 72, -96, 26);

    // Núcleo Neural Central (Processador Holográfico)
    addNode('core_top', 0, -96, 58, { isCore: true });
    addNode('core_left', -13, -88, 56, { isCore: true });
    addNode('core_right', 13, -88, 56, { isCore: true });
    addNode('core_bot', 0, -80, 58, { isCore: true });

    // 3. SOBRANCELHAS CYBERNETIC
    addNode('glabella', 0, -70, 64);
    addNode('brow_in_l', -22, -72, 62);
    addNode('brow_in_r', 22, -72, 62);
    addNode('brow_mid_l', -48, -73, 54);
    addNode('brow_mid_r', 48, -73, 54);
    addNode('brow_out_l', -75, -68, 40);
    addNode('brow_out_r', 75, -68, 40);

    // 4. SENSORES ÓPTICOS / OLHOS BIÔNICOS
    // Olho Esquerdo
    addNode('eye_in_l', -20, -50, 56, { isEye: true });
    addNode('eye_top_l', -40, -58, 54, { isEye: true });
    addNode('eye_out_l', -64, -48, 44, { isEye: true });
    addNode('eye_bot_l', -40, -42, 52, { isEye: true });
    addNode('pupil_l', -40, -50, 56, { isPupil: true, isLeftPupil: true });

    // Olho Direito
    addNode('eye_in_r', 20, -50, 56, { isEye: true });
    addNode('eye_top_r', 40, -58, 54, { isEye: true });
    addNode('eye_out_r', 64, -48, 44, { isEye: true });
    addNode('eye_bot_r', 40, -42, 52, { isEye: true });
    addNode('pupil_r', 40, -50, 56, { isPupil: true, isRightPupil: true });

    // 5. NARIZ & RESPIRADOR MECÂNICO
    addNode('nose_bridge1', 0, -52, 70);
    addNode('nose_bridge2', 0, -28, 80);
    addNode('nose_tip', 0, -2, 90, { isNoseTip: true });
    addNode('nostril_l', -16, -2, 76);
    addNode('nostril_r', 16, -2, 76);
    addNode('subnasal', 0, 8, 78);

    // 6. MAÇÃS DO ROSTO & ENTRADAS DE ÁUDIO LATERAIS
    addNode('cheek_top_l', -80, -32, 34);
    addNode('cheek_top_r', 80, -32, 34);
    addNode('cheek_mid_l', -68, -2, 40);
    addNode('cheek_mid_r', 68, -2, 40);
    addNode('cheek_low_l', -54, 12, 44);
    addNode('cheek_low_r', 54, 12, 44);

    // Antenas e portas de áudio temporais
    addNode('ear_top_l', -96, -30, -5);
    addNode('ear_top_r', 96, -30, -5);
    addNode('ear_mid_l', -100, -10, -5);
    addNode('ear_mid_r', 100, -10, -5);
    addNode('ear_bot_l', -96, 10, -5);
    addNode('ear_bot_r', 96, 10, -5);

    // 7. BOCA ARTICULADA (SE MEXE DINAMICAMENTE AO FALAR)
    // Lábio Superior (Fixo com leve vibração acústica)
    addNode('lip_top_c', 0, 18, 76, { isMouthUpper: true });
    addNode('lip_top_l', -16, 20, 71, { isMouthUpper: true });
    addNode('lip_top_r', 16, 20, 71, { isMouthUpper: true });
    addNode('mouth_corner_l', -34, 24, 59, { isMouthCorner: true });
    addNode('mouth_corner_r', 34, 24, 59, { isMouthCorner: true });

    // Lábio Inferior (Move-se para baixo com o ritmo da fala)
    addNode('lip_bot_c', 0, 26, 74, { isMouthLower: true, mouthWeight: 1.0 });
    addNode('lip_bot_l', -16, 26, 69, { isMouthLower: true, mouthWeight: 0.85 });
    addNode('lip_bot_r', 16, 26, 69, { isMouthLower: true, mouthWeight: 0.85 });

    // Cavidade Acústica Interna (Laser sonoro da fala)
    addNode('mouth_inner_c', 0, 22, 67, { isMouthInner: true, mouthWeight: 0.5 });
    addNode('mouth_inner_l', -18, 22, 61, { isMouthInner: true, mouthWeight: 0.4 });
    addNode('mouth_inner_r', 18, 22, 61, { isMouthInner: true, mouthWeight: 0.4 });

    // 8. MANDÍBULA & QUEIXO ARTICULADOS (Acompanham a abertura bucal)
    addNode('mentolabial', 0, 44, 69, { isJaw: true, jawWeight: 0.6 });
    addNode('chin_top_l', -20, 52, 63, { isJaw: true, jawWeight: 0.65 });
    addNode('chin_top_r', 20, 52, 63, { isJaw: true, jawWeight: 0.65 });

    addNode('jaw_angle_l', -74, 36, 18, { isJaw: true, jawWeight: 0.25 });
    addNode('jaw_angle_r', 74, 36, 18, { isJaw: true, jawWeight: 0.25 });
    addNode('jaw_mid_l', -56, 62, 28, { isJaw: true, jawWeight: 0.55 });
    addNode('jaw_mid_r', 56, 62, 28, { isJaw: true, jawWeight: 0.55 });

    addNode('chin_corner_l', -26, 86, 48, { isChin: true, chinWeight: 0.9 });
    addNode('chin_corner_r', 26, 86, 48, { isChin: true, chinWeight: 0.9 });
    addNode('chin_tip', 0, 94, 56, { isChin: true, chinWeight: 1.0 });

    // 9. PESCOÇO & TRANSDUTOR DE TRANSMISSÃO
    addNode('throat_core', 0, 122, 25, { isThroat: true });
    addNode('neck_l1', -34, 116, 15);
    addNode('neck_r1', 34, 116, 15);
    addNode('neck_base_l', -52, 142, -5);
    addNode('neck_base_r', 52, 142, -5);
    addNode('neck_base_c', 0, 146, 10);

    // ==========================================
    // CONEXÕES POLIGONAIS (WIREFRAME HOLOGRÁFICO)
    // ==========================================
    // Crânio & Testa
    addEdge('crown_tl2', 'crown_tl1');
    addEdge('crown_tl1', 'crown_top');
    addEdge('crown_top', 'crown_tr1');
    addEdge('crown_tr1', 'crown_tr2');
    addEdge('crown_tl2', 'temple_l');
    addEdge('crown_tr2', 'temple_r');

    addEdge('temple_l', 'forehead_out_l');
    addEdge('forehead_out_l', 'forehead_l');
    addEdge('forehead_l', 'forehead_c');
    addEdge('forehead_c', 'forehead_r');
    addEdge('forehead_r', 'forehead_out_r');
    addEdge('forehead_out_r', 'temple_r');

    // Núcleo Neural
    addEdge('forehead_c', 'core_top');
    addEdge('core_top', 'core_left');
    addEdge('core_left', 'core_bot');
    addEdge('core_bot', 'core_right');
    addEdge('core_right', 'core_top');
    addEdge('core_bot', 'glabella');

    // Sobrancelhas
    addEdge('glabella', 'brow_in_l');
    addEdge('brow_in_l', 'brow_mid_l');
    addEdge('brow_mid_l', 'brow_out_l');
    addEdge('brow_out_l', 'temple_l');

    addEdge('glabella', 'brow_in_r');
    addEdge('brow_in_r', 'brow_mid_r');
    addEdge('brow_mid_r', 'brow_out_r');
    addEdge('brow_out_r', 'temple_r');

    // Olhos / Sensores Ópticos
    addEdge('eye_in_l', 'eye_top_l');
    addEdge('eye_top_l', 'eye_out_l');
    addEdge('eye_out_l', 'eye_bot_l');
    addEdge('eye_bot_l', 'eye_in_l');
    addEdge('brow_mid_l', 'eye_top_l');

    addEdge('eye_in_r', 'eye_top_r');
    addEdge('eye_top_r', 'eye_out_r');
    addEdge('eye_out_r', 'eye_bot_r');
    addEdge('eye_bot_r', 'eye_in_r');
    addEdge('brow_mid_r', 'eye_top_r');

    // Nariz
    addEdge('glabella', 'nose_bridge1');
    addEdge('nose_bridge1', 'nose_bridge2');
    addEdge('nose_bridge2', 'nose_tip');
    addEdge('nose_tip', 'nostril_l');
    addEdge('nostril_l', 'subnasal');
    addEdge('nose_tip', 'nostril_r');
    addEdge('nostril_r', 'subnasal');
    addEdge('eye_in_l', 'nose_bridge1');
    addEdge('eye_in_r', 'nose_bridge1');

    // Bochechas & Orelhas
    addEdge('eye_out_l', 'cheek_top_l');
    addEdge('cheek_top_l', 'cheek_mid_l');
    addEdge('cheek_mid_l', 'cheek_low_l');
    addEdge('cheek_top_l', 'ear_top_l');
    addEdge('ear_top_l', 'ear_mid_l');
    addEdge('ear_mid_l', 'ear_bot_l');
    addEdge('ear_bot_l', 'jaw_angle_l');

    addEdge('eye_out_r', 'cheek_top_r');
    addEdge('cheek_top_r', 'cheek_mid_r');
    addEdge('cheek_mid_r', 'cheek_low_r');
    addEdge('cheek_top_r', 'ear_top_r');
    addEdge('ear_top_r', 'ear_mid_r');
    addEdge('ear_mid_r', 'ear_bot_r');
    addEdge('ear_bot_r', 'jaw_angle_r');

    // Boca
    addEdge('subnasal', 'lip_top_c');
    addEdge('lip_top_c', 'lip_top_l');
    addEdge('lip_top_l', 'mouth_corner_l');
    addEdge('lip_top_c', 'lip_top_r');
    addEdge('lip_top_r', 'mouth_corner_r');

    addEdge('mouth_corner_l', 'lip_bot_l');
    addEdge('lip_bot_l', 'lip_bot_c');
    addEdge('lip_bot_c', 'lip_bot_r');
    addEdge('lip_bot_r', 'mouth_corner_r');

    addEdge('nostril_l', 'lip_top_l');
    addEdge('nostril_r', 'lip_top_r');
    addEdge('cheek_low_l', 'mouth_corner_l');
    addEdge('cheek_low_r', 'mouth_corner_r');

    // Cavidade interna
    addEdge('mouth_inner_l', 'mouth_inner_c');
    addEdge('mouth_inner_c', 'mouth_inner_r');

    // Mandíbula & Queixo
    addEdge('lip_bot_c', 'mentolabial');
    addEdge('mentolabial', 'chin_top_l');
    addEdge('mentolabial', 'chin_top_r');

    addEdge('jaw_angle_l', 'jaw_mid_l');
    addEdge('jaw_mid_l', 'chin_corner_l');
    addEdge('chin_corner_l', 'chin_tip');
    addEdge('chin_tip', 'chin_corner_r');
    addEdge('chin_corner_r', 'jaw_mid_r');
    addEdge('jaw_mid_r', 'jaw_angle_r');

    addEdge('chin_top_l', 'chin_corner_l');
    addEdge('chin_top_r', 'chin_corner_r');

    // Pescoço & Transdutor
    addEdge('chin_tip', 'throat_core');
    addEdge('jaw_mid_l', 'neck_l1');
    addEdge('jaw_mid_r', 'neck_r1');
    addEdge('neck_l1', 'throat_core');
    addEdge('neck_r1', 'throat_core');
    addEdge('throat_core', 'neck_base_c');
    addEdge('neck_l1', 'neck_base_l');
    addEdge('neck_r1', 'neck_base_r');
    addEdge('neck_base_l', 'neck_base_c');
    addEdge('neck_base_r', 'neck_base_c');
  }

  initAmbientParticles() {
    this.ambientParticles = [];
    const count = 65;
    for (let i = 0; i < count; i++) {
      const radius = 110 + Math.random() * 110;
      const theta = Math.random() * Math.PI * 2;
      const phi = (Math.random() - 0.5) * Math.PI;

      this.ambientParticles.push({
        baseX: radius * Math.cos(phi) * Math.sin(theta),
        baseY: radius * Math.sin(phi) + (Math.random() - 0.5) * 80,
        baseZ: radius * Math.cos(phi) * Math.cos(theta),
        speed: 0.2 + Math.random() * 0.6,
        size: 1.0 + Math.random() * 2.2,
        phase: Math.random() * Math.PI * 2,
        glow: Math.random() > 0.6,
      });
    }
  }

  animate() {
    requestAnimationFrame(() => this.animate());

    this.time += 0.035;
    this.ctx.clearRect(0, 0, this.width, this.height);

    // 1. Controle da Articulação da Boca em Função do Estado de Fala
    if (this.state === 'SPEAKING') {
      const t = this.time;
      // Oscilação combinada simulando fala articulada natural e pausas
      const speechWave = Math.sin(t * 11.5) * 0.45 + Math.sin(t * 18.2) * 0.35 + Math.sin(t * 6.5) * 0.20;
      const syllableBurst = Math.max(0, Math.sin(t * 14.0)) * (0.65 + 0.35 * Math.sin(t * 4.8));
      const naturalSpeech = Math.max(0, (speechWave + syllableBurst) * 0.95);

      // Pulso extra caso evento onboundary tenha sido disparado
      const pulseDecay = Math.max(0, 1 - (Date.now() - this.lastSpeechPulse) / 220);
      this.targetMouthOpen = Math.min(1.0, Math.max(naturalSpeech, pulseDecay * 0.90));
    } else {
      this.targetMouthOpen = 0.0;
    }

    // Interpolação suave para abertura e fechamento orgânico
    this.mouthOpen += (this.targetMouthOpen - this.mouthOpen) * 0.32;

    // 2. Interpolação de Rotação 3D com Suavidade
    this.rotX += (this.targetRotX - this.rotX) * 0.08;
    this.rotY += (this.targetRotY - this.rotY) * 0.08;

    // Adiciona respiração natural e flutuação em standby
    const idleYaw = Math.sin(this.time * 0.7) * 0.045;
    const idlePitch = Math.cos(this.time * 0.9) * 0.025;
    const currentRotY = this.rotY + idleYaw;
    const currentRotX = this.rotX + idlePitch;

    // Cores temáticas por estado do sistema
    const colors = this.getStateColors();

    // 3. Projeção dos Nós Faciais
    const cosY = Math.cos(currentRotY);
    const sinY = Math.sin(currentRotY);
    const cosX = Math.cos(currentRotX);
    const sinX = Math.sin(currentRotX);

    for (let i = 0; i < this.nodes.length; i++) {
      const node = this.nodes[i];
      let curX = node.baseX;
      let curY = node.baseY;
      let curZ = node.baseZ;

      // Deslocamento Biomecânico da Boca e Mandíbula
      if (node.isMouthLower) {
        curY += this.mouthOpen * 25 * (node.mouthWeight || 1.0);
        curZ += this.mouthOpen * 5;
      }
      if (node.isMouthInner) {
        curY += this.mouthOpen * 20 * (node.mouthWeight || 1.0);
      }
      if (node.isMouthCorner) {
        curX += (node.baseX > 0 ? -1 : 1) * (this.mouthOpen * 3.5);
        curY += this.mouthOpen * 6;
      }
      if (node.isJaw) {
        curY += this.mouthOpen * 15 * (node.jawWeight || 1.0);
        curZ += this.mouthOpen * 4;
      }
      if (node.isChin) {
        curY += this.mouthOpen * 24 * (node.chinWeight || 1.0);
        curZ += this.mouthOpen * 6;
      }

      // Parallax dos Sensores Ópticos (olhar do robô)
      if (node.isPupil) {
        curX += this.lookOffsetX * 3.8;
        curY += this.lookOffsetY * 3.8;
      }

      // Respiração vertical global suave
      curY += Math.sin(this.time * 1.6) * 4.5;

      // Rotação Y (Yaw)
      const x1 = curX * cosY + curZ * sinY;
      const z1 = -curX * sinY + curZ * cosY;

      // Rotação X (Pitch)
      const y2 = curY * cosX - z1 * sinX;
      const z2 = curY * sinX + z1 * cosX;

      // Projeção em Perspectiva
      const scale = this.fov / (this.fov + z2 + this.cameraDistance);
      node.projX = this.centerX + x1 * scale;
      node.projY = this.centerY + y2 * scale;
      node.projScale = scale;
      node.projZ = z2;
    }

    // 4. Renderização do Halo Holográfico Orbital de Telemetria
    this.drawHolographicHalo(colors, currentRotY, currentRotX);

    // 5. Renderização das Arestas Poligonais (Linhas de Conexão Cyber)
    this.drawWireframeEdges(colors);

    // 6. Feixe Acústico de Fala dentro da Boca (Waveform Laser)
    if (this.mouthOpen > 0.08) {
      this.drawMouthAcousticWave(colors);
    }

    // 7. Renderização dos Nós Faciais com Bloom e Glow
    this.drawFaceNodes(colors);

    // 8. Renderização das Partículas Orbitais (Nuvem Quântica)
    this.drawAmbientParticles(colors, cosY, sinY, cosX, sinX);
  }

  getStateColors() {
    switch (this.state) {
      case 'LISTENING':
        return {
          primary: '#ff2a6d',
          secondary: '#ff7700',
          glow: 'rgba(255, 42, 109, 0.8)',
          line: 'rgba(255, 42, 109, 0.22)',
          particle: '#ff5588',
        };
      case 'THINKING':
        return {
          primary: '#a855f7',
          secondary: '#00f0ff',
          glow: 'rgba(168, 85, 247, 0.8)',
          line: 'rgba(168, 85, 247, 0.25)',
          particle: '#c084fc',
        };
      case 'SPEAKING':
        return {
          primary: '#00ffcc',
          secondary: '#38bdf8',
          glow: 'rgba(0, 255, 204, 0.9)',
          line: 'rgba(0, 255, 204, 0.28)',
          particle: '#7dd3fc',
        };
      case 'CODING':
        return {
          primary: '#ffb700',
          secondary: '#ff4400',
          glow: 'rgba(255, 183, 0, 0.85)',
          line: 'rgba(255, 183, 0, 0.25)',
          particle: '#fde047',
        };
      case 'STANDBY':
      default:
        return {
          primary: '#00f0ff',
          secondary: '#0077ff',
          glow: 'rgba(0, 240, 255, 0.75)',
          line: 'rgba(0, 240, 255, 0.20)',
          particle: '#38bdf8',
        };
    }
  }

  drawHolographicHalo(colors, rotY, rotX) {
    const ctx = this.ctx;
    ctx.save();
    
    // Anel orbital inclinado girando ao redor da cabeça
    const haloRadius = 145;
    const haloAngle = this.time * 0.45;
    const haloCenterY = this.centerY + Math.sin(this.time * 1.6) * 4.5 - 15;

    ctx.lineWidth = 1.0;
    ctx.strokeStyle = colors.line;
    ctx.shadowBlur = 6;
    ctx.shadowColor = colors.glow;

    // Elipse inclinada 3D
    ctx.beginPath();
    ctx.ellipse(
      this.centerX,
      haloCenterY,
      haloRadius * (1 + rotY * 0.15),
      haloRadius * 0.32,
      rotY * 0.2,
      0,
      Math.PI * 2
    );
    ctx.stroke();

    // Marcadores de tick rotativos no anel
    const numTicks = 16;
    for (let i = 0; i < numTicks; i++) {
      const a = haloAngle + (i * Math.PI * 2) / numTicks;
      const tx = this.centerX + Math.cos(a) * haloRadius * (1 + rotY * 0.15);
      const ty = haloCenterY + Math.sin(a) * (haloRadius * 0.32);
      
      const isCard = i % 4 === 0;
      ctx.fillStyle = isCard ? colors.primary : colors.secondary;
      ctx.beginPath();
      ctx.arc(tx, ty, isCard ? 2.2 : 1.2, 0, Math.PI * 2);
      ctx.fill();
    }

    ctx.restore();
  }

  drawWireframeEdges(colors) {
    const ctx = this.ctx;
    ctx.save();

    for (let i = 0; i < this.edges.length; i++) {
      const edge = this.edges[i];
      const n1 = this.nodes[edge.i1];
      const n2 = this.nodes[edge.i2];

      // Profundidade média da linha
      const avgZ = (n1.projZ + n2.projZ) / 2;
      const alpha = Math.max(0.08, Math.min(0.65, 0.35 + avgZ * 0.003));

      ctx.beginPath();
      ctx.moveTo(n1.projX, n1.projY);
      ctx.lineTo(n2.projX, n2.projY);

      ctx.strokeStyle = colors.line;
      ctx.globalAlpha = alpha;
      ctx.lineWidth = 1.0;
      ctx.stroke();
    }

    ctx.restore();
  }

  drawMouthAcousticWave(colors) {
    // Renderiza uma grade/onda luminosa dentro da boca que vibra durante a fala
    const ctx = this.ctx;
    ctx.save();

    const nLeft = this.nodes.find(n => n.id === 'mouth_corner_l');
    const nRight = this.nodes.find(n => n.id === 'mouth_corner_r');
    const nTop = this.nodes.find(n => n.id === 'lip_top_c');
    const nBot = this.nodes.find(n => n.id === 'lip_bot_c');

    if (nLeft && nRight && nTop && nBot) {
      const midX = (nLeft.projX + nRight.projX) / 2;
      const midY = (nTop.projY + nBot.projY) / 2;
      const mouthWidth = Math.abs(nRight.projX - nLeft.projX);
      const mouthHeight = Math.abs(nBot.projY - nTop.projY);

      // Onda acústica oscilante
      ctx.beginPath();
      ctx.strokeStyle = colors.primary;
      ctx.lineWidth = 1.8;
      ctx.shadowBlur = 10;
      ctx.shadowColor = colors.glow;

      const segments = 12;
      for (let s = 0; s <= segments; s++) {
        const u = s / segments;
        const px = nLeft.projX + (nRight.projX - nLeft.projX) * u;
        const wave = Math.sin(this.time * 22 + s * 1.4) * (mouthHeight * 0.38);
        const py = midY + wave;
        if (s === 0) ctx.moveTo(px, py);
        else ctx.lineTo(px, py);
      }
      ctx.stroke();

      // Brilho interior
      const grad = ctx.createRadialGradient(midX, midY, 1, midX, midY, mouthHeight * 1.2);
      grad.addColorStop(0, colors.glow);
      grad.addColorStop(1, 'transparent');
      ctx.fillStyle = grad;
      ctx.fillRect(midX - mouthWidth * 0.4, midY - mouthHeight, mouthWidth * 0.8, mouthHeight * 2);
    }

    ctx.restore();
  }

  drawFaceNodes(colors) {
    const ctx = this.ctx;

    // Ordena os nós por profundidade Z para profundidade visual realista
    const sortedNodes = [...this.nodes].sort((a, b) => a.projZ - b.projZ);

    for (let i = 0; i < sortedNodes.length; i++) {
      const node = sortedNodes[i];
      const scale = node.projScale;
      const zNorm = Math.max(0.3, Math.min(1.0, 0.65 + node.projZ * 0.0035));

      ctx.save();
      ctx.translate(node.projX, node.projY);

      if (node.isPupil) {
        // Sensor Óptico / Pupila Brilhante com anel biônico
        const pupilRadius = 3.8 * scale;
        ctx.shadowBlur = 14;
        ctx.shadowColor = colors.glow;
        ctx.fillStyle = '#ffffff';
        ctx.beginPath();
        ctx.arc(0, 0, pupilRadius, 0, Math.PI * 2);
        ctx.fill();

        // Anel do sensor
        ctx.strokeStyle = colors.primary;
        ctx.lineWidth = 1.4;
        ctx.beginPath();
        ctx.arc(0, 0, pupilRadius + 3.0 * scale, 0, Math.PI * 2);
        ctx.stroke();

      } else if (node.isCore) {
        // Núcleo Neural da Testa
        const coreSize = 2.8 * scale;
        ctx.shadowBlur = 12;
        ctx.shadowColor = colors.glow;
        ctx.fillStyle = colors.secondary;
        ctx.beginPath();
        ctx.arc(0, 0, coreSize, 0, Math.PI * 2);
        ctx.fill();

      } else if (node.isThroat) {
        // Transdutor de Voz no Pescoço
        const pulse = this.state === 'SPEAKING' ? 1 + Math.sin(this.time * 16) * 0.4 : 1.0;
        const throatSize = 3.6 * scale * pulse;
        ctx.shadowBlur = 14 * pulse;
        ctx.shadowColor = colors.glow;
        ctx.fillStyle = colors.primary;
        ctx.beginPath();
        ctx.arc(0, 0, throatSize, 0, Math.PI * 2);
        ctx.fill();

      } else if (node.isEye) {
        // Bordas dos olhos
        const r = 2.2 * scale;
        ctx.shadowBlur = 8;
        ctx.shadowColor = colors.glow;
        ctx.fillStyle = colors.primary;
        ctx.beginPath();
        ctx.arc(0, 0, r, 0, Math.PI * 2);
        ctx.fill();

      } else if (node.isMouthLower || node.isMouthUpper || node.isMouthCorner) {
        // Pontos articulados dos lábios
        const r = (node.isMouthLower ? 2.4 : 2.0) * scale;
        ctx.shadowBlur = this.state === 'SPEAKING' ? 10 : 5;
        ctx.shadowColor = colors.glow;
        ctx.fillStyle = this.state === 'SPEAKING' ? '#ffffff' : colors.primary;
        ctx.beginPath();
        ctx.arc(0, 0, r, 0, Math.PI * 2);
        ctx.fill();

      } else {
        // Nó padrão da carcaça do robô
        const r = (1.6 + (node.baseZ > 50 ? 0.6 : 0)) * scale;
        ctx.shadowBlur = 6;
        ctx.shadowColor = colors.glow;
        ctx.fillStyle = colors.primary;
        ctx.globalAlpha = zNorm;
        ctx.beginPath();
        ctx.arc(0, 0, r, 0, Math.PI * 2);
        ctx.fill();
      }

      ctx.restore();
    }
  }

  drawAmbientParticles(colors, cosY, sinY, cosX, sinX) {
    const ctx = this.ctx;
    ctx.save();

    for (let i = 0; i < this.ambientParticles.length; i++) {
      const p = this.ambientParticles[i];

      // Movimentação orbital suave das partículas
      const ang = this.time * 0.15 * p.speed + p.phase;
      const dist = Math.hypot(p.baseX, p.baseZ);
      const curX = Math.cos(ang) * dist;
      const curZ = Math.sin(ang) * dist;
      const curY = p.baseY + Math.sin(this.time * 1.2 + p.phase) * 12;

      // Rotação Y
      const x1 = curX * cosY + curZ * sinY;
      const z1 = -curX * sinY + curZ * cosY;

      // Rotação X
      const y2 = curY * cosX - z1 * sinX;
      const z2 = curY * sinX + z1 * cosX;

      const scale = this.fov / (this.fov + z2 + this.cameraDistance);
      const px = this.centerX + x1 * scale;
      const py = this.centerY + y2 * scale;

      const alpha = Math.max(0.12, Math.min(0.85, 0.45 + z2 * 0.003));
      const pSize = p.size * scale;

      ctx.beginPath();
      ctx.arc(px, py, pSize, 0, Math.PI * 2);
      ctx.fillStyle = p.glow ? colors.primary : colors.particle;
      ctx.globalAlpha = alpha;
      if (p.glow) {
        ctx.shadowBlur = 8;
        ctx.shadowColor = colors.glow;
      }
      ctx.fill();
    }

    ctx.restore();
  }
}

// Compatibilidade com app.js e exportação global
window.CyberFace = CyberFace;
window.ArcReactor = CyberFace;
