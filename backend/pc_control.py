# ========================================
# JARVIS - Controle do PC
# Executa ações no Windows
# ========================================

import os
import subprocess
import webbrowser
from typing import Optional, Tuple
from datetime import datetime

import psutil
import pyautogui
import pyperclip

from config import config


class PCController:
    """Controla o PC Windows"""
    
    def __init__(self):
        # Desabilitar failsafe do pyautogui (mover mouse pro canto não para)
        pyautogui.FAILSAFE = False
        pyautogui.PAUSE = 0.1
    
    # === PROGRAMAS ===
    
    def open_program(self, program: str) -> Tuple[bool, str]:
        """Abre um programa"""
        program_lower = program.lower().strip()
        
        # Verificar se tem caminho personalizado
        if program_lower in config.programs:
            path = config.programs[program_lower]
        else:
            path = program_lower
        
        try:
            # Tentar abrir
            if os.path.exists(path):
                os.startfile(path)
            else:
                # Tentar como comando
                subprocess.Popen(path, shell=True)
            
            return True, f"Programa '{program}' aberto"
            
        except Exception as e:
            return False, f"Erro ao abrir '{program}': {e}"
    
    def close_program(self, program: str) -> Tuple[bool, str]:
        """Fecha um programa"""
        program_lower = program.lower()
        
        try:
            # Mapear nomes comuns para nomes de processo
            process_map = {
                "chrome": "chrome.exe",
                "brave": "brave.exe",
                "firefox": "firefox.exe",
                "discord": "Discord.exe",
                "spotify": "Spotify.exe",
                "vscode": "Code.exe",
                "code": "Code.exe",
                "notepad": "notepad.exe",
                "explorer": "explorer.exe",
            }
            
            process_name = process_map.get(program_lower, f"{program_lower}.exe")
            
            # Encontrar e matar processo
            killed = False
            for proc in psutil.process_iter(['name']):
                if proc.info['name'].lower() == process_name.lower():
                    proc.kill()
                    killed = True
            
            if killed:
                return True, f"Programa '{program}' fechado"
            else:
                return False, f"Programa '{program}' não encontrado"
                
        except Exception as e:
            return False, f"Erro ao fechar '{program}': {e}"
    
    def close_all_programs(self) -> Tuple[bool, str]:
        """Fecha todos os programas (exceto essenciais)"""
        essential = ['explorer.exe', 'python.exe', 'pythonw.exe', 'ollama.exe', 'cmd.exe', 'powershell.exe']
        
        try:
            closed = 0
            for proc in psutil.process_iter(['name', 'pid']):
                name = proc.info['name'].lower()
                if name not in essential and proc.info['pid'] != os.getpid():
                    try:
                        # Só fechar processos com janela
                        if proc.status() == psutil.STATUS_RUNNING:
                            proc.terminate()
                            closed += 1
                    except:
                        pass
            
            return True, f"{closed} programas fechados"
            
        except Exception as e:
            return False, f"Erro ao fechar programas: {e}"
    
    # === VOLUME ===
    
    def set_volume(self, action: str) -> Tuple[bool, str]:
        """Controla o volume do sistema"""
        try:
            from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
            from comtypes import CLSCTX_ALL
            from ctypes import cast, POINTER
            
            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            volume = cast(interface, POINTER(IAudioEndpointVolume))
            
            current = volume.GetMasterVolumeLevelScalar()
            
            action_lower = action.lower()
            
            if "mudo" in action_lower or "mute" in action_lower:
                volume.SetMute(1, None)
                return True, "Volume mutado"
            
            elif "desmudo" in action_lower or "unmute" in action_lower:
                volume.SetMute(0, None)
                return True, "Volume desmutado"
            
            elif "aumentar" in action_lower or "+" in action_lower:
                # Extrair valor ou usar padrão
                import re
                match = re.search(r'(\d+)', action)
                increment = int(match.group(1)) / 100 if match else 0.1
                
                new_vol = min(1.0, current + increment)
                volume.SetMasterVolumeLevelScalar(new_vol, None)
                return True, f"Volume: {int(new_vol * 100)}%"
            
            elif "diminuir" in action_lower or "-" in action_lower:
                import re
                match = re.search(r'(\d+)', action)
                decrement = int(match.group(1)) / 100 if match else 0.1
                
                new_vol = max(0.0, current - decrement)
                volume.SetMasterVolumeLevelScalar(new_vol, None)
                return True, f"Volume: {int(new_vol * 100)}%"
            
            elif "%" in action_lower:
                import re
                match = re.search(r'(\d+)', action)
                if match:
                    new_vol = int(match.group(1)) / 100
                    new_vol = max(0.0, min(1.0, new_vol))
                    volume.SetMasterVolumeLevelScalar(new_vol, None)
                    return True, f"Volume: {int(new_vol * 100)}%"
            
            return False, "Comando de volume não reconhecido"
            
        except Exception as e:
            return False, f"Erro ao controlar volume: {e}"
    
    # === BRILHO ===
    
    def set_brightness(self, action: str) -> Tuple[bool, str]:
        """Controla o brilho da tela"""
        try:
            import screen_brightness_control as sbc
            
            current = sbc.get_brightness()[0]
            action_lower = action.lower()
            
            if "aumentar" in action_lower or "+" in action_lower:
                import re
                match = re.search(r'(\d+)', action)
                increment = int(match.group(1)) if match else 10
                
                new_brightness = min(100, current + increment)
                sbc.set_brightness(new_brightness)
                return True, f"Brilho: {new_brightness}%"
            
            elif "diminuir" in action_lower or "-" in action_lower:
                import re
                match = re.search(r'(\d+)', action)
                decrement = int(match.group(1)) if match else 10
                
                new_brightness = max(0, current - decrement)
                sbc.set_brightness(new_brightness)
                return True, f"Brilho: {new_brightness}%"
            
            elif "%" in action_lower or action_lower.isdigit():
                import re
                match = re.search(r'(\d+)', action)
                if match:
                    new_brightness = max(0, min(100, int(match.group(1))))
                    sbc.set_brightness(new_brightness)
                    return True, f"Brilho: {new_brightness}%"
            
            elif "máximo" in action_lower or "max" in action_lower:
                sbc.set_brightness(100)
                return True, "Brilho: 100%"
            
            elif "mínimo" in action_lower or "min" in action_lower:
                sbc.set_brightness(10)
                return True, "Brilho: 10%"
            
            return False, "Comando de brilho não reconhecido"
            
        except Exception as e:
            return False, f"Erro ao controlar brilho: {e}"
    
    # === MÍDIA ===
    
    def media_control(self, action: str) -> Tuple[bool, str]:
        """Controla reprodução de mídia"""
        try:
            import keyboard
            
            action_lower = action.lower()
            
            if "play" in action_lower or "pause" in action_lower or "pausa" in action_lower:
                keyboard.send('play/pause media')
                return True, "Play/Pause"
            
            elif "próxim" in action_lower or "next" in action_lower or "proximo" in action_lower:
                keyboard.send('next track')
                return True, "Próxima faixa"
            
            elif "anterior" in action_lower or "previous" in action_lower or "volta" in action_lower:
                keyboard.send('previous track')
                return True, "Faixa anterior"
            
            elif "para" in action_lower or "stop" in action_lower:
                keyboard.send('stop media')
                return True, "Mídia parada"
            
            return False, "Comando de mídia não reconhecido"
            
        except Exception as e:
            return False, f"Erro ao controlar mídia: {e}"
    
    # === SISTEMA ===
    
    def system_control(self, action: str) -> Tuple[bool, str]:
        """Controla o sistema (desligar, reiniciar, etc)"""
        action_lower = action.lower()
        
        try:
            if "desligar" in action_lower or "shutdown" in action_lower:
                os.system("shutdown /s /t 5")
                return True, "Desligando em 5 segundos"
            
            elif "reiniciar" in action_lower or "restart" in action_lower:
                os.system("shutdown /r /t 5")
                return True, "Reiniciando em 5 segundos"
            
            elif "suspender" in action_lower or "sleep" in action_lower:
                os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")
                return True, "Suspendendo sistema"
            
            elif "bloquear" in action_lower or "lock" in action_lower:
                os.system("rundll32.exe user32.dll,LockWorkStation")
                return True, "Tela bloqueada"
            
            elif "cancelar" in action_lower:
                os.system("shutdown /a")
                return True, "Desligamento cancelado"
            
            return False, "Comando de sistema não reconhecido"
            
        except Exception as e:
            return False, f"Erro no comando de sistema: {e}"
    
    def get_system_info(self) -> dict:
        """Retorna informações do sistema"""
        try:
            cpu = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            return {
                "cpu": f"{cpu}%",
                "ram": f"{memory.percent}%",
                "ram_used": f"{memory.used / (1024**3):.1f}GB",
                "ram_total": f"{memory.total / (1024**3):.1f}GB",
                "disk": f"{disk.percent}%",
                "disk_used": f"{disk.used / (1024**3):.1f}GB",
                "disk_total": f"{disk.total / (1024**3):.1f}GB",
            }
        except Exception as e:
            return {"error": str(e)}
    
    # === NAVEGADOR / SITES ===
    
    def open_website(self, url: str) -> Tuple[bool, str]:
        """Abre um site no navegador"""
        try:
            # Adicionar https se necessário
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            
            webbrowser.open(url)
            return True, f"Abrindo {url}"
            
        except Exception as e:
            return False, f"Erro ao abrir site: {e}"
    
    def search_web(self, query: str) -> Tuple[bool, str]:
        """Pesquisa no Google"""
        try:
            url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
            webbrowser.open(url)
            return True, f"Pesquisando: {query}"
            
        except Exception as e:
            return False, f"Erro na pesquisa: {e}"
    
    # === ARQUIVOS / PASTAS ===
    
    def open_folder(self, path: str) -> Tuple[bool, str]:
        """Abre uma pasta no Explorer"""
        try:
            # Pastas especiais
            special_folders = {
                "downloads": os.path.expanduser("~/Downloads"),
                "documentos": os.path.expanduser("~/Documents"),
                "desktop": os.path.expanduser("~/Desktop"),
                "área de trabalho": os.path.expanduser("~/Desktop"),
                "imagens": os.path.expanduser("~/Pictures"),
                "músicas": os.path.expanduser("~/Music"),
                "música": os.path.expanduser("~/Music"),
                "videos": os.path.expanduser("~/Videos"),
                "vídeos": os.path.expanduser("~/Videos"),
            }
            
            folder = special_folders.get(path.lower(), path)
            
            if os.path.exists(folder):
                os.startfile(folder)
                return True, f"Abrindo pasta: {folder}"
            else:
                return False, f"Pasta não encontrada: {folder}"
                
        except Exception as e:
            return False, f"Erro ao abrir pasta: {e}"
    
    # === DIGITAÇÃO ===
    
    def type_text(self, text: str, press_enter: bool = False) -> Tuple[bool, str]:
        """Digita texto onde o cursor estiver"""
        try:
            pyautogui.write(text, interval=0.02)
            
            if press_enter:
                pyautogui.press('enter')
            
            return True, f"Digitado: {text[:30]}..."
            
        except Exception as e:
            return False, f"Erro ao digitar: {e}"
    
    def paste_text(self, text: str) -> Tuple[bool, str]:
        """Cola texto (mais rápido para textos longos)"""
        try:
            pyperclip.copy(text)
            pyautogui.hotkey('ctrl', 'v')
            return True, f"Colado: {text[:30]}..."
            
        except Exception as e:
            return False, f"Erro ao colar: {e}"
    
    # === DISCORD ===
    
    def open_discord_dm(self, contact_name: str) -> Tuple[bool, str]:
        """Abre DM no Discord"""
        try:
            user_id = config.discord_contacts.get(contact_name.lower())
            
            if not user_id:
                return False, f"Contato '{contact_name}' não encontrado nas configurações"
            
            url = f"discord://discord.com/users/{user_id}"
            os.startfile(url)
            
            return True, f"Abrindo conversa com {contact_name}"
            
        except Exception as e:
            return False, f"Erro ao abrir Discord: {e}"
    
    def open_discord_channel(self, channel_name: str) -> Tuple[bool, str]:
        """Abre canal no Discord"""
        try:
            channel_id = config.discord_channels.get(channel_name.lower())
            
            if not channel_id:
                return False, f"Canal '{channel_name}' não encontrado nas configurações"
            
            # channel_id deve ser no formato "server_id/channel_id"
            url = f"discord://discord.com/channels/{channel_id}"
            os.startfile(url)
            
            return True, f"Abrindo canal {channel_name}"
            
        except Exception as e:
            return False, f"Erro ao abrir Discord: {e}"
    
    # === INFO ===
    
    def get_time(self) -> str:
        """Retorna hora atual"""
        now = datetime.now()
        return now.strftime("%H:%M")
    
    def get_date(self) -> str:
        """Retorna data atual"""
        now = datetime.now()
        return now.strftime("%d/%m/%Y")


