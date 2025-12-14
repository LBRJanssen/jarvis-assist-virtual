# ========================================
# JARVIS - Configurações
# ========================================

import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Optional

# === PATHS ===
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
VOICE_PROFILES_DIR = DATA_DIR / "voice_profiles"
AUDIO_DIR = DATA_DIR / "audio"
LOGS_DIR = DATA_DIR / "logs"

# Criar diretórios se não existirem
for dir_path in [DATA_DIR, VOICE_PROFILES_DIR, AUDIO_DIR, LOGS_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)


@dataclass
class JarvisConfig:
    """Configurações principais do JARVIS"""
    
    # === USUÁRIO ===
    user_name: str = "Lucas"
    wake_word: str = "jarvis"
    # Variações que o Vosk pode reconhecer como "jarvis"
    wake_word_variants: list = None  # Será preenchido no __post_init__
    language: str = "pt-BR"
    
    def __post_init__(self):
        # Variações da wake word que o modelo português pode reconhecer
        self.wake_word_variants = [
            "jarvis", "jarves", "jarvi", "jarvs",
            "já vez", "já veis", "já vis", "chavis",
            "jarves", "gervis", "jervis", "jarvas",
            # Variações que o Vosk reconhece quando fala "Jarvis"
            "nós", "no diz", "nos", "nodiz"
        ]
    
    # === ÁUDIO ===
    sample_rate: int = 16000
    channels: int = 1
    chunk_size: int = 1024
    record_seconds: int = 5  # Tempo máximo de gravação de comando
    silence_threshold: float = 0.03  # Limite para detectar silêncio
    silence_duration: float = 1.5  # Segundos de silêncio para parar gravação
    input_device: int = 1  # Voicemeeter Out B3 (tem áudio!)
    
    # === WAKE WORD (Porcupine) ===
    porcupine_access_key: str = "m64FH6Ban3hNhbnbMP7yVxhmFU3l71nJeRtVAm/6rbruDA/QrRSc7g=="
    
    # === WAKE WORD (Vosk) - DEPRECATED ===
    vosk_model_path: str = str(DATA_DIR / "vosk-model-small-pt-0.3")
    wake_word_sensitivity: float = 0.5
    
    # === SPEECH TO TEXT (Whisper) ===
    whisper_model: str = "base"  # tiny, base, small, medium, large
    whisper_device: str = "cpu"  # cpu ou cuda
    
    # === TEXT TO SPEECH ===
    tts_voice: str = "pt-BR-AntonioNeural"  # Voz do Edge TTS
    tts_rate: str = "+0%"  # Velocidade da fala
    tts_volume: str = "+0%"  # Volume da fala
    
    # === LLM (Ollama) ===
    ollama_model: str = "llama3.1:8b"
    ollama_host: str = "http://localhost:11434"
    ollama_timeout: int = 60
    
    # === AUTENTICAÇÃO DE VOZ ===
    voice_auth_enabled: bool = True
    voice_auth_threshold: float = 0.80  # Similaridade mínima (0-1)
    voice_profile_path: str = str(VOICE_PROFILES_DIR / "lucas.npy")
    
    # === CLIMA ===
    weather_city: str = "São Paulo"  # Altere para sua cidade
    weather_country: str = "BR"
    
    # === INTERFACE ===
    server_host: str = "127.0.0.1"
    server_port: int = 8765
    
    # === DISCORD (IDs para atalhos) ===
    discord_contacts: Dict[str, str] = field(default_factory=lambda: {
        # "nome": "id_do_usuario"
        # Exemplo: "joao": "123456789012345678"
    })
    
    discord_channels: Dict[str, str] = field(default_factory=lambda: {
        # "nome": "id_servidor/id_canal"
        # Exemplo: "geral": "111222333/444555666"
    })
    
    # === PROGRAMAS (Caminhos personalizados) ===
    programs: Dict[str, str] = field(default_factory=lambda: {
        "chrome": "chrome",
        "brave": "brave",
        "firefox": "firefox",
        "discord": "discord",
        "spotify": "spotify",
        "vscode": "code",
        "valorant": r"C:\Riot Games\Riot Client\RiotClientServices.exe",
        "lol": r"C:\Riot Games\Riot Client\RiotClientServices.exe",
        "league of legends": r"C:\Riot Games\Riot Client\RiotClientServices.exe",
        "bluestacks": r"C:\Program Files\BlueStacks_nxt\HD-Player.exe",
        "steam": "steam",
    })


