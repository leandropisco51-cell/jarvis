/**
 * J.A.R.V.I.S. Arc Reactor Visualizer & Hologram
 * Renderização gráfica em Canvas 2D dos anéis concêntricos do reator e partículas
 */

class ArcReactor {
  constructor(canvasId) {
    this.canvas = document.getElementById(canvasId);
    this.ctx = this.canvas.getContext('2d');
    this.state = 'STANDBY'; // 'STANDBY' | 'LISTENING' | 'THINKING' | 'SPEAKING'
    this.angle1 = 0;
    this.angle2 = 0;
    this.angle3 = 0;
    this.pulse = 0;
    this.particles = [];
    this.numParticles = 40;
    this.audioFreqs = null;
    this.audioVolume = 0;

    this.resize();
    window.addEventListener('resize', () => this.resize());
    this.initParticles();
    this.animate();
  }

  resize() {
    const rect = this.canvas.getBoundingClientRect();
    const dpr = window.devicePixelRatio || 1;
    // Garante que o canvas sempre seja perfeitamente simétrico e circular
    const size = Math.floor(Math.min(rect.width, rect.height)) || 380;
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
    this.centerY = size / 2;
    this.baseRadius = size * 0.40;
  }

  initParticles() {
    this.particles = [];
    for (let i = 0; i < this.numParticles; i++) {
      this.particles.push({
        angle: Math.random() * Math.PI * 2,
        dist: Math.random() * this.baseRadius * 0.8,
        speed: 0.005 + Math.random() * 0.015,
        size: 1 + Math.random() * 2,
        alpha: 0.2 + Math.random() * 0.6,
      });
    }
  }

  setState(newState) {
    this.state = newState;
    if (newState !== 'SPEAKING') {
      this.audioFreqs = null;
      this.audioVolume = 0;
    }
    const label = document.getElementById('reactorStateText');
    if (label) {
      const stateMap = {
        STANDBY: 'SISTEMAS ONLINE // STANDBY',
        LISTENING: 'OUVINDO COMANDOS...',
        THINKING: 'PROCESSANDO RESPOSTA...',
        SPEAKING: 'VOZ NEURAL // TRANSMITINDO...',
        CODING: 'AUTO-EVOLUÇÃO // CODIFICANDO...',
      };
      label.textContent = stateMap[newState] || newState;
      const stateColor = newState === 'LISTENING' ? '#ff3366' : (newState === 'CODING' ? '#ffb700' : '#00f0ff');
      label.style.borderColor = stateColor;
      label.style.color = stateColor;
    }
  }

  updateAudioData(freqArray) {
    if (!freqArray || freqArray.length === 0) {
      this.audioFreqs = null;
      this.audioVolume = 0;
      return;
    }
    this.audioFreqs = freqArray;
    let sum = 0;
    const count = Math.min(freqArray.length, 48);
    for (let i = 0; i < count; i++) {
      sum += freqArray[i];
    }
    this.audioVolume = (sum / count) / 255.0;
  }

  animate() {
    requestAnimationFrame(() => this.animate());

    this.ctx.clearRect(0, 0, this.width, this.height);

    // Ajusta velocidades com base no estado
    let speedMult = 1;
    let mainColor = '#00f0ff';
    let secColor = '#0077ff';

    if (this.state === 'LISTENING') {
      speedMult = 1.4;
      mainColor = '#ff3366';
      secColor = '#ff7700';
    } else if (this.state === 'THINKING') {
      speedMult = 3.0;
      mainColor = '#00f0ff';
      secColor = '#7928ca';
    } else if (this.state === 'SPEAKING') {
      speedMult = 1.8 + this.audioVolume * 1.2;
      mainColor = '#00ffaa';
      secColor = '#00f0ff';
    } else if (this.state === 'CODING') {
      speedMult = 2.5;
      mainColor = '#ffb700';
      secColor = '#ff5500';
    }

    this.angle1 += 0.006 * speedMult;
    this.angle2 -= 0.010 * speedMult;
    this.angle3 += 0.015 * speedMult;
    this.pulse += 0.04 * speedMult;

    const pulseVal = Math.sin(this.pulse) * 6 + (this.state === 'SPEAKING' ? this.audioVolume * 18 : 0);

    // 1. Partículas orbitais
    this.drawParticles(mainColor);

    // 2. Anel externo com marcas táteis
    this.drawOuterRing(this.baseRadius, this.angle1, mainColor, secColor);

    // 3. Anel intermediário com segmentos
    this.drawMiddleRing(this.baseRadius * 0.72, this.angle2, secColor);

    // 4. Anel de ondas de áudio
    this.drawWaveRing(this.baseRadius * 0.52, this.angle3, mainColor, pulseVal);

    // 5. Núcleo central brilhante (Arc Core)
    this.drawCore(this.baseRadius * 0.28, mainColor, pulseVal);
  }

  drawParticles(color) {
    this.ctx.fillStyle = color;
    for (let p of this.particles) {
      p.angle += p.speed;
      const x = this.centerX + Math.cos(p.angle) * p.dist;
      const y = this.centerY + Math.sin(p.angle) * p.dist;
      this.ctx.globalAlpha = p.alpha;
      this.ctx.beginPath();
      this.ctx.arc(x, y, p.size, 0, Math.PI * 2);
      this.ctx.fill();
    }
    this.ctx.globalAlpha = 1.0;
  }

