@echo off
chcp 65001 >nul
title CINEFORGE AI - Autonomous Video Editor
echo ======================================================================
echo    🎬 CINEFORGE AI - AUTONOMOUS AI VIDEO EDITING WORKSTATION
echo    ⚡ Powered by Gemini B1 Web2API Proxy (Zero-Cost, No API Keys)
echo ======================================================================
echo.
echo [1/2] Checking Gemini B1 Web2API Proxy on port 8081...
powershell -Command "$s = Get-NetTCPConnection -State Listen -LocalPort 8081 -ErrorAction SilentlyContinue; if (-not $s) { Start-Process -WindowStyle Minimized python -ArgumentList 'gemini-web2api.py --port 8081' -WorkingDirectory 'gemini-web2api'; Write-Host '  -> Spawned Gemini B1 Proxy on http://127.0.0.1:8081' } else { Write-Host '  -> Gemini B1 Proxy is already active on port 8081' }"

echo.
echo [2/2] Starting CineForge AI Studio server at http://127.0.0.1:8080 ...
timeout /t 2 /nobreak >nul
start "" "http://127.0.0.1:8080"
python app.py
pause
