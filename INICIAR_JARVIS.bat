@echo off
title J.A.R.V.I.S. - Iniciando...
color 0B

echo.
echo    ========================================
echo       J.A.R.V.I.S. - Assistente Pessoal
echo    ========================================
echo.

:: Iniciar Ollama em background (se não estiver rodando)
echo [1/3] Verificando Ollama...
tasklist /FI "IMAGENAME eq ollama.exe" 2>NUL | find /I /N "ollama.exe">NUL
if "%ERRORLEVEL%"=="1" (
    echo       Iniciando Ollama...
    start /B "" "%LOCALAPPDATA%\Programs\Ollama\ollama.exe" serve
    timeout /t 3 /nobreak >NUL
) else (
    echo       Ollama ja esta rodando!
)

:: Iniciar Backend Python
echo.
echo [2/3] Iniciando Backend...
cd /d "%~dp0backend"
start "JARVIS Backend" /MIN cmd /c "python main.py"
timeout /t 5 /nobreak >NUL

:: Iniciar Interface
echo.
echo [3/3] Iniciando Interface...
cd /d "%~dp0desktop"
start "JARVIS Interface" /MIN cmd /c "npx serve src -p 3000 -s"

:: Aguardar e abrir navegador
timeout /t 3 /nobreak >NUL
start http://localhost:3000

echo.
echo    ========================================
echo       JARVIS iniciado com sucesso!
echo    ========================================
echo.
echo    Interface: http://localhost:3000
echo    Backend: WebSocket porta 8765
echo.
echo    Pressione qualquer tecla para fechar esta janela...
echo    (O JARVIS continuara rodando em background)
echo.
pause >NUL


