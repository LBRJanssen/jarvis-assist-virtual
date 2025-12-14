# ========================================
# JARVIS - Cérebro (Ollama/Llama)
# Processa comandos e gera respostas
# ========================================

import re
import json
from typing import Optional, Dict, Any, Tuple
from dataclasses import dataclass
from datetime import datetime

import ollama
from ollama import Client

from config import config, system_prompt


@dataclass
class JarvisResponse:
    """Resposta processada do JARVIS"""
    action: Optional[str] = None  # Tipo de ação
    param: Optional[str] = None   # Parâmetro da ação
    speech: str = ""              # Texto para falar
    raw: str = ""                 # Resposta bruta do LLM


class JarvisBrain:
    """Cérebro do JARVIS - processa comandos usando Llama"""
    
    def __init__(self):
        self.client: Optional[Client] = None
        self.is_connected = False
        self.conversation_history = []
        self.max_history = 10  # Manter últimas N mensagens
    
    def initialize(self) -> bool:
        """Conecta ao Ollama"""
        try:
            print(f"🔄 Conectando ao Ollama ({config.ollama_host})...")
            
            self.client = Client(host=config.ollama_host)
            
            # Testar conexão - API v2 retorna objeto diferente
            models_response = self.client.list()
            
            # Extrair nomes dos modelos (compatível com diferentes versões da API)
            available_models = []
            if hasattr(models_response, 'models'):
                # API nova (objeto)
                for m in models_response.models:
                    if hasattr(m, 'model'):
                        available_models.append(m.model)
                    elif hasattr(m, 'name'):
                        available_models.append(m.name)
            elif isinstance(models_response, dict):
                # API antiga (dict)
                for m in models_response.get('models', []):
                    available_models.append(m.get('name', m.get('model', '')))
            
            print(f"✅ Conectado ao Ollama!")
            print(f"📋 Modelos disponíveis: {available_models}")
            
            # Verificar se o modelo desejado está disponível
            model_name = config.ollama_model.split(':')[0]
            if not any(model_name in m for m in available_models):
                print(f"⚠️  Modelo {config.ollama_model} não encontrado.")
                print(f"   Execute: ollama pull {config.ollama_model}")
                return False
            
            self.is_connected = True
            return True
            
        except Exception as e:
            print(f"❌ Erro ao conectar ao Ollama: {e}")
            print("   Certifique-se que o Ollama está rodando.")
            print("   Execute: ollama serve")
            return False
    
    def _build_context(self) -> str:
        """Constrói contexto com informações atuais"""
        now = datetime.now()
        
        context = f"""
Informações atuais:
- Data: {now.strftime('%d/%m/%Y')}
- Hora: {now.strftime('%H:%M')}
- Dia da semana: {now.strftime('%A')}
"""
        return context
    
    def _parse_response(self, response: str) -> JarvisResponse:
        """Extrai ação e parâmetros da resposta"""
        result = JarvisResponse(raw=response)
        
        # Extrair [AÇÃO: xxx]
        action_match = re.search(r'\[AÇÃO:\s*([^\]]+)\]', response)
        if action_match:
            result.action = action_match.group(1).strip().upper()
        
        # Extrair [PARAM: xxx]
        param_match = re.search(r'\[PARAM:\s*([^\]]+)\]', response)
        if param_match:
            result.param = param_match.group(1).strip()
        
        # Remover tags da fala
        speech = response
        speech = re.sub(r'\[AÇÃO:[^\]]+\]\s*', '', speech)
        speech = re.sub(r'\[PARAM:[^\]]+\]\s*', '', speech)
        result.speech = speech.strip()
        
        return result
    
    def process(self, user_input: str) -> JarvisResponse:
        """
        Processa input do usuário e retorna resposta.
        
        Args:
            user_input: Texto do comando/pergunta do usuário
        
        Returns:
            JarvisResponse com ação, parâmetro e texto para falar
        """
        if not self.is_connected:
            if not self.initialize():
                return JarvisResponse(
                    speech="Desculpe senhor, não consegui conectar ao sistema de processamento."
                )
        
        try:
            # Construir mensagens
            messages = [
                {
                    "role": "system",
                    "content": system_prompt.prompt + "\n" + self._build_context()
                }
            ]
            
            # Adicionar histórico
            messages.extend(self.conversation_history)
            
            # Adicionar mensagem atual
            messages.append({
                "role": "user",
                "content": user_input
            })
            
            print(f"🧠 Processando: '{user_input}'")
            
            # Chamar Ollama (otimizado para velocidade)
            response = self.client.chat(
                model=config.ollama_model,
                messages=messages,
                options={
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "num_predict": 128,  # Reduzido para resposta mais rápida
                    "num_ctx": 2048,     # Contexto menor = mais rápido
                },
                timeout=10.0  # Timeout de 10 segundos
            )
            
            assistant_message = response['message']['content']
            
            # Atualizar histórico
            self.conversation_history.append({"role": "user", "content": user_input})
            self.conversation_history.append({"role": "assistant", "content": assistant_message})
            
            # Limitar histórico
            if len(self.conversation_history) > self.max_history * 2:
                self.conversation_history = self.conversation_history[-self.max_history * 2:]
            
            # Parsear resposta
            result = self._parse_response(assistant_message)
            
            print(f"🤖 Resposta: {result.speech[:100]}...")
            if result.action:
                print(f"   Ação: {result.action} | Param: {result.param}")
            
            return result
            
        except Exception as e:
            print(f"❌ Erro no processamento: {e}")
            return JarvisResponse(
                speech="Desculpe senhor, ocorreu um erro no processamento."
            )
    
    def clear_history(self):
        """Limpa histórico de conversa"""
        self.conversation_history = []
        print("🗑️  Histórico de conversa limpo")
    
    def get_status(self) -> Dict[str, Any]:
        """Retorna status do cérebro"""
        return {
            "connected": self.is_connected,
            "model": config.ollama_model,
            "history_size": len(self.conversation_history)
        }


# === INSTÂNCIA GLOBAL ===
brain = JarvisBrain()


# === TESTE ===
if __name__ == "__main__":
    print("🧠 Teste do Cérebro do JARVIS")
    print("-" * 40)
    
    if not brain.initialize():
        print("Falha ao inicializar. Certifique-se que o Ollama está rodando.")
        exit(1)
    
    # Teste de comandos
    test_commands = [
        "Bom dia Jarvis",
        "Abre o Chrome",
        "Aumenta o volume",
        "Que horas são?",
        "Hora do jogo, abre o Valorant",
        "Quando Roma foi fundada?",
    ]
    
    for cmd in test_commands:
        print(f"\n{'='*50}")
        print(f"👤 Usuário: {cmd}")
        print("-" * 50)
        
        response = brain.process(cmd)
        
        print(f"🤖 JARVIS: {response.speech}")
        if response.action:
            print(f"   [Ação: {response.action}]")
            print(f"   [Param: {response.param}]")
        
        print()
        input("Pressione ENTER para próximo teste...")

