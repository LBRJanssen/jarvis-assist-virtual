@echo off
title J.A.R.V.I.S. - Iniciando...
color 0B

echo.
echo  ========================================
echo     J.A.R.V.I.S. - Assistente Pessoal
echo  ========================================
echo.

:: Verificar Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERRO] Python nao encontrado!
    pause
    exit /b 1
)

:: Verificar Ollama
echo [1/3] Verificando Ollama...
"%LOCALAPPDATA%\Programs\Ollama\ollama.exe" list >nul 2>&1
if %errorlevel% neq 0 (
    echo [AVISO] Iniciando Ollama...
    start "" "%LOCALAPPDATA%\Programs\Ollama\ollama.exe" serve
    timeout /t 3 >nul
)

:: Iniciar servidor da interface
echo [2/3] Iniciando servidor da interface...
start "" /min cmd /c "cd desktop\src && python -m http.server 3000"
timeout /t 2 >nul

:: Abrir interface no navegador
echo [3/3] Abrindo interface...
start http://localhost:3000

:: Iniciar JARVIS
echo.
echo  ========================================
echo     JARVIS iniciado!
echo     Interface: http://localhost:3000
echo     Pressione Ctrl+C para encerrar
echo  ========================================
echo.

cd backend
python main.py

pause


