# ========================================
# JARVIS - Detecção de Wake Word (Whisper)
# Usa Whisper para detectar "Jarvis"
# ========================================

import threading
import time
import numpy as np
import sounddevice as sd
from typing import Callable, Optional

from config import config
from speech_to_text import stt
from logger import logger, log_wake_word, log_error


class WakeWordDetectorWhisper:
    """Detecta a wake word 'Jarvis' usando Whisper"""
    
    def __init__(self):
        self.is_listening = False
        self.callback_on_wake = None
        self._stop_event = threading.Event()
        self.listen_thread = None
        
        # Configurações
        self.chunk_duration = 2.5  # segundos de áudio por vez
        self.sample_rate = config.sample_rate
        self.device = config.input_device
        
        # Variações da wake word
        self.wake_words = [
            "jarvis", "járvis", "jarves", "jarvi",
            "jarv", "jervis", "gervis", "javi",
            "jarv", "javis", "djarvis"
        ]
    
    def initialize(self) -> bool:
        """Inicializa o detector"""
        try:
            # Garantir que o Whisper está carregado
            stt.initialize()
            
            logger.info("[WAKE_WHISPER] Inicializado com sucesso")
            return True
            
        except Exception as e:
            log_error(f"Erro ao inicializar Wake Word Whisper: {e}")
            return False
    
    def _contains_wake_word(self, text: str) -> bool:
        """Verifica se o texto contém a wake word"""
        text_lower = text.lower().strip()
        
        for wake_word in self.wake_words:
            if wake_word in text_lower:
                return True
        
        return False
    
    def _listen_loop(self):
        """Loop de escuta contínua"""
        logger.info("[WAKE_WHISPER] Iniciando loop de escuta...")
        
        while not self._stop_event.is_set():
            try:
                # Gravar chunk de áudio
                samples = int(self.chunk_duration * self.sample_rate)
                
                audio = sd.rec(
                    samples,
                    samplerate=self.sample_rate,
                    channels=1,
                    dtype='float32',
                    device=self.device
                )
                sd.wait()
                
                if self._stop_event.is_set():
                    break
                
                audio = audio.flatten()
                
                # Verificar se tem áudio significativo
                volume = np.abs(audio).mean()
                
                if volume < 0.005:
                    # Silêncio, pular transcrição
                    continue
                
                logger.debug(f"[WAKE_WHISPER] Volume={volume:.4f}, transcrevendo...")
                
                # Transcrever com Whisper
                text, confidence = stt.transcribe(audio)
                
                if text:
                    logger.info(f"[WAKE_WHISPER] Ouvido: '{text}' (conf={confidence:.2f})")
                    
                    # Verificar wake word
                    if self._contains_wake_word(text):
                        log_wake_word(True, text)
                        print(f"🎤 Wake word detectada: '{text}'")
                        
                        if self.callback_on_wake:
                            self.callback_on_wake()
                
            except Exception as e:
                if not self._stop_event.is_set():
                    log_error(f"Erro no loop de escuta: {e}")
                time.sleep(0.5)
    
    def start(self, on_wake_callback: Callable) -> bool:
        """Inicia a escuta contínua pela wake word"""
        if not self.initialize():
            return False
        
        self.callback_on_wake = on_wake_callback
        self._stop_event.clear()
        self.is_listening = True
        
        # Iniciar thread de escuta
        self.listen_thread = threading.Thread(target=self._listen_loop, daemon=True)
        self.listen_thread.start()
        
        print(f"🎤 Usando dispositivo: {self.device}")
        print(f"👂 Escutando pela wake word 'jarvis' (Whisper)...")
        logger.info(f"[WAKE_WHISPER] Escutando com dispositivo {self.device}")
        
        return True
    
    def stop(self):
        """Para a escuta"""
        self._stop_event.set()
        self.is_listening = False
        
        if self.listen_thread:
            self.listen_thread.join(timeout=3)
        
        logger.info("[WAKE_WHISPER] Parado")
        print("🛑 Wake word detector parado")


# Instância global
wake_detector_whisper = WakeWordDetectorWhisper()


# === TESTE ===
if __name__ == "__main__":
    print("🎤 Testando Wake Word Detector (Whisper)")
    print("=" * 50)
    print("Diga 'Jarvis' para testar...")
    print()
    
    def on_wake():
        print("\n" + "=" * 50)
        print("🚀 WAKE WORD DETECTADA!")
        print("=" * 50 + "\n")
    
    detector = WakeWordDetectorWhisper()
    
    if detector.start(on_wake):
        try:
            while True:
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("\n👋 Encerrando...")
            detector.stop()
    else:
        print("❌ Falha ao iniciar detector")

