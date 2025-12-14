# ========================================
# JARVIS - Speech to Text
# Usa OpenAI Whisper para transcrição
# ========================================

from typing import Optional, Tuple
import numpy as np
import tempfile
import os

from config import config, AUDIO_DIR


class SpeechToText:
    """Converte áudio em texto usando Whisper"""
    
    def __init__(self):
        self.model = None
        self.is_loaded = False
    
    def initialize(self) -> bool:
        """Carrega o modelo Whisper"""
        try:
            import whisper
            
            print(f"🔄 Carregando modelo Whisper ({config.whisper_model})...")
            print("   (Primeira vez pode demorar para baixar o modelo)")
            
            self.model = whisper.load_model(config.whisper_model)
            
            self.is_loaded = True
            print("✅ Modelo Whisper carregado!")
            return True
            
        except Exception as e:
            print(f"❌ Erro ao carregar Whisper: {e}")
            return False
    
    def transcribe(self, audio: np.ndarray) -> Tuple[str, float]:
        """
        Transcreve áudio para texto.
        
        Args:
            audio: Array numpy com áudio (float32, mono, 16kHz)
        
        Returns:
            Tuple (texto_transcrito, confiança)
        """
        if not self.is_loaded:
            if not self.initialize():
                return "", 0.0
        
        try:
            # Garantir formato correto
            if audio.dtype != np.float32:
                if audio.dtype == np.int16:
                    audio = audio.astype(np.float32) / 32768.0
                else:
                    audio = audio.astype(np.float32)
            
            # Se for stereo, converter para mono
            if len(audio.shape) > 1:
                audio = audio.mean(axis=1)
            
            # Flatten se necessário
            audio = audio.flatten()
            
            # Normalizar se necessário
            if np.abs(audio).max() > 1.0:
                audio = audio / np.abs(audio).max()
            
            # Transcrever usando Whisper
            result = self.model.transcribe(
                audio,
                language="pt",
                fp16=False,  # CPU não suporta fp16
                verbose=False
            )
            
            text = result.get("text", "").strip()
            
            # Calcular confiança média dos segmentos
            segments = result.get("segments", [])
            if segments:
                avg_confidence = sum(
                    seg.get("no_speech_prob", 0) for seg in segments
                ) / len(segments)
                confidence = 1 - avg_confidence  # Inverter (quanto menor no_speech, melhor)
            else:
                confidence = 0.5
            
            print(f"📝 Transcrição: '{text}' (confiança: {confidence:.0%})")
            
            return text, confidence
            
        except Exception as e:
            print(f"❌ Erro na transcrição: {e}")
            return "", 0.0
    
    def transcribe_file(self, file_path: str) -> Tuple[str, float]:
        """Transcreve áudio de um arquivo"""
        try:
            import soundfile as sf
            audio, sr = sf.read(file_path)
            
            # Resample se necessário
            if sr != config.sample_rate:
                from scipy import signal
                audio = signal.resample(audio, int(len(audio) * config.sample_rate / sr))
            
            return self.transcribe(audio)
            
        except Exception as e:
            print(f"❌ Erro ao ler arquivo: {e}")
            return "", 0.0


# === INSTÂNCIA GLOBAL ===
stt = SpeechToText()


# === TESTE ===
if __name__ == "__main__":
    import sounddevice as sd
    
    print("🎤 Gravando 5 segundos de áudio para teste...")
    
    audio = sd.rec(
        int(5 * config.sample_rate),
        samplerate=config.sample_rate,
        channels=1,
        dtype='float32'
    )
    sd.wait()
    
    print("🔄 Transcrevendo...")
    texto, confianca = stt.transcribe(audio.flatten())
    
    print(f"\n📝 Resultado: '{texto}'")
    print(f"📊 Confiança: {confianca:.0%}")
