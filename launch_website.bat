@echo off
title Trading Platform Launcher
echo =========================================
echo    Starting Trading Platform Website
echo =========================================

echo Opening http://localhost:8000 in your browser...
start http://localhost:8000

echo Starting local web server on port 8000...
echo.
echo Keep this window open to keep the server running.
echo Close this window or press Ctrl+C to stop the server.
echo =========================================
cd frontend
python -m http.server 8000
