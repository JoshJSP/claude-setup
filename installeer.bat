@echo off
rem Alles tussen haakjes: cmd leest het blok in een keer, dus git pull mag dit bestand tijdens het draaien vervangen
(
  cd /d "%~dp0"
  powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0installeer.ps1"
  pause
  exit /b
)
