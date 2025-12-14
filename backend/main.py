# ========================================
# JARVIS - Assistente de Voz Pessoal
# Arquivo Principal
# ========================================

import sys
import os
import time
import threading
from typing import Optional
from enum import Enum
from pathlib import Path

from colorama import init, Fore, Style
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm

# Módulos do JARVIS
from config import config
from wake_word import WakeWordDetector, record_command
from wake_word_whisper import WakeWordDetectorWhisper
from wake_word_porcupine import WakeWordDetectorPorcupine
from speech_to_text import stt
from text_to_speech import tts, speak
from voice_auth import voice_auth, enroll_voice_interactive
from brain import brain, JarvisResponse
from pc_control import execute_action, pc

# Servidor WebSocket (para interface)
import asyncio
from server import manager, run_server, JarvisState as WSState

# Arquivo de configuração inicial
FIRST_RUN_FILE = Path(__file__).parent / "data" / ".first_run_complete"

# Inicializar colorama para Windows
init()

console = Console()


class JarvisState(Enum):
    """Estados do JARVIS"""
    IDLE = "idle"              # Esperando wake word
    LISTENING = "listening"    # Gravando comando
    PROCESSING = "processing"  # Processando com IA
    EXECUTING = "executing"    # Executando ação
    ERROR = "error"            # Erro


