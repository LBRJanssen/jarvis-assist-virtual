# ========================================
# JARVIS - Detecção de Wake Word (Porcupine)
# Sistema profissional da Picovoice
# ========================================

import struct
import threading
import time
from typing import Callable

import pvporcupine
import pyaudio

from config import config
from logger import logger, log_wake_word, log_error


class WakeWordDetectorPorcupine:
    """Detecta a wake word 'Jarvis' usando Porcupine"""
    
    def __init__(self):
        self.porcupine = None
        self.audio_stream = None
        self.pa = None
        self.is_listening = False
        self.callback_on_wake = None
        self._stop_event = threading.Event()
        self.listen_thread = None
        
        # Chave de API do Porcupine (gratuita para uso pessoal)
        # Obtenha em: https://console.picovoice.ai/
        self.access_key = config.porcupine_access_key
    
    def initialize(self) -> bool:
        """Inicializa o Porcupine"""
        try:
            if not self.access_key:
                print("❌ Chave do Porcupine não configurada!")
                print("   1. Acesse: https://console.picovoice.ai/")
                print("   2. Crie conta gratuita")
                print("   3. Copie a Access Key")
                print("   4. Cole em config.py -> porcupine_access_key")
                return False
            
            # Criar instância do Porcupine com wake word "Jarvis"
            self.porcupine = pvporcupine.create(
                access_key=self.access_key,
                keywords=["jarvis"]  # Wake word built-in
            )
            
            # Inicializar PyAudio
            self.pa = pyaudio.PyAudio()
            
            logger.info("[PORCUPINE] Inicializado com sucesso!")
            print("✅ Porcupine inicializado - Wake word: 'Jarvis'")
            return True
            
        except pvporcupine.PorcupineActivationError:
            log_error("Chave do Porcupine inválida ou expirada")
            print("❌ Chave do Porcupine inválida!")
            print("   Obtenha uma nova em: https://console.picovoice.ai/")
            return False
        except Exception as e:
            log_error(f"Erro ao inicializar Porcupine: {e}")
            print(f"❌ Erro: {e}")
            return False
    
    def _listen_loop(self):
        """Loop de escuta contínua"""
        try:
            # Abrir stream de áudio
            self.audio_stream = self.pa.open(
                rate=self.porcupine.sample_rate,
                channels=1,
                format=pyaudio.paInt16,
                input=True,
                frames_per_buffer=self.porcupine.frame_length,
                input_device_index=config.input_device
            )
            
            logger.info("[PORCUPINE] Escutando...")
            
            while not self._stop_event.is_set():
                # Ler áudio
                pcm = self.audio_stream.read(
                    self.porcupine.frame_length,
                    exception_on_overflow=False
                )
                pcm = struct.unpack_from("h" * self.porcupine.frame_length, pcm)
                
                # Processar com Porcupine
                keyword_index = self.porcupine.process(pcm)
                
                if keyword_index >= 0:
                    # Wake word detectada!
                    log_wake_word(True, "jarvis")
                    print("🎤 Wake word 'Jarvis' detectada!")
                    
                    if self.callback_on_wake:
                        self.callback_on_wake()
                        
        except Exception as e:
            if not self._stop_event.is_set():
                log_error(f"Erro no loop Porcupine: {e}")
        finally:
            if self.audio_stream:
                self.audio_stream.close()
    
    def start(self, on_wake_callback: Callable) -> bool:
        """Inicia a escuta pela wake word"""
        if not self.porcupine:
            if not self.initialize():
                return False
        
        self.callback_on_wake = on_wake_callback
        self._stop_event.clear()
        self.is_listening = True
        
        # Iniciar thread de escuta
        self.listen_thread = threading.Thread(target=self._listen_loop, daemon=True)
        self.listen_thread.start()
        
        print(f"👂 Escutando pela wake word 'Jarvis' (Porcupine)...")
        logger.info("[PORCUPINE] Iniciado")
        
        return True
    
    def stop(self):
        """Para a escuta"""
        self._stop_event.set()
        self.is_listening = False
        
        if self.listen_thread:
            self.listen_thread.join(timeout=2)
        
        if self.porcupine:
            self.porcupine.delete()
            self.porcupine = None
        
        if self.pa:
            self.pa.terminate()
            self.pa = None
        
        logger.info("[PORCUPINE] Parado")


# === TESTE ===
if __name__ == "__main__":
    print("🎤 Testando Porcupine Wake Word Detector")
    print("=" * 50)
    print("Diga 'Jarvis' para testar...")
    print()
    
    def on_wake():
        print("\n🚀 JARVIS DETECTADO!\n")
    
    detector = WakeWordDetectorPorcupine()
    
    if detector.start(on_wake):
        try:
            while True:
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("\n👋 Encerrando...")
            detector.stop()
    else:
        print("❌ Falha ao iniciar")


