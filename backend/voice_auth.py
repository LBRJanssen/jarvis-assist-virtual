# ========================================
# JARVIS - Autenticação por Voz
# Usa Resemblyzer para verificação
# ========================================

import numpy as np
from pathlib import Path
from typing import Optional, Tuple, List
import sounddevice as sd
import soundfile as sf

from config import config, VOICE_PROFILES_DIR, AUDIO_DIR

# webrtcvad é opcional (precisa de compilador C++)
WEBRTCVAD_AVAILABLE = False
try:
    import webrtcvad
    WEBRTCVAD_AVAILABLE = True
except ImportError:
    pass


class VoiceAuthenticator:
    """Autentica usuário pela voz usando Resemblyzer"""
    
    def __init__(self):
        self.encoder = None
        self.user_embedding: Optional[np.ndarray] = None
        self.is_loaded = False
    
    def initialize(self) -> bool:
        """Carrega o modelo de autenticação"""
        try:
            from resemblyzer import VoiceEncoder
            
            print("🔄 Carregando modelo de autenticação por voz...")
            self.encoder = VoiceEncoder()
            self.is_loaded = True
            print("✅ Modelo de voz carregado!")
            
            # Tentar carregar perfil existente
            self._load_profile()
            
            return True
            
        except Exception as e:
            print(f"❌ Erro ao carregar Resemblyzer: {e}")
            return False
    
    def _load_profile(self) -> bool:
        """Carrega perfil de voz salvo"""
        profile_path = Path(config.voice_profile_path)
        
        if profile_path.exists():
            try:
                self.user_embedding = np.load(str(profile_path))
                print(f"✅ Perfil de voz carregado: {profile_path.name}")
                return True
            except Exception as e:
                print(f"⚠️  Erro ao carregar perfil: {e}")
        
        return False
    
    def _save_profile(self) -> bool:
        """Salva perfil de voz"""
        if self.user_embedding is None:
            return False
        
        try:
            profile_path = Path(config.voice_profile_path)
            np.save(str(profile_path), self.user_embedding)
            print(f"✅ Perfil de voz salvo: {profile_path.name}")
            return True
        except Exception as e:
            print(f"❌ Erro ao salvar perfil: {e}")
            return False
    
    def _preprocess_audio(self, audio: np.ndarray) -> np.ndarray:
        """Preprocessa áudio para o Resemblyzer"""
        from resemblyzer import preprocess_wav
        
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
        
        # Preprocessar
        return preprocess_wav(audio, source_sr=config.sample_rate)
    
    def enroll(self, audio_samples: List[np.ndarray]) -> bool:
        """
        Cadastra a voz do usuário.
        
        Args:
            audio_samples: Lista de arrays de áudio
        
        Returns:
            True se cadastrado com sucesso
        """
        if not self.is_loaded:
            if not self.initialize():
                return False
        
        try:
            print(f"🔄 Processando {len(audio_samples)} amostras de voz...")
            
            embeddings = []
            for i, audio in enumerate(audio_samples):
                print(f"   Processando amostra {i + 1}/{len(audio_samples)}...")
                processed = self._preprocess_audio(audio)
                embedding = self.encoder.embed_utterance(processed)
                embeddings.append(embedding)
            
            # Média dos embeddings
            self.user_embedding = np.mean(embeddings, axis=0)
            
            # Salvar perfil
            self._save_profile()
            
            print("✅ Voz cadastrada com sucesso!")
            return True
            
        except Exception as e:
            print(f"❌ Erro no cadastro de voz: {e}")
            return False
    
    def verify(self, audio: np.ndarray) -> Tuple[bool, float]:
        """
        Verifica se o áudio pertence ao usuário cadastrado.
        
        Args:
            audio: Array de áudio para verificar
        
        Returns:
            Tuple (é_autorizado, similaridade)
        """
        if not config.voice_auth_enabled:
            return True, 1.0
        
        if self.user_embedding is None:
            print("⚠️  Nenhum perfil de voz cadastrado. Pulando autenticação.")
            return True, 1.0
        
        if not self.is_loaded:
            if not self.initialize():
                return True, 0.0  # Falha segura: permite acesso
        
        try:
            # Preprocessar e extrair embedding
            processed = self._preprocess_audio(audio)
            test_embedding = self.encoder.embed_utterance(processed)
            
            # Calcular similaridade (produto escalar normalizado)
            similarity = np.dot(self.user_embedding, test_embedding)
            
            # Verificar threshold
            is_authorized = similarity >= config.voice_auth_threshold
            
            status = "✅ Autorizado" if is_authorized else "❌ Não autorizado"
            print(f"🔐 Verificação de voz: {status} (similaridade: {similarity:.2%})")
            
            return is_authorized, float(similarity)
            
        except Exception as e:
            print(f"❌ Erro na verificação: {e}")
            return True, 0.0  # Falha segura
    
    def has_profile(self) -> bool:
        """Verifica se existe perfil cadastrado"""
        return self.user_embedding is not None
    
    def delete_profile(self) -> bool:
        """Remove o perfil de voz"""
        try:
            profile_path = Path(config.voice_profile_path)
            if profile_path.exists():
                profile_path.unlink()
            self.user_embedding = None
            print("✅ Perfil de voz removido")
            return True
        except Exception as e:
            print(f"❌ Erro ao remover perfil: {e}")
            return False