class Jarvis:
    """Classe principal do JARVIS"""
    
    def __init__(self):
        self.state = JarvisState.IDLE
        # Usar Porcupine para detecção de wake word (profissional)
        self.wake_detector = WakeWordDetectorPorcupine()
        self.is_running = False
        self._lock = threading.Lock()
        self._cancel_flag = threading.Event()  # Flag para cancelar operação atual
        self._current_task = None  # Thread da tarefa atual
    
    def _print_banner(self):
        """Mostra banner inicial"""
        banner = """
        ╔═══════════════════════════════════════════════════════════╗
        ║                                                           ║
        ║        ██╗ █████╗ ██████╗ ██╗   ██╗██╗███████╗           ║
        ║        ██║██╔══██╗██╔══██╗██║   ██║██║██╔════╝           ║
        ║        ██║███████║██████╔╝██║   ██║██║███████╗           ║
        ║   ██   ██║██╔══██║██╔══██╗╚██╗ ██╔╝██║╚════██║           ║
        ║   ╚█████╔╝██║  ██║██║  ██║ ╚████╔╝ ██║███████║           ║
        ║    ╚════╝ ╚═╝  ╚═╝╚═╝  ╚═╝  ╚═══╝  ╚═╝╚══════╝           ║
        ║                                                           ║
        ║          Just A Rather Very Intelligent System            ║
        ║                      v1.0.0                               ║
        ║                                                           ║
        ╚═══════════════════════════════════════════════════════════╝
        """
        print(Fore.CYAN + banner + Style.RESET_ALL)
    
    def _set_state(self, state: JarvisState, text: str = ""):
        """Atualiza o estado do JARVIS"""
        with self._lock:
            self.state = state
            
            # Cores por estado
            colors = {
                JarvisState.IDLE: Fore.CYAN,
                JarvisState.LISTENING: Fore.YELLOW,
                JarvisState.PROCESSING: Fore.BLUE,
                JarvisState.EXECUTING: Fore.GREEN,
                JarvisState.ERROR: Fore.RED,
            }
            
            color = colors.get(state, Fore.WHITE)
            print(f"{color}[{state.value.upper()}]{Style.RESET_ALL}", end=" ")
            
            # Atualizar interface visual
            self._update_interface(state.value, text)
    
    def initialize(self) -> bool:
        """Inicializa todos os módulos"""
        print("\n" + "="*60)
        print("🚀 Inicializando JARVIS...")
        print("="*60 + "\n")
        
        steps = [
            ("Wake Word (Porcupine)", lambda: self.wake_detector.initialize()),
            ("Speech-to-Text (Whisper)", lambda: stt.initialize()),
            ("Text-to-Speech (Edge TTS)", lambda: True),  # Inicializa sob demanda
            ("Autenticação de Voz", lambda: voice_auth.initialize()),
            ("Cérebro (Ollama)", lambda: brain.initialize()),
        ]
        
        for name, init_func in steps:
            print(f"  🔄 {name}...", end=" ")
            try:
                if init_func():
                    print(f"{Fore.GREEN}✅{Style.RESET_ALL}")
                else:
                    print(f"{Fore.RED}❌{Style.RESET_ALL}")
                    return False
            except Exception as e:
                print(f"{Fore.RED}❌ {e}{Style.RESET_ALL}")
                return False
        
        print("\n" + "="*60)
        print(f"{Fore.GREEN}✅ JARVIS inicializado com sucesso!{Style.RESET_ALL}")
        print("="*60 + "\n")
        
        return True
    
    def _on_wake_word(self):
        """Callback quando wake word é detectada"""
        with self._lock:
            # Se já está processando, CANCELAR e começar novo
            if self.state != JarvisState.IDLE:
                print(f"{Fore.YELLOW}⚠️ Cancelando operação anterior...{Style.RESET_ALL}")
                self._cancel_flag.set()
                
                # Parar fala atual
                tts.stop()
                
                # Aguardar thread anterior terminar (máx 1s)
                if self._current_task and self._current_task.is_alive():
                    self._current_task.join(timeout=1.0)
            
            # Resetar flag de cancelamento
            self._cancel_flag.clear()
            
            # Mudar para listening
            self.state = JarvisState.LISTENING
        
        self._set_state(JarvisState.LISTENING)
        print(f"{Fore.YELLOW}🎤 Escutando...{Style.RESET_ALL}")
        
        # Executar em thread separada para permitir cancelamento
        self._current_task = threading.Thread(target=self._process_command, daemon=True)
        self._current_task.start()
    
    def _process_command(self):
        """Processa comando em thread separada (permite cancelamento)"""
        # Gravar comando
        audio = record_command()
        
        if self._cancel_flag.is_set():
            return
        
        if audio is None or len(audio) < 1000:
            self._set_state(JarvisState.IDLE)
            return
        
        # Verificar voz (se habilitado) - rápido
        if config.voice_auth_enabled and voice_auth.has_profile():
            authorized, confidence = voice_auth.verify(audio)
            
            if self._cancel_flag.is_set():
                return
            
            if not authorized:
                self._set_state(JarvisState.ERROR)
                speak("Desculpe, não reconheço sua voz.")
                time.sleep(1)
                self._set_state(JarvisState.IDLE)
                return
        
        # Transcrever (usar modelo tiny para velocidade)
        self._set_state(JarvisState.PROCESSING)
        
        # Salvar modelo atual
        original_model = config.whisper_model
        config.whisper_model = "tiny"  # Mais rápido para comandos
        
        text, confidence = stt.transcribe(audio)
        
        # Restaurar modelo
        config.whisper_model = original_model
        
        if self._cancel_flag.is_set():
            return
        
        if not text or confidence < 0.3:
            self._set_state(JarvisState.ERROR)
            speak("Desculpe senhor, não consegui entender.")
            time.sleep(1)
            self._set_state(JarvisState.IDLE)
            return
        
        print(f"{Fore.WHITE}👤 Você: {text}{Style.RESET_ALL}")
        
        # Processar com IA (com timeout)
        response = brain.process(text)
        
        if self._cancel_flag.is_set():
            return
        
        # Executar ação (se houver)
        if response.action and response.action != "NENHUMA":
            self._set_state(JarvisState.EXECUTING)
            success, msg = execute_action(response.action, response.param)
            
            if not success:
                print(f"{Fore.RED}❌ Erro na ação: {msg}{Style.RESET_ALL}")
        
        if self._cancel_flag.is_set():
            return
        
        # Falar resposta (sem bloquear)
        if response.speech:
            print(f"{Fore.CYAN}🤖 JARVIS: {response.speech}{Style.RESET_ALL}")
            # Falar em thread separada para não bloquear
            threading.Thread(target=lambda: speak(response.speech), daemon=True).start()
        
        # Voltar ao idle
        self._set_state(JarvisState.IDLE)
    
    def _check_first_run(self):
        """Verifica se é a primeira execução - configuração será feita por voz depois"""
        if FIRST_RUN_FILE.exists():
            return False  # Não é primeira execução
        
        # Marcar que passou pela primeira execução
        FIRST_RUN_FILE.parent.mkdir(parents=True, exist_ok=True)
        FIRST_RUN_FILE.touch()
        
        return True  # É primeira execução
    
    def _first_run_voice_setup(self):
        """Configuração de voz feita pelo próprio JARVIS falando"""
        print(f"\n{Fore.CYAN}🎉 Primeira execução detectada!{Style.RESET_ALL}")
        
        # JARVIS fala boas-vindas
        speak("Olá senhor! É um prazer conhecê-lo. Sou o JARVIS, seu assistente pessoal.")
        time.sleep(0.5)
        
        # Perguntar sobre configuração de voz
        if config.voice_auth_enabled and not voice_auth.has_profile():
            speak("Para sua segurança, posso aprender a reconhecer apenas a sua voz. "
                  "Assim, ninguém além do senhor poderá me comandar.")
            time.sleep(0.3)
            speak("Deseja configurar o reconhecimento de voz agora? Diga sim ou não.")
            
            print(f"\n{Fore.YELLOW}🎤 Aguardando resposta... (diga 'sim' ou 'não'){Style.RESET_ALL}")
            
            # Gravar resposta
            audio = record_command(duration=5)
            
            if audio is not None and len(audio) > 1000:
                text, _ = stt.transcribe(audio)
                text_lower = text.lower() if text else ""
                
                print(f"{Fore.WHITE}👤 Você disse: {text}{Style.RESET_ALL}")
                
                if any(word in text_lower for word in ["sim", "yes", "quero", "pode", "claro", "ok", "beleza"]):
                    speak("Perfeito! Vamos começar o cadastro da sua voz.")
                    time.sleep(0.5)
                    self._voice_enrollment_interactive()
                else:
                    speak("Entendido senhor. Quando quiser configurar, basta me pedir.")
            else:
                speak("Não consegui ouvir sua resposta. Podemos configurar isso depois, senhor.")
    
    def _voice_enrollment_interactive(self):
        """Cadastro de voz interativo por voz"""
        frases = [
            "Jarvis, ativar sistema",
            "Bom dia Jarvis",
            "Jarvis, abra o navegador",
            "Jarvis, qual a previsão do tempo",
            "Jarvis, tocar música"
        ]
        
        embeddings = []
        
        speak(f"Vou pedir que o senhor repita {len(frases)} frases curtas. Fale de forma natural.")
        time.sleep(0.5)
        
        for i, frase in enumerate(frases, 1):
            print(f"\n{Fore.CYAN}📝 Frase {i}/{len(frases)}: \"{frase}\"{Style.RESET_ALL}")
            speak(f"Frase {i}. Por favor, diga: {frase}")
            
            time.sleep(0.5)
            print(f"{Fore.YELLOW}🎤 Gravando...{Style.RESET_ALL}")
            
            audio = record_command(duration=5)
            
            if audio is not None and len(audio) > 1000:
                # Extrair embedding
                embedding = voice_auth._extract_embedding(audio)
                if embedding is not None:
                    embeddings.append(embedding)
                    print(f"{Fore.GREEN}✅ Gravação {i} capturada!{Style.RESET_ALL}")
                    speak("Ótimo!")
                else:
                    print(f"{Fore.RED}❌ Não consegui processar o áudio{Style.RESET_ALL}")
                    speak("Não consegui processar. Vamos continuar.")
            else:
                print(f"{Fore.RED}❌ Áudio muito curto{Style.RESET_ALL}")
                speak("O áudio ficou muito curto. Vamos continuar.")
        
        # Salvar perfil se tiver embeddings suficientes
        if len(embeddings) >= 3:
            import numpy as np
            voice_auth.voice_embedding = np.mean(embeddings, axis=0)
            voice_auth._save_profile()
            
            print(f"\n{Fore.GREEN}✅ Perfil de voz cadastrado com sucesso!{Style.RESET_ALL}")
            speak("Excelente senhor! Seu perfil de voz foi cadastrado com sucesso. "
                  "Agora apenas o senhor poderá me comandar.")
        else:
            print(f"\n{Fore.RED}❌ Não foi possível cadastrar (poucas amostras){Style.RESET_ALL}")
            speak("Infelizmente não consegui amostras suficientes. "
                  "Podemos tentar novamente depois, senhor.")
    
    def _start_websocket_server(self):
        """Inicia servidor WebSocket em thread separada"""
        def run_ws():
            print(f"{Fore.CYAN}🌐 Iniciando servidor WebSocket...{Style.RESET_ALL}")
            run_server(config.server_host, config.server_port)
        
        self.ws_thread = threading.Thread(target=run_ws, daemon=True)
        self.ws_thread.start()
        time.sleep(1)  # Dar tempo para o servidor iniciar
        print(f"{Fore.GREEN}✅ WebSocket rodando em ws://{config.server_host}:{config.server_port}/ws{Style.RESET_ALL}")
    
    def _update_interface(self, state: str, text: str = ""):
        """Atualiza estado na interface visual"""
        try:
            state_map = {
                "idle": WSState.IDLE,
                "listening": WSState.LISTENING,
                "processing": WSState.PROCESSING,
                "executing": WSState.EXECUTING,
                "error": WSState.ERROR,
            }
            ws_state = state_map.get(state, WSState.IDLE)
            asyncio.run(manager.broadcast_state(ws_state, text))
        except Exception as e:
            pass  # Silenciar erros de WebSocket
    
    def run(self):
        """Executa o JARVIS"""
        self._print_banner()
        
        # Iniciar servidor WebSocket PRIMEIRO
        self._start_websocket_server()
        
        # Verificar se é primeira execução
        is_first_run = self._check_first_run()
        
        # Atualizar interface: processando
        self._update_interface("processing", "Inicializando sistemas...")
        
        # Inicializar módulos
        if not self.initialize():
            print(f"\n{Fore.RED}❌ Falha na inicialização. Verifique os erros acima.{Style.RESET_ALL}")
            self._update_interface("error", "Falha na inicialização")
            return
        
        # Primeira execução - JARVIS fala e oferece configurar voz
        if is_first_run:
            self._first_run_voice_setup()
        else:
            # Mensagem de boas-vindas normal
            speak("Bom dia, senhor. Todos os sistemas operacionais e prontos.")
        
        # Atualizar interface: pronto
        self._update_interface("idle", "Aguardando 'Jarvis'...")
        
        # Iniciar escuta
        print(f"\n{Fore.CYAN}👂 Aguardando wake word '{config.wake_word}'...{Style.RESET_ALL}")
        print(f"{Fore.WHITE}   (Pressione Ctrl+C para sair){Style.RESET_ALL}\n")
        
        self.is_running = True
        
        if not self.wake_detector.start(self._on_wake_word):
            print(f"{Fore.RED}❌ Falha ao iniciar detector de wake word{Style.RESET_ALL}")
            self._update_interface("error", "Falha no detector de voz")
            return
        
        # Loop principal
        try:
            while self.is_running:
                time.sleep(0.1)
                
        except KeyboardInterrupt:
            print(f"\n\n{Fore.YELLOW}👋 Encerrando JARVIS...{Style.RESET_ALL}")
            self.shutdown()
    
    def shutdown(self):
        """Encerra o JARVIS"""
        self.is_running = False
        self.wake_detector.stop()
        speak("Até logo, senhor.")
        print(f"{Fore.CYAN}✅ JARVIS encerrado.{Style.RESET_ALL}")