  drawOuterRing(r, angle, color, secColor) {
    const ctx = this.ctx;
    ctx.save();
    ctx.translate(this.centerX, this.centerY);
    ctx.rotate(angle);

    // Círculo base fino
    ctx.strokeStyle = 'rgba(0, 240, 255, 0.15)';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.arc(0, 0, r, 0, Math.PI * 2);
    ctx.stroke();

    // 4 arcos de destaque
    ctx.strokeStyle = color;
    ctx.lineWidth = 3;
    ctx.shadowBlur = 10;
    ctx.shadowColor = color;
    for (let i = 0; i < 4; i++) {
      ctx.beginPath();
      ctx.arc(0, 0, r, (i * Math.PI) / 2 + 0.1, (i * Math.PI) / 2 + 0.6);
      ctx.stroke();
    }

    // Traços radiais (ticks)
    ctx.shadowBlur = 0;
    ctx.strokeStyle = 'rgba(0, 240, 255, 0.4)';
    ctx.lineWidth = 1.5;
    const ticks = 48;
    for (let i = 0; i < ticks; i++) {
      const a = (i * Math.PI * 2) / ticks;
      const len = i % 4 === 0 ? 8 : 4;
      const x1 = Math.cos(a) * (r - len);
      const y1 = Math.sin(a) * (r - len);
      const x2 = Math.cos(a) * r;
      const y2 = Math.sin(a) * r;
      ctx.beginPath();
      ctx.moveTo(x1, y1);
      ctx.lineTo(x2, y2);
      ctx.stroke();
    }
    ctx.restore();
  }

  drawMiddleRing(r, angle, color) {
    const ctx = this.ctx;
    ctx.save();
    ctx.translate(this.centerX, this.centerY);
    ctx.rotate(angle);

    ctx.strokeStyle = color;
    ctx.lineWidth = 2;
    ctx.shadowBlur = 8;
    ctx.shadowColor = color;

    // Segmentos do reator triangular
    const segments = 12;
    for (let i = 0; i < segments; i++) {
      const start = (i * Math.PI * 2) / segments;
      const end = start + (Math.PI * 2) / segments * 0.65;
      ctx.beginPath();
      ctx.arc(0, 0, r, start, end);
      ctx.stroke();
    }
    ctx.restore();
  }

  drawWaveRing(r, angle, color, pulse) {
    const ctx = this.ctx;
    ctx.save();
    ctx.translate(this.centerX, this.centerY);
    ctx.rotate(angle);

    const bars = 36;
    ctx.strokeStyle = color;
    ctx.lineWidth = 2;
    for (let i = 0; i < bars; i++) {
      const a = (i * Math.PI * 2) / bars;
      let barH = 5 + Math.sin(i * 0.8 + this.pulse) * 4;
      if (this.state === 'SPEAKING' && this.audioFreqs) {
        const binIdx = (i * 2) % Math.min(this.audioFreqs.length, 48);
        const freqNorm = this.audioFreqs[binIdx] / 255.0;
        barH = 4 + freqNorm * 28 + Math.abs(Math.sin(i * 1.2 + this.pulse)) * 4;
      } else if (this.state === 'SPEAKING' || this.state === 'LISTENING') {
        barH += Math.abs(Math.sin(i * 1.5 + this.pulse * 2)) * 12;
      }
      const x1 = Math.cos(a) * (r - barH / 2);
      const y1 = Math.sin(a) * (r - barH / 2);
      const x2 = Math.cos(a) * (r + barH / 2);
      const y2 = Math.sin(a) * (r + barH / 2);
      ctx.beginPath();
      ctx.moveTo(x1, y1);
      ctx.lineTo(x2, y2);
      ctx.stroke();
    }
    ctx.restore();
  }

  drawCore(r, color, pulse) {
    const ctx = this.ctx;
    ctx.save();
    ctx.translate(this.centerX, this.centerY);

    const effR = Math.max(5, r + pulse);

    // Gradiente radial intenso no centro
    const grad = ctx.createRadialGradient(0, 0, 0, 0, 0, effR * 1.8);
    grad.addColorStop(0, '#ffffff');
    grad.addColorStop(0.3, color);
    grad.addColorStop(0.8, 'rgba(0, 119, 255, 0.4)');
    grad.addColorStop(1, 'transparent');

    ctx.fillStyle = grad;
    ctx.beginPath();
    ctx.arc(0, 0, effR * 1.8, 0, Math.PI * 2);
    ctx.fill();

    // Triângulo / hexágono interno holográfico
    ctx.strokeStyle = '#ffffff';
    ctx.lineWidth = 2;
    ctx.shadowBlur = 12;
    ctx.shadowColor = color;
    ctx.beginPath();
    for (let i = 0; i < 3; i++) {
      const a = (i * Math.PI * 2) / 3 - Math.PI / 2 + this.angle3 * 0.5;
      const x = Math.cos(a) * effR * 0.85;
      const y = Math.sin(a) * effR * 0.85;
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    }
    ctx.closePath();
    ctx.stroke();

    ctx.restore();
  }
}

window.ArcReactor = ArcReactor;
