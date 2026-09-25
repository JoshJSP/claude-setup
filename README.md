# Claude Code setup van Josh

## Wat erin zit

| Bestand | Wat het doet |
|---|---|
| `installeer.bat` | Hierop dubbelklikken, dat start `installeer.ps1` |
| `installeer.ps1` | Installeert wat mist (Git, Python, Claude Code), dan 20 plugins, kopieert de losse skills en zet de PowerShell-tool aan |
| `telefoon.bat` / `telefoon.py` | Bestuur Claude Code op je laptop vanaf je telefoon via Telegram (zie onder) |
| `skills\` | apple-design, graphify, task-observer, transitions-dev, transitions-polish |

## Installeren (Windows 10/11, werkt ook op een lege laptop)

1. Download deze repo: groene knop **Code** > **Download ZIP**.
   Pak de zip uit (rechtsklik > "Alles uitpakken"). Niet vanuit de zip starten.
2. Dubbelklik op `installeer.bat`.
   - Zegt Windows "Windows heeft uw pc beschermd": klik "Meer informatie" > "Toch uitvoeren".
   - Vraagt Windows om toestemming voor Git of Python: klik Ja.
   - Duurt een paar minuten. Wacht tot er "Klaar" staat.
3. Open een NIEUW PowerShell-venster, typ `claude` en log in met je eigen Claude-account.
4. Met `/plugin` zie je wat er geïnstalleerd is.

Ging er iets mis? Het script zet aan het eind op een rij wat er fout ging en wat je moet doen.
Meestal is het internet even weg: gewoon opnieuw dubbelklikken, wat al gelukt is blijft staan.

## Bijwerken

Als Josh iets verandert: download de zip opnieuw en dubbelklik weer op `installeer.bat`.
Of, als je de repo met Git hebt binnengehaald (`git clone`), in die map:

```
git pull
.\installeer.bat
```

## Laptop besturen vanaf je telefoon (via Telegram)

Remote Control van Claude staat op het schoolaccount uit, daarom gaat dit via Telegram.
Je stuurt de bot een bericht, Claude Code voert het uit op je laptop en stuurt het antwoord terug.

**Eerste keer**
1. Zet Telegram op je telefoon. Zoek **@BotFather**, stuur `/newbot` en kies een naam.
   BotFather geeft je een token (lange code met een dubbele punt erin).
2. Dubbelklik op `telefoon.bat` en plak het token.
3. Het venster toont een koppelcode van 6 cijfers. Stuur die code naar JOUW nieuwe bot.
   Nu luistert de bot alleen nog naar jou.

**Daarna**: dubbelklik `telefoon.bat` en stuur je bot opdrachten, bijv. "zet mijn Downloads op volgorde".
- `/nieuw` begint een nieuw gesprek (anders onthoudt Claude het vorige bericht).
- Een opdracht duurt al snel 15+ seconden, grote klussen minuten. Je krijgt pas antwoord als het af is.
- Gaat er iets fout (niet ingelogd, limiet bereikt, geen internet, fout token), dan stuurt de bot
  een bericht dat met "Fout:" begint en zegt wat je moet doen. Het staat ook in het venster op de laptop.

**Let op**
- De laptop moet aan staan (geen slaapstand) en het venster van `telefoon.bat` moet open blijven.
  Automatisch starten: Win+R, typ `shell:startup`, zet daar een snelkoppeling naar `telefoon.bat`.
- Claude mag via de bot ALLES zonder te vragen. Deel je bot-token met niemand; het staat in
  `~\.claude\telefoon.json`. Opnieuw koppelen: verwijder dat bestand.
- Wil je het hele scherm zien en zelf de muis bewegen? Gebruik dan Chrome Remote Desktop
  (gratis, remotedesktop.google.com). Dat staat los van Claude.

## PowerShell

Het script zet `CLAUDE_CODE_USE_POWERSHELL_TOOL=1` in `~\.claude\settings.json`.
Claude kan dan PowerShell-commando's draaien in plaats van alleen Git Bash.

## Kosten

Alle plugins en skills zijn gratis en open source. Claude Code zelf heeft wel een
Claude-abonnement (Pro of hoger) of API-tegoed nodig. De vercel-plugin werkt pas met
een Vercel-account; het gratis Hobby-account is genoeg.

## Extra's die je zelf aanzet (gratis, via je eigen account)

- claude.ai > Instellingen > Connectors: o.a. Adobe, Consensus, Fibery.
  Wat je daar koppelt verschijnt vanzelf in Claude Code.
  Microsoft 365, Gmail en Google Calendar kunnen met het schoolaccount niet inloggen in Claude Code.
- 21st.dev (UI-componenten): maak een account op 21st.dev en voeg de MCP-server toe
  met je eigen sleutel volgens hun instructies.

## Handig om te weten

- Veel plugins = meer tokens per sessie. Wil je er een uitzetten: `claude plugin disable <naam>`
- "explanatory-output-style" laat Claude uitleg (Insights) geven bij code. Te veel tekst? Zet die uit.
- "ponytail" dwingt de simpelste oplossing af. Uitzetten in een sessie: "stop ponytail".
- De Anthropic-skills (docx, pdf, pptx, xlsx) komen via je eigen claude.ai-account en zitten hier niet in.
