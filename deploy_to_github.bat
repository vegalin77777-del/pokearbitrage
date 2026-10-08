@echo off
title Push to GitHub for Cloud Deployment
echo ========================================================
echo   PokeArbitrage Pro - 一鍵推送到 GitHub 準備雲端部署
echo ========================================================
echo.
echo 請先在 https://github.com/new 建立一個新的空白專案 (例如命名為 pokearbitrage)
echo.
set /p repo="請貼上您的 GitHub 倉庫網址 (例如: https://github.com/username/pokearbitrage.git): "

git remote remove origin >nul 2>&1
git remote add origin %repo%
git branch -M main
git push -u origin main

echo.
echo ========================================================
echo  程式碼已成功推送至 GitHub！
echo.
echo  下一步：
echo  1. 前往 https://render.com 或 https://zeabur.com
echo  2. 點擊「New Web Service」選取您的 GitHub 專案
echo  3. 系統將自動完成部署並給您專屬的公開 HTTPS 網址！
echo ========================================================
pause
