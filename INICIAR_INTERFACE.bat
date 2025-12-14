@echo off
title J.A.R.V.I.S. - Interface
color 0B

echo.
echo  Iniciando servidor da interface...
echo  Abra no navegador: http://localhost:3000
echo.
echo  Pressione Ctrl+C para encerrar
echo.

cd desktop\src
start http://localhost:3000
python -m http.server 3000


