// ========================================
// JARVIS - Particle System
// Esfera de partículas que reage ao estado
// ========================================

class JarvisParticles {
    constructor(canvas) {
        this.canvas = canvas;
        this.ctx = canvas.getContext('2d');
        this.particles = [];
        this.connections = [];
        
        // Configurações
        this.particleCount = 800;
        this.baseRadius = 150;
        this.connectionDistance = 50;
        
        // Estado atual
        this.state = 'idle'; // idle, listening, processing, executing, error
        
        // Cores por estado (HEX para RGB)
        this.colors = {
            idle: { r: 0, g: 255, b: 255 },        // #00FFFF - Ciano
            listening: { r: 255, g: 165, b: 0 },    // #FFA500 - Laranja
            processing: { r: 0, g: 127, b: 255 },   // #007FFF - Azul
            executing: { r: 57, g: 255, b: 20 },    // #39FF14 - Verde
            error: { r: 255, g: 0, b: 0 }           // #FF0000 - Vermelho
        };
        
        // Cor atual (para transição suave)
        this.currentColor = { ...this.colors.idle };
        this.targetColor = { ...this.colors.idle };
        
        // Animação
        this.time = 0;
        this.pulsePhase = 0;
        this.rotationSpeed = 0.001;
        this.pulseSpeed = 0.02;
        this.pulseIntensity = 0.1;
        
        // Inicialização
        this.resize();
        this.init();
        this.animate();
        
        // Event listener para resize
        window.addEventListener('resize', () => this.resize());
    }
    
    resize() {
        this.canvas.width = window.innerWidth;
        this.canvas.height = window.innerHeight;
        this.centerX = this.canvas.width / 2;
        this.centerY = this.canvas.height / 2;
        
        // Ajustar raio baseado no tamanho da tela
        this.baseRadius = Math.min(this.canvas.width, this.canvas.height) * 0.3;
    }
    
    init() {
        this.particles = [];
        
        // Criar partículas em distribuição esférica
        for (let i = 0; i < this.particleCount; i++) {
            // Distribuição uniforme em esfera usando método de rejeição
            const theta = Math.random() * Math.PI * 2; // Ângulo horizontal
            const phi = Math.acos(2 * Math.random() - 1); // Ângulo vertical
            const r = this.baseRadius * (0.8 + Math.random() * 0.4); // Raio com variação
            
            this.particles.push({
                // Posição esférica
                theta: theta,
                phi: phi,
                baseR: r,
                r: r,
                
                // Posição cartesiana (calculada)
                x: 0,
                y: 0,
                z: 0,
                
                // Propriedades visuais
                size: 1 + Math.random() * 2,
                alpha: 0.3 + Math.random() * 0.7,
                
                // Velocidades individuais
                thetaSpeed: (Math.random() - 0.5) * 0.002,
                phiSpeed: (Math.random() - 0.5) * 0.001,
                
                // Offset para pulsação individual
                pulseOffset: Math.random() * Math.PI * 2
            });
        }
    }
    
    setState(newState) {
        const validStates = ['idle', 'listening', 'processing', 'executing', 'error'];
        if (!validStates.includes(newState)) return;
        
        this.state = newState;
        this.targetColor = { ...this.colors[newState] };
        
        // Ajustar animação por estado
        switch (newState) {
            case 'idle':
                this.pulseSpeed = 0.02;
                this.pulseIntensity = 0.1;
                this.rotationSpeed = 0.001;
                break;
            case 'listening':
                this.pulseSpeed = 0.08;
                this.pulseIntensity = 0.3;
                this.rotationSpeed = 0.003;
                break;
            case 'processing':
                this.pulseSpeed = 0.04;
                this.pulseIntensity = 0.15;
                this.rotationSpeed = 0.005;
                break;
            case 'executing':
                this.pulseSpeed = 0.1;
                this.pulseIntensity = 0.4;
                this.rotationSpeed = 0.002;
                break;
            case 'error':
                this.pulseSpeed = 0.15;
                this.pulseIntensity = 0.5;
                this.rotationSpeed = 0.001;
                break;
        }
        
        // Atualizar classe do body para CSS
        document.body.className = `state-${newState}`;
    }
    
    updateColor() {
        // Transição suave de cor
        const speed = this.state === 'listening' ? 0.3 : 0.05;
        
        this.currentColor.r += (this.targetColor.r - this.currentColor.r) * speed;
        this.currentColor.g += (this.targetColor.g - this.currentColor.g) * speed;
        this.currentColor.b += (this.targetColor.b - this.currentColor.b) * speed;
    }
    
