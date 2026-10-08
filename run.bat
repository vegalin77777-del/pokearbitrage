@echo off
title PokeArbitrage Pro - Pokemon Card Scanner
echo =======================================================
echo   PokeArbitrage Pro - 寶可夢神卡雷達與跨平台比價獵手
echo =======================================================
echo.
echo 正在啟動本地 Web 控制台伺服器 (http://127.0.0.1:5500)...
cd /d "%~dp0"
python app.py
pause
