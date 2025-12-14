@echo off
:: Inicia JARVIS silenciosamente

:: Iniciar Ollama
start "" /B "%LOCALAPPDATA%\Programs\Ollama\ollama.exe" serve 2>nul

:: Iniciar Backend Python (janela minimizada)
start "JARVIS_BACKEND" /MIN cmd /c "cd /d %~dp0backend && python main.py"

:: Aguardar backend iniciar
:loop
timeout /t 1 /nobreak >nul
netstat -an 2>nul | find "8765" | find "LISTENING" >nul
if errorlevel 1 goto loop

:: Abrir interface
start "" "%~dp0desktop\src-tauri\target\release\jarvis.exe"