    update() {
        this.time += 0.016; // ~60fps
        this.pulsePhase += this.pulseSpeed;
        
        this.updateColor();
        
        // Atualizar partículas
        for (const p of this.particles) {
            // Rotação
            p.theta += p.thetaSpeed + this.rotationSpeed;
            p.phi += p.phiSpeed;
            
            // Pulsação
            const pulse = Math.sin(this.pulsePhase + p.pulseOffset) * this.pulseIntensity;
            p.r = p.baseR * (1 + pulse);
            
            // Converter coordenadas esféricas para cartesianas
            p.x = p.r * Math.sin(p.phi) * Math.cos(p.theta);
            p.y = p.r * Math.sin(p.phi) * Math.sin(p.theta);
            p.z = p.r * Math.cos(p.phi);
        }
    }
    
    draw() {
        // Limpar canvas com fade (trail effect)
        this.ctx.fillStyle = 'rgba(10, 10, 15, 0.2)';
        this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
        
        const { r, g, b } = this.currentColor;
        
        // Ordenar partículas por Z para efeito de profundidade
        const sortedParticles = [...this.particles].sort((a, b) => a.z - b.z);
        
        // Desenhar conexões primeiro
        this.ctx.strokeStyle = `rgba(${r}, ${g}, ${b}, 0.1)`;
        this.ctx.lineWidth = 0.5;
        
        for (let i = 0; i < sortedParticles.length; i++) {
            const p1 = sortedParticles[i];
            const screen1 = this.project(p1);
            
            for (let j = i + 1; j < sortedParticles.length; j++) {
                const p2 = sortedParticles[j];
                
                // Calcular distância 3D
                const dx = p1.x - p2.x;
                const dy = p1.y - p2.y;
                const dz = p1.z - p2.z;
                const dist = Math.sqrt(dx * dx + dy * dy + dz * dz);
                
                if (dist < this.connectionDistance) {
                    const screen2 = this.project(p2);
                    const alpha = (1 - dist / this.connectionDistance) * 0.3;
                    
                    this.ctx.strokeStyle = `rgba(${r}, ${g}, ${b}, ${alpha})`;
                    this.ctx.beginPath();
                    this.ctx.moveTo(screen1.x, screen1.y);
                    this.ctx.lineTo(screen2.x, screen2.y);
                    this.ctx.stroke();
                }
            }
        }
        
        // Desenhar partículas
        for (const p of sortedParticles) {
            const screen = this.project(p);
            
            // Tamanho baseado na profundidade
            const scale = screen.scale;
            const size = p.size * scale;
            
            // Alpha baseado na profundidade
            const depthAlpha = 0.3 + scale * 0.7;
            const alpha = p.alpha * depthAlpha;
            
            // Glow
            const gradient = this.ctx.createRadialGradient(
                screen.x, screen.y, 0,
                screen.x, screen.y, size * 3
            );
            gradient.addColorStop(0, `rgba(${r}, ${g}, ${b}, ${alpha})`);
            gradient.addColorStop(0.5, `rgba(${r}, ${g}, ${b}, ${alpha * 0.3})`);
            gradient.addColorStop(1, `rgba(${r}, ${g}, ${b}, 0)`);
            
            this.ctx.fillStyle = gradient;
            this.ctx.beginPath();
            this.ctx.arc(screen.x, screen.y, size * 3, 0, Math.PI * 2);
            this.ctx.fill();
            
            // Core
            this.ctx.fillStyle = `rgba(${r}, ${g}, ${b}, ${alpha})`;
            this.ctx.beginPath();
            this.ctx.arc(screen.x, screen.y, size, 0, Math.PI * 2);
            this.ctx.fill();
        }
        
        // Glow central
        const centerGlow = this.ctx.createRadialGradient(
            this.centerX, this.centerY, 0,
            this.centerX, this.centerY, this.baseRadius * 0.5
        );
        centerGlow.addColorStop(0, `rgba(${r}, ${g}, ${b}, 0.1)`);
        centerGlow.addColorStop(1, `rgba(${r}, ${g}, ${b}, 0)`);
        
        this.ctx.fillStyle = centerGlow;
        this.ctx.beginPath();
        this.ctx.arc(this.centerX, this.centerY, this.baseRadius * 0.5, 0, Math.PI * 2);
        this.ctx.fill();
    }
    
    project(particle) {
        // Projeção perspectiva simples
        const fov = 500;
        const scale = fov / (fov + particle.z);
        
        return {
            x: this.centerX + particle.x * scale,
            y: this.centerY + particle.y * scale,
            scale: scale
        };
    }
    
    animate() {
        this.update();
        this.draw();
        requestAnimationFrame(() => this.animate());
    }
}

// Exportar para uso global
window.JarvisParticles = JarvisParticles;


