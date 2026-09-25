@echo off
rem Bestuur Claude Code vanaf je telefoon via Telegram. Laat dit venster open.
where python >nul 2>nul || (
  echo FOUT: Python is niet gevonden. Dubbelklik eerst op installeer.bat en open daarna dit bestand opnieuw.
  pause
  exit /b 1
)
python "%~dp0telefoon.py"
pause
