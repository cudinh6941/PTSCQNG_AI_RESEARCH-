@echo off
title PAIP — Petrovietnam AI Platform
echo ========================================================
echo   PAIP — Petrovietnam AI Platform (R&D Lab)
echo   Agent 0: Tro Ly Ra Soat & Xuat File Word Thong Minh
echo ========================================================
echo Dang khoi dong Web Server tai http://localhost:8000 ...
echo.

cd /d "%~dp0"
call .venv\Scripts\activate.bat
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
pause
