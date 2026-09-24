/**
 * J.A.R.V.I.S. WebGL 3D Robotic Face Engine (Three.js)
 * Rosto robótico mecatrônico futurista em WebGL real com placas metálicas chanfradas,
 * sensores ópticos dinâmicos, nuvem de partículas flutuantes e mandíbula articulada
 * com lip-sync em perfeita sincronia com a voz do Jarvis.
 */

class CyberFace {
  constructor(canvasId) {
    this.canvas = document.getElementById(canvasId);
    this.state = 'STANDBY'; // 'STANDBY' | 'LISTENING' | 'THINKING' | 'SPEAKING' | 'CODING'

    // Parâmetros de Áudio e Fala
    this.mouthOpen = 0.0;
    this.targetMouthOpen = 0.0;
    this.lastSpeechPulse = 0;

    // Rastreamento de Mouse / Parallax
    this.normMouseX = 0.0;
    this.normMouseY = 0.0;
    this.targetRotY = 0.0;
    this.targetRotX = 0.0;

    // Temporizador
    this.time = 0.0;

    // Inicialização do Universo 3D WebGL
    this.initWebGL();
    this.initMaterials();
    this.buildRobotFace();
    this.buildParticleCloud();
    this.initLighting();

    this.resize();
    window.addEventListener('resize', () => this.resize());
    window.addEventListener('mousemove', (e) => this.handleMouseMove(e));

    this.animate();
  }

  initWebGL() {
    this.scene = new THREE.Scene();

    const rect = this.canvas.getBoundingClientRect();
    const width = rect.width || 440;
    const height = rect.height || 440;

    this.camera = new THREE.PerspectiveCamera(40, width / height, 0.1, 100);
    this.camera.position.set(0, 0, 6.2);

    this.renderer = new THREE.WebGLRenderer({
      canvas: this.canvas,
      antialias: true,
      alpha: true,
      powerPreference: 'high-performance'
    });
    this.renderer.setSize(width, height, false);
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
    this.renderer.toneMappingExposure = 1.15;
  }

  resize() {
    const rect = this.canvas.getBoundingClientRect();
    const width = rect.width || 440;
    const height = rect.height || 440;

    this.camera.aspect = width / height;
    this.camera.updateProjectionMatrix();
    this.renderer.setSize(width, height, false);
  }

  handleMouseMove(e) {
    const rect = this.canvas.getBoundingClientRect();
    const canvasCenterX = rect.left + rect.width / 2;
    const canvasCenterY = rect.top + rect.height / 2;

    this.normMouseX = Math.max(-1, Math.min(1, (e.clientX - canvasCenterX) / (window.innerWidth / 2)));
    this.normMouseY = Math.max(-1, Math.min(1, (e.clientY - canvasCenterY) / (window.innerHeight / 2)));

    // Rotação suave da cabeça robótica
    this.targetRotY = this.normMouseX * 0.42; // Yaw (~24 graus)
    this.targetRotX = -this.normMouseY * 0.28; // Pitch (~16 graus)
  }

  pulseSpeech() {
    this.lastSpeechPulse = Date.now();
  }

