"""Bestuur Claude Code op je laptop via Telegram.

Starten: dubbelklik op telefoon.bat. Eerste keer vraagt hij je bot-token en een koppelcode.
Alleen stdlib, dus elke Python 3 werkt.
Test zonder Telegram:  python telefoon.py --test "zeg ok"
"""
import json
import os
import random
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

CONFIG = Path(os.environ.get("CLAUDE_CONFIG_DIR") or Path.home() / ".claude") / "telefoon.json"
WERKMAP = Path.home()
MAX_TIJD = 20 * 60  # seconden per opdracht
OPNIEUW_KOPPELEN = f"Verwijder {CONFIG} en start telefoon.bat opnieuw om een nieuw token in te voeren."


class Stop(Exception):
    """Fout waar opnieuw proberen niet helpt; de uitleg staat in de tekst."""


def uitleg(fout):
    """Maak van een fout een zin die zegt wat er mis is en wat je moet doen."""
    if isinstance(fout, urllib.error.HTTPError):
        if fout.code in (401, 404):
            return f"Telegram kent dit bot-token niet (fout {fout.code}). Klopt het token, of is de bot verwijderd?\n{OPNIEUW_KOPPELEN}"
        if fout.code == 409:
            return "telefoon.bat draait al in een ander venster (fout 409). Sluit dat venster, er mag er maar een tegelijk draaien."
        if fout.code == 429:
            return "Telegram zegt: te veel berichten tegelijk (fout 429). Wacht een minuut."
        return f"Telegram gaf fout {fout.code}: {fout.reason}"
    if isinstance(fout, (urllib.error.URLError, TimeoutError, ConnectionError)):
        return "Geen verbinding met Telegram. Is de wifi weg, of blokkeert dit netwerk Telegram?"
    if isinstance(fout, Stop):
        return str(fout)
    return f"Onverwachte fout: {type(fout).__name__}: {fout}"


def api(token, methode, **velden):
    req = urllib.request.Request(
        f"https://api.telegram.org/bot{token}/{methode}",
        data=json.dumps(velden).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=70) as r:
        return json.load(r)["result"]


def stukken(tekst, max_len=4000):
    """Telegram weigert berichten boven 4096 tekens."""
    # ** van markdown/bionify toont Telegram letterlijk als sterretjes
    tekst = tekst.replace("**", "").strip() or "(leeg antwoord)"
    return [tekst[i:i + max_len] for i in range(0, len(tekst), max_len)]


def claude_fout(uitvoer):
    """Herken de bekende oorzaken in wat Claude Code zelf meldt."""
    laag = uitvoer.lower()
    if any(w in laag for w in ("log in", "login", "not logged", "unauthorized", "authenticat", "oauth")):
        return "Claude Code is niet ingelogd. Open PowerShell op de laptop, typ claude en log in."
    if "rate limit" in laag or "usage limit" in laag or "limit reached" in laag:
        return "Je Claude-limiet is bereikt. Wacht tot die weer vrij is (Claude Code zegt hoe lang)."
    if "policy" in laag or "organization" in laag:
        return "Dit mag niet van de beheerder van je (school)account."
    if "no conversation found" in laag:
        return "Er is geen vorig gesprek om op door te gaan. Stuur je opdracht nog een keer."
    return None


def vraag_claude(opdracht, doorgaan):
    claude = shutil.which("claude")
    if not claude:
        return "Fout: Claude Code is niet gevonden op deze laptop. Dubbelklik opnieuw op installeer.bat."
    cmd = [claude, "-p", opdracht, "--permission-mode", "bypassPermissions"]
    if doorgaan:
        cmd.append("--continue")  # zelfde gesprek als het vorige bericht
    try:
        # TELEFOON_BRUG: de klaar-melding stuurt dit antwoord dan niet nog een keer
        r = subprocess.run(cmd, cwd=WERKMAP, capture_output=True, text=True, env={**os.environ, "TELEFOON_BRUG": "1"},
                           encoding="utf-8", errors="replace", timeout=MAX_TIJD)
    except subprocess.TimeoutExpired:
        return f"Fout: gestopt na {MAX_TIJD // 60} minuten, de opdracht duurde te lang. Knip hem op in kleinere stukken."
    if r.returncode == 0:
        return r.stdout
    melding = (r.stderr or r.stdout).strip() or "(Claude Code gaf geen uitleg)"
    oorzaak = claude_fout(melding)
    kop = f"Fout: {oorzaak}" if oorzaak else f"Fout: Claude Code stopte met code {r.returncode}."
    return f"{kop}\n\nWat Claude Code zei:\n{melding[-1500:]}"


def lees_config():
    try:
        c = json.loads(CONFIG.read_text())
        return c["token"], int(c["eigenaar"])
    except (ValueError, KeyError, TypeError):
        raise Stop(f"{CONFIG} is kapot of onvolledig.\n{OPNIEUW_KOPPELEN}")