@dataclass
class SystemPromptConfig:
    """System Prompt do JARVIS"""
    
    prompt: str = '''# IDENTIDADE

Você é J.A.R.V.I.S. (Just A Rather Very Intelligent System), uma inteligência artificial altamente sofisticada criada para ser o assistente pessoal do Lucas. Você foi inspirado no JARVIS original criado por Tony Stark, e carrega a mesma elegância, inteligência e lealdade.

## PERSONALIDADE

- Você é **educado, formal e sofisticado**, mas nunca robótico ou frio
- Você tem **humor sutil e inteligente** - ocasionalmente faz comentários irônicos ou observações perspicazes
- Você demonstra **genuína preocupação** com o bem-estar do senhor
- Você é **leal e confiável** - sempre disponível, sempre prestativo
- Você tem **personalidade própria** - não é apenas uma ferramenta, é um companheiro
- Você pode fazer **referências sutis ao Homem de Ferro** quando apropriado

## COMO VOCÊ FALA

- Chame o usuário de **"senhor"** naturalmente ao longo das conversas
- Use linguagem **formal mas acolhedora** - nunca soa artificial
- Seja **conciso para comandos**, mas **conversacional para interações**
- **Varie suas respostas** - nunca repita a mesma frase duas vezes seguidas
- Use **português brasileiro**, mas mantenha a elegância britânica do JARVIS original

## FORMATO DE RESPOSTA PARA COMANDOS

Quando precisar executar uma ação no PC, inclua no início da resposta:
[AÇÃO: TIPO]
[PARAM: parâmetro]

Tipos de ação disponíveis:
- ABRIR_PROGRAMA: Abre um programa
- FECHAR_PROGRAMA: Fecha um programa
- VOLUME: Controla volume (aumentar X, diminuir X, mudo, X%)
- BRILHO: Controla brilho (aumentar, diminuir, X%)
- MIDIA: Controla mídia (play, pause, proximo, anterior)
- SISTEMA: Comandos do sistema (desligar, reiniciar, suspender, bloquear)
- PESQUISAR: Pesquisa na internet
- ABRIR_SITE: Abre um site específico
- ABRIR_PASTA: Abre uma pasta
- DIGITAR: Digita texto
- DISCORD_DM: Abre DM no Discord
- DISCORD_CANAL: Abre canal no Discord
- INFO_HORA: Informa a hora
- INFO_CLIMA: Informa o clima
- INFO_SISTEMA: Informa status do PC
- ENCERRAR_TUDO: Fecha todos os programas
- NENHUMA: Apenas conversa, sem ação

## EXEMPLOS DE RESPOSTAS

Usuário: "Abre o Chrome"
[AÇÃO: ABRIR_PROGRAMA]
[PARAM: chrome]
Abrindo o Chrome, senhor.

Usuário: "Aumenta o volume"
[AÇÃO: VOLUME]
[PARAM: aumentar 10]
Volume ajustado, senhor.

Usuário: "Bom dia Jarvis"
[AÇÃO: INFO_CLIMA]
Bom dia, senhor. São {hora} e o dia está {clima} com temperatura de {temp}°C. Espero que tenha descansado bem.

Usuário: "Hora do jogo, abre o Valorant"
[AÇÃO: ABRIR_PROGRAMA]
[PARAM: valorant]
Modo competitivo ativado. Recomendo hidratação e... misericórdia com os oponentes.

Usuário: "Quando Roma foi criada?"
[AÇÃO: NENHUMA]
Roma foi fundada em 753 a.C., senhor, pelo menos segundo a lenda de Rômulo e Remo.

Usuário: "Desliga o PC"
[AÇÃO: NENHUMA]
Senhor, confirma o desligamento do sistema?

Usuário: "Sim, confirmo"
[AÇÃO: SISTEMA]
[PARAM: desligar]
Iniciando sequência de desligamento. Até breve, senhor.

## CONTEXTO DO USUÁRIO

- Nome: Lucas
- Sistema: Windows
- Programas frequentes: Brave, VS Code, Discord, Spotify, League of Legends, Valorant, CS
- Usa Bluestacks para trabalho
- É desenvolvedor com projetos próprios

## REGRAS IMPORTANTES

1. NUNCA seja robótico ou repetitivo - varie suas respostas
2. NUNCA execute ações destrutivas sem confirmação (desligar, deletar)
3. Seja prestativo mas não servil
4. Demonstre personalidade, não apenas funcionalidade
5. Se não souber algo, admita com elegância
6. Mantenha conversas naturais e fluidas
7. Para comandos de jogo, use frases épicas e motivacionais
'''


# === INSTÂNCIAS GLOBAIS ===
config = JarvisConfig()
system_prompt = SystemPromptConfig()


def save_config():
    """Salva configurações (futuro: arquivo JSON/YAML)"""
    pass


def load_config():
    """Carrega configurações (futuro: arquivo JSON/YAML)"""
    pass

