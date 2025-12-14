# 📱 JARVIS Mobile - Plano Futuro

## 🎯 Objetivo

Criar um **aplicativo próprio** para celular que permita comandar o JARVIS por **voz** e executar ações no **computador**.

---

## 📋 Requisitos

| Requisito | Descrição |
|-----------|-----------|
| **Tipo** | App nativo próprio (não Telegram/WhatsApp) |
| **Entrada** | Comando de voz (igual no PC) |
| **Execução** | No computador (não no celular) |
| **Conexão** | Via internet (funciona de qualquer lugar) |

---

## 🔄 Fluxo Planejado

```
┌─────────────────────────────────────────────────────────┐
│  📱 APP JARVIS (Celular)                                │
│                                                         │
│  1. Você abre o app                                     │
│  2. Fala: "Jarvis, abre o Discord"                      │
│  3. App converte voz → texto                            │
│  4. Envia comando para o PC via internet                │
└─────────────────────────────────────────────────────────┘
                          ↓
                    🌐 Internet
                          ↓
┌─────────────────────────────────────────────────────────┐
│  🖥️ PC (JARVIS rodando)                                 │
│                                                         │
│  5. Recebe o comando                                    │
│  6. Processa com Llama 3.1                              │
│  7. Executa ação (abre Discord)                         │
│  8. Envia resposta de volta pro celular                 │
└─────────────────────────────────────────────────────────┘
                          ↓
                    🌐 Internet
                          ↓
┌─────────────────────────────────────────────────────────┐
│  📱 APP JARVIS (Celular)                                │
│                                                         │
│  9. Recebe resposta                                     │
│  10. Fala: "Abrindo o Discord, senhor."                 │
└─────────────────────────────────────────────────────────┘
```

---

## 🛠️ Tecnologias Planejadas

| Componente | Opções |
|------------|--------|
| **Framework App** | Flutter ou React Native |
| **Comunicação** | WebSocket ou API REST |
| **Speech-to-Text (celular)** | Nativo do dispositivo ou Whisper |
| **Text-to-Speech (celular)** | Nativo do dispositivo ou voz clonada |
| **Servidor** | PC rodando servidor FastAPI/WebSocket |
| **Túnel Internet** | Ngrok, Cloudflare Tunnel, ou IP fixo |

---

## 📲 Funcionalidades do App

### MVP (Versão Inicial)
- [ ] Botão para ativar microfone
- [ ] Enviar comando de voz para o PC
- [ ] Receber resposta em texto
- [ ] Ouvir resposta por voz

### Versão Completa (Futuro)
- [ ] Wake word "Jarvis" no celular também
- [ ] Autenticação por voz (só sua voz)
- [ ] Visual com partículas igual no PC
- [ ] Notificações do PC no celular
- [ ] Ver status do PC em tempo real
- [ ] Histórico de comandos

---

## ⚠️ Desafios a Resolver

1. **Conexão via Internet**
   - PC precisa estar acessível de fora
   - Opções: Ngrok, Cloudflare Tunnel, VPN, IP fixo

2. **Segurança**
   - Autenticação para não deixar qualquer um controlar seu PC
   - Criptografia na comunicação

3. **Latência**
   - Voz → Texto → Internet → PC → Resposta → Internet → Celular
   - Pode ter delay de 2-5 segundos

---

## 📅 Quando Implementar

**Fase atual:** ❌ Não incluído

**Pré-requisitos:**
1. JARVIS desktop funcionando 100%
2. Servidor de API rodando no PC
3. Conhecimento em Flutter/React Native

**Prioridade:** Depois que o JARVIS no PC estiver completo e testado.

---

*Este documento será atualizado quando iniciarmos o desenvolvimento mobile.*


