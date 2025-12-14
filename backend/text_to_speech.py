# ========================================
# JARVIS - Text to Speech
# Usa Edge TTS para síntese de voz
# ========================================

import asyncio
import tempfile
import os
from typing import Optional
from pathlib import Path

import edge_tts
import pygame

from config import config, AUDIO_DIR


class TextToSpeech:
    """Converte texto em fala usando Edge TTS"""
    
    def __init__(self):
        self.is_initialized = False
        self._init_pygame()
    
    def _init_pygame(self):
        """Inicializa o pygame mixer para reprodução"""
        try:
            pygame.mixer.init()
            self.is_initialized = True
        except Exception as e:
            print(f"⚠️  Erro ao inicializar pygame: {e}")
            self.is_initialized = False
    
    async def _generate_speech(self, text: str, output_path: str) -> bool:
        """Gera áudio a partir do texto usando Edge TTS"""
        try:
            communicate = edge_tts.Communicate(
                text,
                voice=config.tts_voice,
                rate=config.tts_rate,
                volume=config.tts_volume
            )
            
            await communicate.save(output_path)
            return True
            
        except Exception as e:
            print(f"❌ Erro na síntese de voz: {e}")
            return False
    
    def speak(self, text: str, wait: bool = True) -> bool:
        """
        Fala o texto.
        
        Args:
            text: Texto para falar
            wait: Se True, espera terminar de falar
        
        Returns:
            True se sucesso
        """
        if not text:
            return False
        
        if not self.is_initialized:
            self._init_pygame()
            if not self.is_initialized:
                print(f"🔊 [TTS desabilitado] {text}")
                return False
        
        try:
            # Usar diretório temporário do sistema
            import uuid
            temp_file = Path(tempfile.gettempdir()) / f"jarvis_tts_{uuid.uuid4().hex[:8]}.mp3"
            
            # Gerar áudio
            print(f"🔊 Falando: '{text[:50]}{'...' if len(text) > 50 else ''}'")
            
            asyncio.run(self._generate_speech(text, str(temp_file)))
            
            if not temp_file.exists():
                print("❌ Arquivo de áudio não foi gerado")
                return False
            
            # Reproduzir
            pygame.mixer.music.load(str(temp_file))
            pygame.mixer.music.play()
            
            if wait:
                while pygame.mixer.music.get_busy():
                    pygame.time.Clock().tick(10)
            
            # Limpar arquivo temporário (com delay para liberar)
            try:
                pygame.mixer.music.unload()
                temp_file.unlink()
            except:
                pass
            
            return True
            
        except Exception as e:
            print(f"❌ Erro ao falar: {e}")
            return False
    
    def speak_async(self, text: str):
        """Fala sem bloquear (fire and forget)"""
        import threading
        thread = threading.Thread(target=self.speak, args=(text, True), daemon=True)
        thread.start()
    
    def stop(self):
        """Para a fala atual"""
        try:
            pygame.mixer.music.stop()
        except:
            pass
    
    def is_speaking(self) -> bool:
        """Retorna se está falando"""
        try:
            return pygame.mixer.music.get_busy()
        except:
            return False
    
    def set_voice(self, voice: str):
        """Altera a voz"""
        config.tts_voice = voice
    
    def set_rate(self, rate: str):
        """Altera a velocidade (ex: '+10%', '-20%')"""
        config.tts_rate = rate
    
    @staticmethod
    async def list_voices() -> list:
        """Lista todas as vozes disponíveis"""
        voices = await edge_tts.list_voices()
        return voices
    
    @staticmethod
    def get_portuguese_voices() -> list:
        """Retorna vozes em português"""
        voices = asyncio.run(TextToSpeech.list_voices())
        pt_voices = [v for v in voices if v["Locale"].startswith("pt-")]
        return pt_voices


# === INSTÂNCIA GLOBAL ===
tts = TextToSpeech()


# === FUNÇÃO HELPER ===
def speak(text: str, wait: bool = True) -> bool:
    """Função helper para falar texto"""
    return tts.speak(text, wait)


# === TESTE ===
if __name__ == "__main__":
    print("🔊 Testando Text-to-Speech...")
    
    # Listar vozes portuguesas
    print("\n📋 Vozes em português disponíveis:")
    pt_voices = TextToSpeech.get_portuguese_voices()
    for v in pt_voices:
        print(f"  - {v['ShortName']}: {v['Gender']}")
    
    # Testar fala
    print("\n🎤 Testando fala...")
    tts.speak("Olá senhor, todos os sistemas operacionais e prontos para o dia.")
    tts.speak("Iniciando protocolo de teste. Sucesso confirmado.")