def instellen():
    print("Eerste keer instellen.")
    print("1. Open Telegram, zoek @BotFather, stuur /newbot en volg de stappen.")
    while True:
        token = input("2. Plak hier het token dat BotFather je geeft: ").strip()
        if ":" not in token:
            print("   Dat lijkt geen token. Het ziet eruit als 123456789:ABCdef... Probeer opnieuw.")
            continue
        try:
            api(token, "getMe")
            break
        except Exception as e:
            if isinstance(e, urllib.error.HTTPError) and e.code in (401, 404):
                print("   Telegram kent dit token niet. Kopieer het nog eens uit BotFather (helemaal, zonder spaties).")
            else:
                print(f"   {uitleg(e)}")
    code = str(random.randint(100000, 999999))
    print(f"3. Stuur je nieuwe bot dit bericht in Telegram:  {code}")
    offset = 0
    while True:
        try:
            updates = api(token, "getUpdates", offset=offset, timeout=50)
        except Exception as e:
            print(f"   {uitleg(e)} Ik probeer het over 10 seconden opnieuw.")
            time.sleep(10)
            continue
        for u in updates:
            offset = u["update_id"] + 1
            bericht = u.get("message") or {}
            tekst = bericht.get("text", "").strip()
            if tekst == code:
                eigenaar = bericht["chat"]["id"]
                CONFIG.parent.mkdir(parents=True, exist_ok=True)
                CONFIG.write_text(json.dumps({"token": token, "eigenaar": eigenaar}))
                api(token, "sendMessage", chat_id=eigenaar, text="Gekoppeld. Stuur maar een opdracht.")
                print("   Gekoppeld.")
                return token, eigenaar, offset
            if tekst:
                print(f"   Bericht ontvangen, maar dat is niet de code {code}. Stuur precies die 6 cijfers.")


def behandel(token, eigenaar, tekst, doorgaan):
    """Voer een bericht uit. Geeft terug of het volgende bericht het gesprek voortzet."""
    if tekst in ("/nieuw", "/start"):
        api(token, "sendMessage", chat_id=eigenaar, text="Nieuw gesprek.")
        return False
    print(f"> {tekst}")
    api(token, "sendChatAction", chat_id=eigenaar, action="typing")
    antwoord = vraag_claude(tekst, doorgaan)
    if antwoord.startswith("Fout:"):
        print(antwoord)
    for stuk in stukken(antwoord):
        api(token, "sendMessage", chat_id=eigenaar, text=stuk)
    return True


def main():
    token, eigenaar, offset = lees_config() if CONFIG.exists() else instellen()
    print("Luistert naar Telegram. Laat dit venster open. Ctrl+C om te stoppen.")
    doorgaan = False
    offline = False
    while True:
        try:
            updates = api(token, "getUpdates", offset=offset, timeout=50)
        except urllib.error.HTTPError as e:
            if e.code in (401, 404, 409):
                raise Stop(uitleg(e))
            print(uitleg(e))
            time.sleep(10)
            continue
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            if not offline:  # een keer melden, niet elke 5 seconden
                print(f"{uitleg(e)} Ik blijf het proberen.")
                offline = True
            time.sleep(5)
            continue
        if offline:
            print("Verbinding is terug.")
            offline = False
        for u in updates:
            offset = u["update_id"] + 1
            bericht = u.get("message") or {}
            tekst = bericht.get("text", "").strip()
            # Alleen de eigenaar: deze bot voert commando's uit op je laptop
            if bericht.get("chat", {}).get("id") != eigenaar:
                continue
            if not tekst:
                api(token, "sendMessage", chat_id=eigenaar, text="Ik snap alleen tekstberichten, geen foto's of spraak.")
                continue
            try:
                doorgaan = behandel(token, eigenaar, tekst, doorgaan)
            except Exception as e:
                melding = f"Fout: {uitleg(e)}"
                print(melding)
                try:  # lukt dit ook niet, dan staat het in elk geval in het venster
                    api(token, "sendMessage", chat_id=eigenaar, text=melding)
                except Exception:
                    pass


if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "--test":
        assert stukken("") == ["(leeg antwoord)"]
        assert stukken("**Jo**sh") == ["Josh"]
        assert [len(s) for s in stukken("x" * 9000)] == [4000, 4000, 1000]
        assert "niet ingelogd" in claude_fout("Invalid API key · Please run /login")
        assert claude_fout("iets heel anders") is None
        fout = urllib.error.HTTPError("u", 409, "Conflict", None, None)
        assert "ander venster" in uitleg(fout)
        assert "verbinding" in uitleg(urllib.error.URLError("x")).lower()
        print(vraag_claude(sys.argv[2], doorgaan=False))
    else:
        try:
            main()
        except KeyboardInterrupt:
            print("Gestopt.")
        except Exception as e:
            print(f"\nFOUT: {uitleg(e)}")
            sys.exit(1)