# === FUNÇÕES DE UTILIDADE ===

def check_dependencies():
    """Verifica dependências necessárias"""
    print("🔍 Verificando dependências...\n")
    
    dependencies = [
        ("numpy", "numpy"),
        ("sounddevice", "sounddevice"),
        ("vosk", "vosk"),
        ("faster_whisper", "faster-whisper"),
        ("edge_tts", "edge-tts"),
        ("pygame", "pygame"),
        ("resemblyzer", "resemblyzer"),
        ("ollama", "ollama"),
        ("pyautogui", "pyautogui"),
        ("psutil", "psutil"),
    ]
    
    missing = []
    
    for module, package in dependencies:
        try:
            __import__(module)
            print(f"  ✅ {package}")
        except ImportError:
            print(f"  ❌ {package}")
            missing.append(package)
    
    if missing:
        print(f"\n⚠️  Pacotes faltando: {', '.join(missing)}")
        print(f"   Execute: pip install {' '.join(missing)}")
        return False
    
    print("\n✅ Todas as dependências instaladas!")
    return True


def check_ollama():
    """Verifica se o Ollama está rodando"""
    try:
        import httpx
        response = httpx.get(f"{config.ollama_host}/api/tags", timeout=5)
        return response.status_code == 200
    except:
        return False