# === INSTÂNCIA GLOBAL ===
pc = PCController()


# === EXECUTOR DE AÇÕES ===

def execute_action(action: str, param: str = None) -> Tuple[bool, str]:
    """
    Executa uma ação baseada no tipo.
    
    Args:
        action: Tipo de ação (ABRIR_PROGRAMA, VOLUME, etc)
        param: Parâmetro da ação
    
    Returns:
        Tuple (sucesso, mensagem)
    """
    action = action.upper() if action else ""
    
    actions_map = {
        "ABRIR_PROGRAMA": lambda: pc.open_program(param),
        "FECHAR_PROGRAMA": lambda: pc.close_program(param),
        "ENCERRAR_TUDO": lambda: pc.close_all_programs(),
        "VOLUME": lambda: pc.set_volume(param),
        "BRILHO": lambda: pc.set_brightness(param),
        "MIDIA": lambda: pc.media_control(param),
        "SISTEMA": lambda: pc.system_control(param),
        "PESQUISAR": lambda: pc.search_web(param),
        "ABRIR_SITE": lambda: pc.open_website(param),
        "ABRIR_PASTA": lambda: pc.open_folder(param),
        "DIGITAR": lambda: pc.type_text(param),
        "DISCORD_DM": lambda: pc.open_discord_dm(param),
        "DISCORD_CANAL": lambda: pc.open_discord_channel(param),
        "INFO_HORA": lambda: (True, f"São {pc.get_time()}"),
        "INFO_SISTEMA": lambda: (True, str(pc.get_system_info())),
        "NENHUMA": lambda: (True, "Sem ação"),
    }
    
    if action in actions_map:
        return actions_map[action]()
    
    return False, f"Ação desconhecida: {action}"


# === TESTE ===
if __name__ == "__main__":
    print("🖥️  Teste de Controle do PC")
    print("-" * 40)
    
    # Teste de info do sistema
    print("\n📊 Info do Sistema:")
    info = pc.get_system_info()
    for k, v in info.items():
        print(f"   {k}: {v}")
    
    # Teste de hora
    print(f"\n⏰ Hora: {pc.get_time()}")
    print(f"📅 Data: {pc.get_date()}")
    
    # Teste interativo
    print("\n" + "="*50)
    print("Digite comandos para testar (ou 'sair'):")
    print("Exemplos: abrir chrome, volume 50%, brilho aumentar")
    print("="*50)
    
    while True:
        cmd = input("\n> ").strip()
        
        if cmd.lower() == 'sair':
            break
        
        # Parsear comando simples
        parts = cmd.split(' ', 1)
        action = parts[0].upper()
        param = parts[1] if len(parts) > 1 else None
        
        # Mapear comandos de teste
        if action == "ABRIR":
            action = "ABRIR_PROGRAMA"
        elif action == "FECHAR":
            action = "FECHAR_PROGRAMA"
        
        success, msg = execute_action(action, param)
        print(f"{'✅' if success else '❌'} {msg}")


