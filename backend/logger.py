# ========================================
# JARVIS - Sistema de Logs
# ========================================

import logging
import os
from datetime import datetime
from pathlib import Path

# Diretório de logs
LOG_DIR = Path(__file__).parent / "data" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Arquivo de log do dia
LOG_FILE = LOG_DIR / f"jarvis_{datetime.now().strftime('%Y-%m-%d')}.log"

# Configurar formato
LOG_FORMAT = "%(asctime)s [%(levelname)s] %(message)s"
DATE_FORMAT = "%H:%M:%S"

# Criar logger
logger = logging.getLogger("JARVIS")
logger.setLevel(logging.DEBUG)

# Handler para arquivo
file_handler = logging.FileHandler(LOG_FILE, encoding='utf-8')
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))

# Handler para console
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))

# Adicionar handlers
logger.addHandler(file_handler)
logger.addHandler(console_handler)


def log_audio(device_id, volume):
    """Log de áudio capturado"""
    logger.debug(f"[AUDIO] Device={device_id}, Volume={volume:.6f}")


def log_wake_word(detected: bool, text: str = ""):
    """Log de detecção de wake word"""
    if detected:
        logger.info(f"[WAKE] Wake word detectada! Texto: '{text}'")
    else:
        logger.debug(f"[WAKE] Verificando: '{text}'")


def log_command(text: str):
    """Log de comando recebido"""
    logger.info(f"[COMANDO] '{text}'")


def log_response(text: str):
    """Log de resposta do JARVIS"""
    logger.info(f"[RESPOSTA] '{text[:100]}...' " if len(text) > 100 else f"[RESPOSTA] '{text}'")


def log_action(action: str, param: str = ""):
    """Log de ação executada"""
    logger.info(f"[AÇÃO] {action} -> {param}")


def log_error(error: str):
    """Log de erro"""
    logger.error(f"[ERRO] {error}")


def log_state(state: str):
    """Log de mudança de estado"""
    logger.debug(f"[ESTADO] -> {state}")


def log_mic_test(device_id, volume: float):
    """Log de teste de microfone"""
    status = "OK" if volume > 0.005 else "SEM_AUDIO"
    logger.info(f"[MIC_TEST] Device={device_id}, Volume={volume:.6f}, Status={status}")


# Função para ver logs recentes
def get_recent_logs(lines: int = 50) -> str:
    """Retorna as últimas linhas do log"""
    if LOG_FILE.exists():
        with open(LOG_FILE, 'r', encoding='utf-8') as f:
            all_lines = f.readlines()
            return ''.join(all_lines[-lines:])
    return "Nenhum log encontrado"


# Log de inicialização
logger.info("="*50)
logger.info("JARVIS Logger inicializado")
logger.info(f"Arquivo de log: {LOG_FILE}")
logger.info("="*50)