# === MAIN ===

def main():
    """Função principal"""
    
    # Verificar argumentos
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        
        if arg == "--check":
            check_dependencies()
            return
        
        elif arg == "--enroll":
            voice_auth.initialize()
            enroll_voice_interactive()
            return
        
        elif arg == "--help":
            print("""
JARVIS - Assistente de Voz Pessoal

Uso:
  python main.py          Inicia o JARVIS
  python main.py --check  Verifica dependências
  python main.py --enroll Cadastra voz do usuário
  python main.py --help   Mostra esta ajuda

Requisitos:
  - Python 3.10+
  - Ollama rodando (ollama serve)
  - Modelo Llama instalado (ollama pull llama3.1:8b)
  - Modelo Vosk baixado em data/vosk-model-small-pt-0.3/
            """)
            return
    
    # Verificar Ollama
    if not check_ollama():
        print(f"{Fore.RED}❌ Ollama não está rodando!{Style.RESET_ALL}")
        print(f"   Execute: {Fore.YELLOW}ollama serve{Style.RESET_ALL}")
        print(f"   E depois: {Fore.YELLOW}ollama pull llama3.1:8b{Style.RESET_ALL}")
        return
    
    # Iniciar JARVIS
    jarvis = Jarvis()
    jarvis.run()


if __name__ == "__main__":
    main()

