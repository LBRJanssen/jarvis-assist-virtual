# ========================================
# JARVIS - WebSocket Server
# Conecta o backend com a interface
# ========================================

import asyncio
import json
from typing import Set, Optional
from dataclasses import dataclass, asdict
from enum import Enum

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import uvicorn


class JarvisState(str, Enum):
    IDLE = "idle"
    LISTENING = "listening"
    PROCESSING = "processing"
    EXECUTING = "executing"
    ERROR = "error"


@dataclass
class StateMessage:
    type: str = "state"
    state: str = "idle"
    text: str = ""


class ConnectionManager:
    """Gerencia conexões WebSocket"""
    
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self.current_state = JarvisState.IDLE
        self.current_text = "Aguardando 'Jarvis'..."
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)
        # Enviar estado atual para novo cliente
        await self.send_state(websocket, self.current_state, self.current_text)
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)
    
    async def send_state(self, websocket: WebSocket, state: JarvisState, text: str = ""):
        message = StateMessage(type="state", state=state.value, text=text)
        await websocket.send_json(asdict(message))
    
    async def broadcast_state(self, state: JarvisState, text: str = ""):
        self.current_state = state
        self.current_text = text
        
        message = StateMessage(type="state", state=state.value, text=text)
        
        disconnected = set()
        for connection in self.active_connections:
            try:
                await connection.send_json(asdict(message))
            except:
                disconnected.add(connection)
        
        # Remover conexões mortas
        self.active_connections -= disconnected
    
    async def broadcast(self, data: dict):
        disconnected = set()
        for connection in self.active_connections:
            try:
                await connection.send_json(data)
            except:
                disconnected.add(connection)
        
        self.active_connections -= disconnected


# === INSTÂNCIAS GLOBAIS ===
app = FastAPI(title="JARVIS Backend")
manager = ConnectionManager()


# === ROTAS ===

@app.get("/")
async def root():
    return FileResponse("../desktop/src/index.html")


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Processar comandos da interface (se necessário)
            message = json.loads(data)
            print(f"📩 Recebido: {message}")
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)


# === API para o main.py controlar a interface ===

async def set_state(state: JarvisState, text: str = ""):
    """Atualiza o estado na interface"""
    await manager.broadcast_state(state, text)


async def send_transcription(text: str):
    """Envia transcrição para a interface"""
    await manager.broadcast({
        "type": "transcription",
        "text": text
    })


async def send_response(text: str):
    """Envia resposta do JARVIS para a interface"""
    await manager.broadcast({
        "type": "response", 
        "text": text
    })


async def send_error(text: str):
    """Envia erro para a interface"""
    await manager.broadcast({
        "type": "error",
        "text": text
    })


# === SERVIDOR ===

def run_server(host: str = "127.0.0.1", port: int = 8765):
    """Inicia o servidor WebSocket"""
    # Nota: arquivos estáticos são servidos pelo Tauri, não precisamos montar aqui
    uvicorn.run(app, host=host, port=port, log_level="warning")


if __name__ == "__main__":
    print("🌐 Iniciando servidor JARVIS...")
    print("   WebSocket: ws://127.0.0.1:8765/ws")
    print("   Interface: http://127.0.0.1:8765/")
    run_server()

