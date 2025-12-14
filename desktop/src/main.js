// ========================================
// JARVIS - Main Interface Controller
// Conecta com o backend Python via WebSocket
// ========================================

class JarvisInterface {
    constructor() {
        this.particles = null;
        this.ws = null;
        this.statusText = document.getElementById('status-text');
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 10;
        
        this.init();
    }
    
    init() {
        // Inicializar partículas
        const canvas = document.getElementById('particles');
        this.particles = new JarvisParticles(canvas);
        
        // Conectar ao backend
        this.connect();
        
        // Estado inicial
        this.setState('idle', 'Aguardando "Jarvis"...');
        
        // Keyboard shortcuts para debug
        document.addEventListener('keydown', (e) => this.handleKeyboard(e));
    }
    
    connect() {
        const wsUrl = 'ws://127.0.0.1:8765/ws';
        
        try {
            this.ws = new WebSocket(wsUrl);
            
            this.ws.onopen = () => {
                console.log('✅ Conectado ao JARVIS backend');
                this.reconnectAttempts = 0;
                this.setState('idle', 'Aguardando "Jarvis"...');
            };
            
            this.ws.onmessage = (event) => {
                this.handleMessage(JSON.parse(event.data));
            };
            
            this.ws.onclose = () => {
                console.log('❌ Conexão perdida');
                this.setState('error', 'Desconectado');
                this.scheduleReconnect();
            };
            
            this.ws.onerror = (error) => {
                console.error('Erro WebSocket:', error);
            };
            
        } catch (error) {
            console.error('Erro ao conectar:', error);
            this.setState('error', 'Erro de conexão');
            this.scheduleReconnect();
        }
    }
    
    scheduleReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            const delay = Math.min(1000 * this.reconnectAttempts, 5000);
            
            console.log(`Reconectando em ${delay/1000}s... (tentativa ${this.reconnectAttempts})`);
            
            setTimeout(() => this.connect(), delay);
        } else {
            this.setState('error', 'Backend offline');
        }
    }
    
    handleMessage(data) {
        console.log('📩 Mensagem:', data);
        
        switch (data.type) {
            case 'state':
                this.setState(data.state, data.text);
                break;
                
            case 'transcription':
                this.setState('processing', `"${data.text}"`);
                break;
                
            case 'response':
                this.setState('executing', data.text);
                // Voltar ao idle após um tempo
                setTimeout(() => {
                    this.setState('idle', 'Aguardando "Jarvis"...');
                }, 3000);
                break;
                
            case 'error':
                this.setState('error', data.text || 'Erro');
                setTimeout(() => {
                    this.setState('idle', 'Aguardando "Jarvis"...');
                }, 3000);
                break;
        }
    }
    
    setState(state, text = '') {
        // Atualizar partículas
        if (this.particles) {
            this.particles.setState(state);
        }
        
        // Atualizar texto
        if (this.statusText && text) {
            this.statusText.textContent = text;
        }
        
        console.log(`Estado: ${state} - ${text}`);
    }
    
    send(data) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(data));
        }
    }
    
    handleKeyboard(e) {
        // Teclas de debug (1-5 para mudar estados)
        if (e.key >= '1' && e.key <= '5') {
            const states = ['idle', 'listening', 'processing', 'executing', 'error'];
            const texts = [
                'Aguardando "Jarvis"...',
                'Escutando...',
                'Processando...',
                'Executando...',
                'Erro!'
            ];
            const index = parseInt(e.key) - 1;
            this.setState(states[index], texts[index]);
        }
        
        // ESC para fechar (Tauri)
        if (e.key === 'Escape') {
            if (window.__TAURI__) {
                window.__TAURI__.window.getCurrent().close();
            }
        }
    }
}

// Inicializar quando DOM estiver pronto
document.addEventListener('DOMContentLoaded', () => {
    window.jarvis = new JarvisInterface();
    
    // Mensagem no console
    console.log(`
    ╔═══════════════════════════════════════╗
    ║         J.A.R.V.I.S. Interface        ║
    ║                                       ║
    ║  Teclas de debug:                     ║
    ║  1 - Idle (Aguardando)                ║
    ║  2 - Listening (Escutando)            ║
    ║  3 - Processing (Processando)         ║
    ║  4 - Executing (Executando)           ║
    ║  5 - Error (Erro)                     ║
    ║                                       ║
    ║  ESC - Fechar                         ║
    ╚═══════════════════════════════════════╝
    `);
});

