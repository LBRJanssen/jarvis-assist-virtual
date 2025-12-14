# 🤖 J.A.R.V.I.S. - Assistente de Voz Pessoal

Assistente de voz inteligente para Windows, inspirado no JARVIS do Iron Man.

## ✨ Funcionalidades

- 🎤 **Wake Word** - Ativação por voz usando Porcupine
- 🧠 **IA Local** - Processamento com Llama 3.1 via Ollama
- 🎨 **Interface Visual** - Partículas 3D reativas (Tauri)
- 🔊 **TTS/STT** - Whisper para transcrição, Edge TTS para síntese
- 🔐 **Autenticação por Voz** - Apenas você pode comandar
- 💻 **Controle do PC** - Abre apps, controla volume, etc.

## 🚀 Instalação

### Pré-requisitos

- Python 3.12+
- Rust (para Tauri)
- Node.js 18+
- Ollama instalado
- C++ Build Tools (para compilar dependências)

### Passo a Passo

1. **Clone o repositório**
```bash
git clone https://github.com/seu-usuario/jarvis.git
cd jarvis
```

2. **Instale dependências Python**
```bash
cd backend
pip install -r requirements.txt
```

3. **Configure Porcupine**
   - Acesse: https://console.picovoice.ai/
   - Crie conta gratuita
   - Copie sua Access Key
   - Cole em `backend/config.py` → `porcupine_access_key`

4. **Baixe modelo Vosk (opcional)**
```bash
cd backend/data
# O modelo será baixado automaticamente na primeira execução
```

5. **Instale modelo Ollama**
```bash
ollama pull llama3.1:8b
```

6. **Compile interface Tauri**
```bash
cd desktop
npm install
npx tauri build
```

## 🎮 Uso

### Iniciar JARVIS

**Opção 1: Script automático**
```bash
./JARVIS.bat
```

**Opção 2: Manual**
```bash
# Terminal 1 - Backend
cd backend
python main.py

# Terminal 2 - Interface (opcional, se não usar Tauri)
cd desktop/src
python -m http.server 3000
```

### Comandos

Diga **"Jarvis"** para ativar, depois:

- "Abre o Chrome"
- "Aumenta o volume"
- "Que horas são?"
- "Abre o Valorant"
- "Qual a previsão do tempo?"

## 📁 Estrutura

```
jarvis/
├── backend/          # Backend Python
│   ├── main.py      # Fluxo principal
│   ├── brain.py     # IA (Ollama)
│   ├── wake_word_porcupine.py  # Detecção wake word
│   ├── speech_to_text.py  # Whisper
│   ├── text_to_speech.py  # Edge TTS
│   └── ...
├── desktop/          # Interface Tauri
│   ├── src/         # Frontend (HTML/JS)
│   └── src-tauri/   # Backend Rust
└── README.md
```

## ⚙️ Configuração

Edite `backend/config.py` para personalizar:

- Wake word
- Dispositivo de áudio
- Modelo Whisper
- Voz TTS
- Modelo Ollama

## 🐛 Troubleshooting

**JARVIS não responde:**
- Verifique se Ollama está rodando: `ollama serve`
- Verifique dispositivo de áudio em `config.py`

**Erro de porta 8765:**
- Feche outros processos Python
- Ou mude a porta em `config.py`

**Porcupine não funciona:**
- Verifique se a Access Key está correta
- Obtenha nova chave em: https://console.picovoice.ai/

## 📝 Licença

MIT License - Use livremente!

## 🙏 Créditos

- **Porcupine** - Picovoice (Wake Word)
- **Whisper** - OpenAI (Speech-to-Text)
- **Ollama** - Llama 3.1 (IA)
- **Edge TTS** - Microsoft (Text-to-Speech)
- **Tauri** - Framework Desktop

---

**Desenvolvido com ❤️ para automação pessoal**
