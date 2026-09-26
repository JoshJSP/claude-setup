"""Stuur een Telegram-bericht zodra Claude Code klaar is met een opdracht.

Hangt aan de Stop-hook. Claude Code geeft op stdin een JSON mee met o.a.
`transcript_path`; daar lezen we het laatste antwoord uit.

Gebruikt dezelfde bot als telefoon.py (token en chat uit telefoon.json). Nog niet
gekoppeld? Dan doet hij niets. Faalt hij, dan zwijgt hij en geeft hij 0 terug:
een melding die misgaat mag nooit een sessie ophouden.
"""
import json
import os
import sys
import urllib.parse
import urllib.request
from pathlib import Path

CONFIGMAP = Path(os.environ.get("CLAUDE_CONFIG_DIR") or Path.home() / ".claude")
MAX_TEKENS = 3500  # Telegram kapt boven 4096; ruim eronder blijven


def laatste_antwoord(transcript):
    """Pak de tekst van het laatste antwoord van de assistent uit het transcript."""
    laatste = ""
    for regel in Path(transcript).read_text("utf-8", errors="replace").splitlines():
        try:
            bericht = json.loads(regel).get("message") or {}
        except (json.JSONDecodeError, AttributeError):
            continue
        if bericht.get("role") != "assistant":
            continue
        inhoud = bericht.get("content")
        if isinstance(inhoud, str):
            stukken = [inhoud]
        elif isinstance(inhoud, list):
            stukken = [d.get("text", "") for d in inhoud if isinstance(d, dict) and d.get("type") == "text"]
        else:
            continue
        tekst = "\n".join(s for s in stukken if s).strip()
        if tekst:
            laatste = tekst
    return laatste


def main():
    # Via de telefoonbrug krijg je het antwoord al; anders komt alles dubbel binnen
    if os.environ.get("TELEFOON_BRUG"):
        return 0
    try:
        c = json.loads((CONFIGMAP / "telefoon.json").read_text())
        token, chat = c["token"], c["eigenaar"]
        payload = json.loads(sys.stdin.read() or "{}")
    except (OSError, ValueError, KeyError, TypeError):
        return 0

    tekst = ""
    if payload.get("transcript_path"):
        try:
            tekst = laatste_antwoord(payload["transcript_path"])
        except OSError:
            pass
    tekst = tekst.replace("**", "") or "(geen samenvatting uit het transcript te halen)"
    if len(tekst) > MAX_TEKENS:
        tekst = tekst[:MAX_TEKENS] + "\n\n[...ingekort]"

    data = urllib.parse.urlencode({
        "chat_id": chat,
        "text": f"Claude Code is klaar\n\n{tekst}",
        "disable_web_page_preview": "true",
    }).encode()
    try:
        urllib.request.urlopen(f"https://api.telegram.org/bot{token}/sendMessage", data, timeout=15).read()
    except Exception:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