# === INSTÂNCIA GLOBAL ===
voice_auth = VoiceAuthenticator()


# === FUNÇÃO DE CADASTRO INTERATIVO ===
def enroll_voice_interactive():
    """Cadastra a voz do usuário de forma interativa"""
    
    print("\n" + "="*50)
    print("🎤 CADASTRO DE VOZ - JARVIS")
    print("="*50)
    print("\nVocê vai gravar 5 frases para cadastrar sua voz.")
    print("Fale de forma natural e clara.\n")
    
    phrases = [
        "Jarvis, ativar sistema de segurança",
        "Meu nome é Lucas e essa é minha voz",
        "Abrir configurações do computador",
        "Reproduzir minha playlist favorita",
        "Qual a previsão do tempo para amanhã"
    ]
    
    audio_samples = []
    
    for i, phrase in enumerate(phrases):
        print(f"\n📝 Frase {i + 1}/5: \"{phrase}\"")
        input("   Pressione ENTER quando estiver pronto...")
        
        print("   🔴 Gravando (fale agora)...")
        
        audio = sd.rec(
            int(4 * config.sample_rate),
            samplerate=config.sample_rate,
            channels=1,
            dtype='float32'
        )
        sd.wait()
        
        audio_samples.append(audio.flatten())
        print("   ✅ Gravado!")
    
    print("\n🔄 Processando amostras...")
    
    if voice_auth.enroll(audio_samples):
        print("\n✅ VOZ CADASTRADA COM SUCESSO!")
        print("   Agora apenas você pode controlar o JARVIS.")
    else:
        print("\n❌ Erro no cadastro. Tente novamente.")


# === TESTE ===
if __name__ == "__main__":
    print("🔐 Teste de Autenticação por Voz")
    print("-" * 40)
    
    if not voice_auth.initialize():
        print("Falha ao inicializar")
        exit(1)
    
    if not voice_auth.has_profile():
        print("\n⚠️  Nenhum perfil cadastrado.")
        resposta = input("Deseja cadastrar sua voz agora? (s/n): ")
        
        if resposta.lower() == 's':
            enroll_voice_interactive()
    
    else:
        print("\n✅ Perfil de voz encontrado!")
        print("\n🎤 Vamos testar a verificação.")
        input("Pressione ENTER e fale algo...")
        
        print("🔴 Gravando...")
        audio = sd.rec(
            int(3 * config.sample_rate),
            samplerate=config.sample_rate,
            channels=1,
            dtype='float32'
        )
        sd.wait()
        
        autorizado, similaridade = voice_auth.verify(audio.flatten())
        
        if autorizado:
            print(f"\n✅ VOZ RECONHECIDA! (Similaridade: {similaridade:.2%})")
        else:
            print(f"\n❌ VOZ NÃO RECONHECIDA (Similaridade: {similaridade:.2%})")

