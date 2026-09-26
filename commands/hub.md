---
description: Plugin-hub - overzicht van alle beschikbare plugins/repos en wat je al hebt
argument-hint: "[web|mine|all|cat|search <woord>|find <woord>|add owner/repo]"
allowed-tools: Bash(python:*)
---

Draai de plugin-hub en toon de uitvoer.

Zonder argument: overzicht. `web` opent de visuele pagina in de browser (installeren met 1 klik,
en zoeken op GitHub naar nieuwe repos). `mine` = wat je al hebt. `search <woord>` zoekt in je
eigen catalogus, `find <woord>` zoekt nieuwe marketplace-repos op GitHub.

!`python "$HOME/.claude/hub/hub.py" $ARGUMENTS`

Bij `web`: het commando blijft draaien tot Ctrl+C - start hem op de achtergrond en geef de gebruiker de
URL. Bij de andere modi: vat kort samen (in het Nederlands) wat er te zien is. Wil de gebruiker iets
installeren, gebruik dan `claude plugin install <naam>@<marketplace>`.
