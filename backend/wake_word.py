# ========================================
# JARVIS - Detecção de Wake Word
# Usa Vosk para detectar "Jarvis"
# ========================================

import json
import queue
import threading
from pathlib import Path
from typing import Callable, Optional

import numpy as np
import sounddevice as sd
from vosk import Model, KaldiRecognizer

from config import config, DATA_DIR
from logger import logger, log_wake_word, log_audio, log_error


class WakeWordDetector:
    """Detecta a wake word 'Jarvis' usando Vosk"""
    
    def __init__(self):
        self.model: Optional[Model] = None
        self.recognizer: Optional[KaldiRecognizer] = None
        self.audio_queue = queue.Queue()
        self.is_listening = False
        self.callback_on_wake: Optional[Callable] = None
        self._stop_event = threading.Event()
        
    def initialize(self) -> bool:
        """Inicializa o modelo Vosk"""
        model_path = Path(config.vosk_model_path)
        
        if not model_path.exists():
            print(f"⚠️  Modelo Vosk não encontrado em: {model_path}")
            print(f"📥 Baixe o modelo em: https://alphacephei.com/vosk/models")
            print(f"   Modelo recomendado: vosk-model-small-pt-0.3")
            print(f"   Extraia para: {DATA_DIR}")
            return False
        
        try:
            print("🔄 Carregando modelo Vosk...")
            self.model = Model(str(model_path))
            self.recognizer = KaldiRecognizer(self.model, config.sample_rate)
            self.recognizer.SetWords(True)
            print("✅ Modelo Vosk carregado!")
            return True
        except Exception as e:
            print(f"❌ Erro ao carregar modelo Vosk: {e}")
            return False
    
    def _audio_callback(self, indata, frames, time, status):
        """Callback para captura de áudio"""
        if status:
            print(f"⚠️  Status do áudio: {status}")
        self.audio_queue.put(bytes(indata))
    
    def _process_audio(self):
        """Processa áudio e detecta wake word"""
        frame_count = 0
        while not self._stop_event.is_set():
            try:
                data = self.audio_queue.get(timeout=0.5)
                frame_count += 1
                
                # Log de volume a cada 50 frames (~2.5 segundos)
                if frame_count % 50 == 0:
                    audio_np = np.frombuffer(data, dtype=np.int16).astype(np.float32) / 32768.0
                    volume = np.abs(audio_np).mean()
                    logger.debug(f"[AUDIO] Volume={volume:.6f}")
                
                if self.recognizer.AcceptWaveform(data):
                    result = json.loads(self.recognizer.Result())
                    text = result.get("text", "").lower()
                    
                    if text:  # Se reconheceu algo
                        logger.info(f"[VOSK] Reconhecido: '{text}'")
                    
                    # Verificar todas as variações da wake word
                    wake_detected = any(variant in text for variant in config.wake_word_variants)
                    if wake_detected:
                        log_wake_word(True, text)
                        print(f"🎤 Wake word detectada: '{text}'")
                        if self.callback_on_wake:
                            self.callback_on_wake()
                else:
                    # Resultado parcial (para feedback em tempo real)
                    partial = json.loads(self.recognizer.PartialResult())
                    partial_text = partial.get("partial", "").lower()
                    
                    # Log parcial se tiver conteúdo
                    if partial_text and len(partial_text) > 2:
                        logger.debug(f"[VOSK_PARCIAL] '{partial_text}'")
                    
                    # Verificar todas as variações da wake word
                    wake_detected = any(variant in partial_text for variant in config.wake_word_variants)
                    if wake_detected:
                        log_wake_word(True, partial_text)
                        print(f"🎤 Wake word detectada (parcial): '{partial_text}'")
                        if self.callback_on_wake:
                            self.callback_on_wake()
                        # Reseta o reconhecedor após detectar
                        self.recognizer.Reset()
                        
            except queue.Empty:
                continue
            except Exception as e:
                log_error(f"Erro no processamento: {e}")
                print(f"❌ Erro no processamento: {e}")
    
    def start(self, on_wake_callback: Callable):
        """Inicia a escuta contínua pela wake word"""
        if not self.model:
            if not self.initialize():
                return False
        
        self.callback_on_wake = on_wake_callback
        self._stop_event.clear()
        self.is_listening = True
        
        # Thread de processamento
        self.process_thread = threading.Thread(target=self._process_audio, daemon=True)
        self.process_thread.start()
        
        # Inicia captura de áudio
        device = getattr(config, 'input_device', None)
        print(f"🎤 Usando dispositivo de entrada: {device}")
        
        self.stream = sd.RawInputStream(
            samplerate=config.sample_rate,
            blocksize=8000,
            dtype="int16",
            channels=config.channels,
            device=device,
            callback=self._audio_callback
        )
        self.stream.start()
        
        print(f"👂 Escutando pela wake word '{config.wake_word}'...")
        return True
    
    def stop(self):
        """Para a escuta"""
        self._stop_event.set()
        self.is_listening = False
        
        if hasattr(self, 'stream'):
            self.stream.stop()
            self.stream.close()
        
        print("🔇 Wake word detector parado.")
    
    def is_active(self) -> bool:
        """Retorna se está escutando"""
        return self.is_listening


# === FUNÇÃO AUXILIAR PARA GRAVAR COMANDO ===

def record_command(duration: float = None, silence_stop: bool = True) -> Optional[np.ndarray]:
    """
    Grava áudio do microfone para capturar o comando do usuário.
    
    Args:
        duration: Duração máxima em segundos (None = usa config)
        silence_stop: Se True, para ao detectar silêncio
    
    Returns:
        Array numpy com o áudio gravado
    """
    duration = duration or config.record_seconds
    
    print(f"🎙️  Gravando comando (máx {duration}s)...")
    
    frames = []
    silence_frames = 0
    max_silence_frames = int(config.silence_duration * config.sample_rate / config.chunk_size)
    
    def callback(indata, frame_count, time_info, status):
        nonlocal silence_frames
        
        frames.append(indata.copy())
        
        # Detectar silêncio
        if silence_stop:
            volume = np.abs(indata).mean()
            if volume < config.silence_threshold:
                silence_frames += 1
            else:
                silence_frames = 0
    
    try:
        device = getattr(config, 'input_device', None)
        with sd.InputStream(
            samplerate=config.sample_rate,
            channels=config.channels,
            dtype='float32',
            blocksize=config.chunk_size,
            device=device,
            callback=callback
        ):
            frames_needed = int(duration * config.sample_rate / config.chunk_size)
            
            for _ in range(frames_needed):
                sd.sleep(int(1000 * config.chunk_size / config.sample_rate))
                
                # Para se detectou silêncio suficiente
                if silence_stop and silence_frames >= max_silence_frames and len(frames) > 10:
                    print("🔇 Silêncio detectado, finalizando gravação...")
                    break
        
        if frames:
            audio = np.concatenate(frames, axis=0)
            print(f"✅ Gravado {len(audio) / config.sample_rate:.1f}s de áudio")
            return audio
        
        return None
        
    except Exception as e:
        print(f"❌ Erro na gravação: {e}")
        return None


# === TESTE ===
if __name__ == "__main__":
    detector = WakeWordDetector()
    
    def on_wake():
        print("\n🚀 JARVIS ATIVADO!")
        audio = record_command()
        if audio is not None:
            print(f"Áudio capturado: {audio.shape}")
    
    if detector.start(on_wake):
        try:
            print("Pressione Ctrl+C para parar...")
            while True:
                sd.sleep(1000)
        except KeyboardInterrupt:
            detector.stop()

