@echo off
(
  cd /d "%~dp0"
  powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0installeer.ps1"
  pause
  exit /b
)
