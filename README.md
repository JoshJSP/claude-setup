# Claude Code setup van Josh

## Installeren (Windows 10/11)

Open **PowerShell** (Start > typ `powershell` > Enter) en plak deze regel:

```
git clone https://github.com/JoshJSP/claude-setup "$HOME\claude-setup"; & "$HOME\claude-setup\installeer.bat"
```

Log in met je GitHub-account als daarom gevraagd wordt (de repo is prive, Josh moet je eerst uitnodigen).
Het script installeert alles in een paar minuten en zegt aan het eind "Klaar, alles gelukt".
Daarna: open een NIEUW PowerShell-venster, typ `claude` en log in met je eigen Claude-account.

**"git wordt niet herkend"?** Dan staat Git nog niet op je laptop. Plak eerst dit, sluit PowerShell,
open hem opnieuw en plak dan de regel hierboven:

```
winget install --id Git.Git -e
```

Onderweg:
- Vraagt Windows om toestemming voor Git of Python: klik Ja.
- Het script vraagt of Claude nooit meer om toestemming mag vragen. Enter = nee (veiliger).
- Ging er iets mis? Het script zet aan het eind op een rij wat er fout ging en wat je moet doen.
  Meestal is het internet even weg: gewoon opnieuw starten, wat al gelukt is blijft staan.

## Bijwerken

Dubbelklik op `installeer.bat` in de map `claude-setup` (in je gebruikersmap).
Hij haalt zelf de nieuwste versie op (`git pull`) en installeert wat er nieuw is. Er komt niets dubbel.

## Wat je krijgt

| Wat | |
|---|---|
| 20 plugins | superpowers, frontend-design, context7, plugin-dev, explanatory-output-style, vercel, unity, ponytail, session-tax, claude-bionify, bedrock, frontend-mobile-development, ui-design, avoid-ai-writing, python-development, javascript-typescript, file-conversion, game-development, jvm-languages, web-quality-skills |
| 5 skills | apple-design, graphify, task-observer, transitions-dev, transitions-polish |
| `/hub` | Typ `/hub` in Claude Code: overzicht van alle plugins. `/hub web` opent een pagina waar je met 1 klik installeert |
| Klaar-melding | Na elke opdracht een Telegram-bericht met wat Claude gedaan heeft (zodra je de telefoonbrug hieronder hebt gekoppeld) |
| Telefoonbrug | `telefoon.bat`: bestuur Claude Code op je laptop vanaf je telefoon (zie onder) |
| PowerShell-tool | Claude kan PowerShell-commando's draaien in plaats van alleen Git Bash |
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
- Na het koppelen krijg je ook na elke gewone Claude-opdracht op de laptop een klaar-bericht.
- Gaat er iets fout (niet ingelogd, limiet bereikt, geen internet, fout token), dan stuurt de bot
  een bericht dat met "Fout:" begint en zegt wat je moet doen. Het staat ook in het venster op de laptop.

**Let op**
- De laptop moet aan staan (geen slaapstand) en het venster van `telefoon.bat` moet open blijven.
  Automatisch starten: Win+R, typ `shell:startup`, zet daar een snelkoppeling naar `telefoon.bat`.
- Claude mag via de bot ALLES zonder te vragen. Deel je bot-token met niemand; het staat in
  `~\.claude\telefoon.json`. Opnieuw koppelen: verwijder dat bestand.
- Wil je het hele scherm zien en zelf de muis bewegen? Gebruik dan Chrome Remote Desktop
  (gratis, remotedesktop.google.com). Dat staat los van Claude.

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

- Toch nooit meer toestemming vragen, of juist weer wel? Draai `installeer.bat` opnieuw, of zet in `~\.claude\settings.json` `permissions.defaultMode` op `bypassPermissions` (of haal het weg).
- Geen klaar-berichten meer? Verwijder het blok met `klaar-melden.py` onder `hooks` in `~\.claude\settings.json`.

- Veel plugins = meer tokens per sessie. Wil je er een uitzetten: `claude plugin disable <naam>`
- "explanatory-output-style" laat Claude uitleg (Insights) geven bij code. Te veel tekst? Zet die uit.
- "ponytail" dwingt de simpelste oplossing af. Uitzetten in een sessie: "stop ponytail".
- De Anthropic-skills (docx, pdf, pptx, xlsx) komen via je eigen claude.ai-account en zitten hier niet in.