  setState(newState) {
    this.state = newState;
    this.updateThemeColors();

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
      const theme = this.getThemeValues();
      label.style.borderColor = theme.cssPrimary;
      label.style.color = theme.cssPrimary;
    }
  }

  getThemeValues() {
    switch (this.state) {
      case 'LISTENING':
        return {
          primary: 0xff2a6d,
          secondary: 0xff7700,
          cssPrimary: '#ff2a6d',
          glowIntensity: 1.5,
        };
      case 'THINKING':
        return {
          primary: 0xa855f7,
          secondary: 0x00f0ff,
          cssPrimary: '#a855f7',
          glowIntensity: 1.6,
        };
      case 'SPEAKING':
        return {
          primary: 0x00ffcc,
          secondary: 0x38bdf8,
          cssPrimary: '#00ffcc',
          glowIntensity: 1.8,
        };
      case 'CODING':
        return {
          primary: 0xffb700,
          secondary: 0xff4400,
          cssPrimary: '#ffb700',
          glowIntensity: 1.5,
        };
      case 'STANDBY':
      default:
        return {
          primary: 0x00f0ff,
          secondary: 0x0077ff,
          cssPrimary: '#00f0ff',
          glowIntensity: 1.2,
        };
    }
  }

  updateThemeColors() {
    const theme = this.getThemeValues();

    if (this.glowMat) {
      this.glowMat.color.setHex(theme.primary);
      this.glowMat.emissive.setHex(theme.primary);
      this.glowMat.emissiveIntensity = theme.glowIntensity;
    }

    if (this.particleMat) {
      this.particleMat.color.setHex(theme.primary);
    }

    if (this.rimLightL) {
      this.rimLightL.color.setHex(theme.primary);
    }

    if (this.rimLightR) {
      this.rimLightR.color.setHex(theme.secondary);
    }

    if (this.eyes) {
      this.eyes.forEach(eye => {
        if (eye.light) eye.light.color.setHex(theme.primary);
      });
    }

    if (this.mouthLight) {
      this.mouthLight.color.setHex(theme.primary);
    }
  }

  initMaterials() {
    // 1. Placas Metálicas Principais (Titânio / Grafite Mecha)
    this.metalPlateMat = new THREE.MeshStandardMaterial({
      color: 0x111c2a,
      metalness: 0.88,
      roughness: 0.28,
      envMapIntensity: 1.0,
      flatShading: false,
    });

    // 2. Placas Metálicas Escuras / Rebaixos
    this.darkMetalMat = new THREE.MeshStandardMaterial({
      color: 0x070c14,
      metalness: 0.95,
      roughness: 0.18,
      flatShading: true,
    });

    // 3. Material Neon de Energia Cibernética (Emissive Glow)
    this.glowMat = new THREE.MeshStandardMaterial({
      color: 0x00f0ff,
      emissive: 0x00f0ff,
      emissiveIntensity: 1.2,
      roughness: 0.1,
      metalness: 0.1,
    });

    // 4. Lentes dos Sensores Ópticos (Olhos)
    this.eyeLensMat = new THREE.MeshStandardMaterial({
      color: 0xffffff,
      emissive: 0x00f0ff,
      emissiveIntensity: 2.0,
      metalness: 0.2,
      roughness: 0.05,
    });

    // 5. Wireframe Holográfico Sutil
    this.wireframeMat = new THREE.MeshBasicMaterial({
      color: 0x00f0ff,
      wireframe: true,
      transparent: true,
      opacity: 0.15,
    });

    // 6. Material da Nuvem de Partículas
    this.particleMat = new THREE.PointsMaterial({
      size: 0.045,
      color: 0x00f0ff,
      transparent: true,
      opacity: 0.75,
      blending: THREE.AdditiveBlending,
    });
  }

  buildRobotFace() {
    // Grupo que contém toda a cabeça robótica (rotaciona junto com o mouse)
    this.headGroup = new THREE.Group();
    this.headGroup.position.set(0, 0.1, 0);
    this.scene.add(this.headGroup);

    // ==========================================
    // 1. CRÂNIO & CAPACETE (Cranium & Helmet Dome)
    // ==========================================
    const craniumGeo = new THREE.SphereGeometry(1.45, 32, 24, 0, Math.PI * 2, 0, Math.PI * 0.55);
    craniumGeo.scale(1.0, 1.22, 1.15);
    const craniumMesh = new THREE.Mesh(craniumGeo, this.metalPlateMat);
    craniumMesh.position.set(0, 0.25, -0.15);
    this.headGroup.add(craniumMesh);

    // Sobreposição Wireframe no crânio (holographic overlay)
    const craniumWire = new THREE.Mesh(craniumGeo, this.wireframeMat);
    craniumWire.position.copy(craniumMesh.position);
    craniumWire.scale.multiplyScalar(1.002);
    this.headGroup.add(craniumWire);

    // Crista Central da Cabeça (Crest Plate)
    const crestGeo = new THREE.BoxGeometry(0.18, 0.35, 2.2);
    const crestMesh = new THREE.Mesh(crestGeo, this.darkMetalMat);
    crestMesh.position.set(0, 1.62, -0.15);
    crestMesh.rotation.x = -0.16;
    this.headGroup.add(crestMesh);

    // Fita de neon central na crista
    const crestNeonGeo = new THREE.BoxGeometry(0.04, 0.04, 2.0);
    const crestNeon = new THREE.Mesh(crestNeonGeo, this.glowMat);
    crestNeon.position.set(0, 1.82, -0.15);
    crestNeon.rotation.x = -0.16;
    this.headGroup.add(crestNeon);

    // Escudos Temporais Laterais
    [-1, 1].forEach(side => {
      const shieldGeo = new THREE.BoxGeometry(0.2, 1.15, 1.6);
      const shield = new THREE.Mesh(shieldGeo, this.metalPlateMat);
      shield.position.set(side * 1.48, 0.42, -0.2);
      shield.rotation.z = side * -0.07;
      this.headGroup.add(shield);
    });

    // ==========================================
    // 2. PLACAS DA TESTA & CHIPSET NEURAL
    // ==========================================
    // Placa da Testa Curvada
    const foreheadGeo = new THREE.CylinderGeometry(1.42, 1.48, 0.58, 20, 1, false, Math.PI * 0.22, Math.PI * 0.56);
    const forehead = new THREE.Mesh(foreheadGeo, this.metalPlateMat);
    forehead.position.set(0, 0.78, 0.02);
    forehead.rotation.y = -Math.PI * 0.5;
    this.headGroup.add(forehead);

    // Núcleo Neural Central Iluminado (Processador na testa)
    const coreGeo = new THREE.OctahedronGeometry(0.16, 0);
    const coreMesh = new THREE.Mesh(coreGeo, this.glowMat);
    coreMesh.position.set(0, 0.88, 1.45);
    this.headGroup.add(coreMesh);
    this.neuralCore = coreMesh;

    // ==========================================
    // 3. SOBRANCELHA & VISOR ESCURO
    // ==========================================
    // Barras angulares da sobrancelha robótica
    [-1, 1].forEach(side => {
      const browGeo = new THREE.BoxGeometry(0.9, 0.22, 0.45);
      const brow = new THREE.Mesh(browGeo, this.darkMetalMat);
      brow.position.set(side * 0.55, 0.46, 1.34);
      brow.rotation.z = side * -0.14;
      brow.rotation.y = side * 0.18;
      this.headGroup.add(brow);

      // Fita de neon da sobrancelha
      const browNeonGeo = new THREE.BoxGeometry(0.85, 0.03, 0.05);
      const browNeon = new THREE.Mesh(browNeonGeo, this.glowMat);
      browNeon.position.set(side * 0.55, 0.55, 1.48);
      browNeon.rotation.copy(brow.rotation);
      this.headGroup.add(browNeon);
    });

    // Visor Preto de Fundo (Atrás dos olhos)
    const visorGeo = new THREE.BoxGeometry(2.1, 0.58, 0.35);
    const visor = new THREE.Mesh(visorGeo, this.darkMetalMat);
    visor.position.set(0, 0.22, 1.25);
    this.headGroup.add(visor);

    // ==========================================
    // 4. SENSORES ÓPTICOS CYBERNETIC (OLHOS)
    // ==========================================
    this.eyes = [];
    [-1, 1].forEach(side => {
      const eyeSocketGroup = new THREE.Group();
      eyeSocketGroup.position.set(side * 0.58, 0.22, 1.36);

      // Aro chanfrado metálico
      const bezelGeo = new THREE.CylinderGeometry(0.24, 0.28, 0.12, 18);
      bezelGeo.rotateX(Math.PI * 0.5);
      const bezel = new THREE.Mesh(bezelGeo, this.darkMetalMat);
      eyeSocketGroup.add(bezel);

      // Anel de neon brilhante
      const ringGeo = new THREE.TorusGeometry(0.22, 0.035, 10, 24);
      const ring = new THREE.Mesh(ringGeo, this.glowMat);
      eyeSocketGroup.add(ring);

      // Lente óptica central
      const lensGeo = new THREE.SphereGeometry(0.14, 18, 18);
      const lens = new THREE.Mesh(lensGeo, this.eyeLensMat);
      eyeSocketGroup.add(lens);

      // Ponto focal / Pupila que mira no mouse
      const pupilGeo = new THREE.SphereGeometry(0.065, 12, 12);
      const pupil = new THREE.Mesh(pupilGeo, new THREE.MeshBasicMaterial({ color: 0xffffff }));
      pupil.position.z = 0.09;
      eyeSocketGroup.add(pupil);

      // Luz emitida por cada olho
      const eyeLight = new THREE.PointLight(0x00f0ff, 1.4, 3.8);
      eyeLight.position.set(0, 0, 0.22);
      eyeSocketGroup.add(eyeLight);

      this.headGroup.add(eyeSocketGroup);
      this.eyes.push({
        group: eyeSocketGroup,
        lens,
        pupil,
        light: eyeLight,
        basePos: eyeSocketGroup.position.clone()
      });
    });

    // ==========================================
    // 5. BOCHECHAS CHANFRADAS (Cheekplates)
    // ==========================================
    [-1, 1].forEach(side => {
      const cheekGeo = new THREE.BoxGeometry(0.75, 0.95, 0.4);
      const cheek = new THREE.Mesh(cheekGeo, this.metalPlateMat);
      cheek.position.set(side * 0.96, -0.26, 1.15);
      cheek.rotation.y = side * 0.42;
      cheek.rotation.z = side * 0.15;
      this.headGroup.add(cheek);

      // Costura luminosa de neon na bochecha
      const seamGeo = new THREE.BoxGeometry(0.04, 0.88, 0.04);
      const seam = new THREE.Mesh(seamGeo, this.glowMat);
      seam.position.set(side * 1.08, -0.26, 1.30);
      seam.rotation.copy(cheek.rotation);
      this.headGroup.add(seam);
    });

    // ==========================================
    // 6. NARIZ & RESPIRADOR MECÂNICO
    // ==========================================
    // Ponte do nariz
    const noseBridgeGeo = new THREE.BoxGeometry(0.24, 0.65, 0.32);
    const noseBridge = new THREE.Mesh(noseBridgeGeo, this.darkMetalMat);
    noseBridge.position.set(0, 0.04, 1.44);
    noseBridge.rotation.x = -0.16;
    this.headGroup.add(noseBridge);

    // Respirador / Ventilação
    const ventBaseGeo = new THREE.ConeGeometry(0.38, 0.45, 4);
    ventBaseGeo.rotateY(Math.PI * 0.25);
    ventBaseGeo.rotateX(Math.PI);
    const ventBase = new THREE.Mesh(ventBaseGeo, this.darkMetalMat);
    ventBase.position.set(0, -0.32, 1.48);
    this.headGroup.add(ventBase);

    // Aletas horizontais do respirador com brilho
    for (let i = 0; i < 3; i++) {
      const slatGeo = new THREE.BoxGeometry(0.30 - i * 0.07, 0.035, 0.08);
      const slat = new THREE.Mesh(slatGeo, this.glowMat);
      slat.position.set(0, -0.23 - i * 0.08, 1.55 - i * 0.03);
      this.headGroup.add(slat);
    }

    // ==========================================
    // 7. ORELHAS / TURBINAS AUDITIVAS LATERAIS
    // ==========================================
    this.earRings = [];
    [-1, 1].forEach(side => {
      const earGroup = new THREE.Group();
      earGroup.position.set(side * 1.62, 0.06, -0.12);
      earGroup.rotation.y = side * Math.PI * 0.5;

      const housingGeo = new THREE.CylinderGeometry(0.48, 0.52, 0.25, 24);
      const housing = new THREE.Mesh(housingGeo, this.darkMetalMat);
      earGroup.add(housing);

      const innerRingGeo = new THREE.TorusGeometry(0.36, 0.04, 8, 24);
      const innerRing = new THREE.Mesh(innerRingGeo, this.glowMat);
      innerRing.rotation.x = Math.PI * 0.5;
      earGroup.add(innerRing);

      const centerCoreGeo = new THREE.CylinderGeometry(0.18, 0.18, 0.3, 16);
      const centerCore = new THREE.Mesh(centerCoreGeo, this.metalPlateMat);
      earGroup.add(centerCore);

      this.headGroup.add(earGroup);
      this.earRings.push(innerRing);
    });

    // ==========================================
    // 8. MANDÍBULA ARTICULADA & BOCA QUE FALA (Lip-Sync)
    // ==========================================
    // Lábio Superior Fixo
    const upperLipGeo = new THREE.BoxGeometry(0.68, 0.12, 0.32);
    const upperLip = new THREE.Mesh(upperLipGeo, this.darkMetalMat);
    upperLip.position.set(0, -0.54, 1.40);
    this.headGroup.add(upperLip);

    // Fita de neon no lábio superior
    const upperLipNeonGeo = new THREE.BoxGeometry(0.64, 0.025, 0.04);
    const upperLipNeon = new THREE.Mesh(upperLipNeonGeo, this.glowMat);
    upperLipNeon.position.set(0, -0.49, 1.48);
    this.headGroup.add(upperLipNeon);

    // Cavidade interna da boca (recesso acústico)
    const mouthCavityGeo = new THREE.BoxGeometry(0.68, 0.38, 0.42);
    const mouthCavity = new THREE.Mesh(mouthCavityGeo, new THREE.MeshBasicMaterial({ color: 0x01050a }));
    mouthCavity.position.set(0, -0.66, 1.25);
    this.headGroup.add(mouthCavity);

    // Luz pontual no interior da boca (acende e vibra quando fala!)
    this.mouthLight = new THREE.PointLight(0x00ffcc, 0.0, 3.0);
    this.mouthLight.position.set(0, -0.66, 1.38);
    this.headGroup.add(this.mouthLight);

    // Barras de Equalizador de Áudio (Voice Matrix Teeth)
    this.audioBars = [];
    const barCount = 7;
    for (let i = 0; i < barCount; i++) {
      const barGeo = new THREE.BoxGeometry(0.05, 0.18, 0.05);
      const barMesh = new THREE.Mesh(barGeo, this.glowMat);
      const u = (i - (barCount - 1) / 2) * 0.085;
      barMesh.position.set(u, -0.64, 1.36);
      this.headGroup.add(barMesh);
      this.audioBars.push(barMesh);
    }

    // GRUPO DA MANDÍBULA MÓVEL (Hinged at the Jaw Joint)
    this.jawGroup = new THREE.Group();
    // Pivô de rotação posicionado na articulação temporomandibular
    this.jawGroup.position.set(0, -0.42, 0.35);
    this.headGroup.add(this.jawGroup);

    // Lábio Inferior Móvel
    const lowerLipGeo = new THREE.BoxGeometry(0.65, 0.12, 0.30);
    const lowerLip = new THREE.Mesh(lowerLipGeo, this.darkMetalMat);
    lowerLip.position.set(0, -0.22, 1.05);
    this.jawGroup.add(lowerLip);

    // Fita de neon no lábio inferior
    const lowerLipNeonGeo = new THREE.BoxGeometry(0.60, 0.025, 0.04);
    const lowerLipNeon = new THREE.Mesh(lowerLipNeonGeo, this.glowMat);
    lowerLipNeon.position.set(0, -0.27, 1.15);
    this.jawGroup.add(lowerLipNeon);

    // Placa do Queixo Angular (Chiseled Chin)
    const chinGeo = new THREE.BoxGeometry(0.72, 0.58, 0.65);
    const chin = new THREE.Mesh(chinGeo, this.metalPlateMat);
    chin.position.set(0, -0.54, 0.98);
    chin.rotation.x = -0.26;
    this.jawGroup.add(chin);

    // Linha de neon no queixo
    const chinGlowGeo = new THREE.BoxGeometry(0.48, 0.05, 0.05);
    const chinGlow = new THREE.Mesh(chinGlowGeo, this.glowMat);
    chinGlow.position.set(0, -0.66, 1.18);
    this.jawGroup.add(chinGlow);

    // Vigas laterais da mandíbula que conectam à articulação
    [-1, 1].forEach(side => {
      const strutGeo = new THREE.BoxGeometry(0.2, 0.35, 1.25);
      const strut = new THREE.Mesh(strutGeo, this.darkMetalMat);
      strut.position.set(side * 0.88, -0.35, 0.45);
      strut.rotation.y = side * 0.32;
      strut.rotation.x = 0.16;
      this.jawGroup.add(strut);
    });

    // ==========================================
    // 9. PESCOÇO & COLUNA ESPINHAL ROBÓTICA
    // ==========================================
    const neckGeo = new THREE.CylinderGeometry(0.65, 0.8, 1.15, 20);
    const neck = new THREE.Mesh(neckGeo, this.darkMetalMat);
    neck.position.set(0, -1.25, -0.2);
    this.headGroup.add(neck);

    // Pistões hidráulicos do pescoço
    [-1, 1].forEach(side => {
      const pistonGeo = new THREE.CylinderGeometry(0.11, 0.11, 0.95, 14);
      const piston = new THREE.Mesh(pistonGeo, this.metalPlateMat);
      piston.position.set(side * 0.78, -1.18, 0.02);
      piston.rotation.z = side * 0.22;
      this.headGroup.add(piston);
    });
  }

  buildParticleCloud() {
    // 1.500 Partículas Holográficas Volumétricas Flutuando no Espaço ao Redor da Cabeça
    const pCount = 1500;
    const posArray = new Float32Array(pCount * 3);
    this.particleOriginalPos = new Float32Array(pCount * 3);
    this.particleSpeeds = new Float32Array(pCount);

    for (let i = 0; i < pCount; i++) {
      const theta = Math.random() * Math.PI * 2;
      const phi = (Math.random() - 0.5) * Math.PI;
      const radius = 1.9 + Math.random() * 2.6;

      const x = radius * Math.cos(phi) * Math.sin(theta);
      const y = radius * Math.sin(phi);
      const z = radius * Math.cos(phi) * Math.cos(theta);

      posArray[i * 3] = x;
      posArray[i * 3 + 1] = y;
      posArray[i * 3 + 2] = z;

      this.particleOriginalPos[i * 3] = x;
      this.particleOriginalPos[i * 3 + 1] = y;
      this.particleOriginalPos[i * 3 + 2] = z;

      this.particleSpeeds[i] = 0.3 + Math.random() * 0.7;
    }

    const pGeo = new THREE.BufferGeometry();
    pGeo.setAttribute('position', new THREE.BufferAttribute(posArray, 3));
    this.particleSystem = new THREE.Points(pGeo, this.particleMat);
    this.scene.add(this.particleSystem);
  }

  initLighting() {
    // 1. Luz Ambiente
    this.ambientLight = new THREE.AmbientLight(0x0a1420, 1.4);
    this.scene.add(this.ambientLight);

    // 2. Luz Direcional Principal (Key Light)
    this.keyLight = new THREE.DirectionalLight(0xe0f7ff, 2.2);
    this.keyLight.position.set(2, 4, 5);
    this.scene.add(this.keyLight);

    // 3. Rim Light Esquerda (Cyan)
    this.rimLightL = new THREE.PointLight(0x00f0ff, 2.5, 8.0);
    this.rimLightL.position.set(-3.5, 2.0, 1.5);
    this.scene.add(this.rimLightL);

    // 4. Rim Light Direita (Blue)
    this.rimLightR = new THREE.PointLight(0x0077ff, 2.5, 8.0);
    this.rimLightR.position.set(3.5, -1.0, 1.5);
    this.scene.add(this.rimLightR);
  }

  animate() {
    requestAnimationFrame(() => this.animate());

    this.time += 0.032;

    // 1. Articulação da Mandíbula e Lip-Sync ao Falar
    if (this.state === 'SPEAKING') {
      const t = this.time;
      // Oscilador harmônico multiespectral com cadência orgânica de fala
      const speechWave = Math.sin(t * 12.0) * 0.45 + Math.sin(t * 19.5) * 0.35 + Math.sin(t * 7.2) * 0.20;
      const syllableBurst = Math.max(0, Math.sin(t * 15.0)) * (0.7 + 0.3 * Math.sin(t * 4.5));
      const naturalSpeech = Math.max(0, (speechWave + syllableBurst) * 1.0);

      // Impulso extra caso evento onboundary tenha sido emitido pelo TTS
      const pulseDecay = Math.max(0, 1 - (Date.now() - this.lastSpeechPulse) / 240);
      this.targetMouthOpen = Math.min(1.0, Math.max(naturalSpeech, pulseDecay * 0.95));

      // Iluminação interna da cavidade bucal ao falar
      this.mouthLight.intensity = this.mouthOpen * 3.2;

      // Barras de equalizador de voz dentro da boca
      this.audioBars.forEach((bar, idx) => {
        const barH = 0.5 + Math.sin(t * 24 + idx * 1.4) * 0.5;
        bar.scale.y = Math.max(0.15, this.mouthOpen * (0.7 + barH * 2.3));
      });
    } else {
      this.targetMouthOpen = 0.0;
      this.mouthLight.intensity = 0.0;
      this.audioBars.forEach(bar => { bar.scale.y = 0.15; });
    }

    // Interpolação suave e elástica da mandíbula
    this.mouthOpen += (this.targetMouthOpen - this.mouthOpen) * 0.36;
    this.jawGroup.rotation.x = -this.mouthOpen * 0.38; // Movimento amplo, claro e visível da boca!
    this.jawGroup.position.z = 0.35 + this.mouthOpen * 0.08;

    // 2. Rastreamento Suave do Cursor (Parallax 3D da Cabeça)
    this.headGroup.rotation.y += (this.targetRotY - this.headGroup.rotation.y) * 0.07;
    this.headGroup.rotation.x += (this.targetRotX - this.headGroup.rotation.x) * 0.07;

    // Respiração / Flutuação Mecânica
    this.headGroup.position.y = 0.1 + Math.sin(this.time * 1.6) * 0.10;

    // Pupilas acompanham a mira do mouse
    if (this.eyes) {
      this.eyes.forEach(eye => {
        eye.pupil.position.x = this.normMouseX * 0.065;
        eye.pupil.position.y = -this.normMouseY * 0.065;
      });
    }

    // Rotação dos anéis das orelhas
    if (this.earRings) {
      this.earRings.forEach((ring, idx) => {
        ring.rotation.z += (idx === 0 ? 0.03 : -0.03);
      });
    }

    // Pulso do núcleo neural na testa
    if (this.neuralCore) {
      const corePulse = 1.0 + Math.sin(this.time * 4) * 0.15;
      this.neuralCore.scale.setScalar(corePulse);
    }

    // 3. Animação da Nuvem de Partículas Flutuantes
    if (this.particleSystem) {
      const pos = this.particleSystem.geometry.attributes.position.array;
      const count = pos.length / 3;

      for (let i = 0; i < count; i++) {
        const speed = this.particleSpeeds[i];
        const origX = this.particleOriginalPos[i * 3];
        const origY = this.particleOriginalPos[i * 3 + 1];
        const origZ = this.particleOriginalPos[i * 3 + 2];

        // Movimento orbital fluido e ondulação tridimensional
        const angle = this.time * 0.12 * speed + i * 0.02;
        const radius = Math.hypot(origX, origZ);

        pos[i * 3] = Math.cos(angle) * radius;
        pos[i * 3 + 1] = origY + Math.sin(this.time * 1.5 + i) * 0.14;
        pos[i * 3 + 2] = Math.sin(angle) * radius;
      }
      this.particleSystem.geometry.attributes.position.needsUpdate = true;
    }

    // 4. Renderização do Frame WebGL
    this.renderer.render(this.scene, this.camera);
  }
}

// Compatibilidade com app.js e exportação global
window.CyberFace = CyberFace;
window.ArcReactor = CyberFace;
