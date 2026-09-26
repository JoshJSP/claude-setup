@echo off
rem Altijd vanuit deze map, ook als je hem vanuit PowerShell of een andere map start
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0installeer.ps1"
pause
