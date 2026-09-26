# Installeert Josh' Claude Code plugins + skills en zet de PowerShell-tool aan.
# Starten: dubbelklik op installeer.bat. Opnieuw starten = bijwerken (hij doet zelf git pull).
param([switch]$ZonderPull)

$ErrorActionPreference = 'Stop'
$mislukt = [Collections.Generic.List[string]]::new()   # alles wat fout ging, voor het overzicht aan het eind
# CLAUDE_CONFIG_DIR volgt Claude Code zelf; standaard is dat ~\.claude
$claudeMap = if ($env:CLAUDE_CONFIG_DIR) { $env:CLAUDE_CONFIG_DIR } else { Join-Path $HOME '.claude' }

# Onverwachte fout: zeg wat er misging in plaats van alleen rode tekst
trap {
    Write-Host "`nFOUT: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "Dit gebeurde bij regel $($_.InvocationInfo.ScriptLineNumber) van installeer.ps1." -ForegroundColor Red
    Write-Host "Controleer je internet en dubbelklik opnieuw op installeer.bat. Blijft het misgaan, stuur Josh een foto van dit venster." -ForegroundColor Yellow
    exit 1
}

function Ververs-Path {
    $env:Path = [Environment]::GetEnvironmentVariable('Path', 'Machine') + ';' +
                [Environment]::GetEnvironmentVariable('Path', 'User') + ';' +
                (Join-Path $HOME '.local\bin')
}

# Met git clone binnengehaald? Dan eerst de nieuwste versie ophalen.
if (-not $ZonderPull -and (Test-Path (Join-Path $PSScriptRoot '.git')) -and (Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Host "Nieuwste versie ophalen (git pull)..." -ForegroundColor Cyan
    $voor = git -C $PSScriptRoot rev-parse HEAD
    git -C $PSScriptRoot pull --ff-only
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Bijwerken lukte niet (geen internet, of je hebt zelf bestanden in deze map veranderd). Ik installeer de versie die er nu staat." -ForegroundColor Yellow
    } elseif ((git -C $PSScriptRoot rev-parse HEAD) -ne $voor) {
        # Dit script is misschien zelf veranderd: start de nieuwe versie
        & $PSCommandPath -ZonderPull
        exit $LASTEXITCODE
    }
}

# Git is nodig om plugins van GitHub te halen, Python voor graphify, de hub en de telefoonbrug. Beide gratis.
foreach ($app in @(@{cmd='git'; id='Git.Git'}, @{cmd='python'; id='Python.Python.3.12'})) {
    $gevonden = Get-Command $app.cmd -ErrorAction SilentlyContinue
    # 'python' kan de nep-snelkoppeling naar de Microsoft Store zijn
    if (-not $gevonden -or $gevonden.Source -like '*WindowsApps*') {
        Write-Host "$($app.cmd) installeren..." -ForegroundColor Cyan
        if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
            $mislukt.Add("$($app.cmd): winget ontbreekt. Installeer 'App Installer' uit de Microsoft Store, of $($app.cmd) zelf.")
            continue
        }
        winget install --id $app.id -e --source winget --accept-package-agreements --accept-source-agreements
        Ververs-Path
        if (-not (Get-Command $app.cmd -ErrorAction SilentlyContinue)) {
            $mislukt.Add("$($app.cmd) installeren lukte niet (winget code $LASTEXITCODE). Klik je 'Ja' bij de Windows-vraag? Anders: herstart de laptop en probeer opnieuw.")
        }
    }
}
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Host "FOUT: Git ontbreekt, en zonder Git kunnen de plugins niet van GitHub komen." -ForegroundColor Red
    $mislukt | ForEach-Object { Write-Host " - $_" -ForegroundColor Yellow }
    exit 1
}
# Sommige plugin-repo's hebben diepe mappen; zonder dit faalt de checkout boven 260 tekens
git config --global core.longpaths true

if (-not (Get-Command claude -ErrorAction SilentlyContinue)) {
    Write-Host "Claude Code installeren..." -ForegroundColor Cyan
    try { Invoke-RestMethod https://claude.ai/install.ps1 | Invoke-Expression }
    catch { Write-Host "Downloaden van Claude Code mislukte: $($_.Exception.Message)" -ForegroundColor Red }
    Ververs-Path
}
if (-not (Get-Command claude -ErrorAction SilentlyContinue)) {
    Write-Host "FOUT: Claude Code is niet gevonden na het installeren." -ForegroundColor Red
    Write-Host "Controleer je internet (claude.ai moet bereikbaar zijn), sluit dit venster en dubbelklik opnieuw op installeer.bat." -ForegroundColor Yellow
    exit 1
}

$marketplaces = @(
    'anthropics/claude-plugins-official',
    'DietrichGebert/ponytail',
    'wshobson/agents',
    'ccplugins/awesome-claude-code-plugins',
    'addyosmani/web-quality-skills'
)
$plugins = @(
    'superpowers@claude-plugins-official',
    'frontend-design@claude-plugins-official',
    'context7@claude-plugins-official',
    'plugin-dev@claude-plugins-official',
    'explanatory-output-style@claude-plugins-official',
    'vercel@claude-plugins-official',
    'unity@claude-plugins-official',
    'ponytail@ponytail',
    'session-tax@awesome-claude-code-plugins',
    'claude-bionify@awesome-claude-code-plugins',
    'bedrock@awesome-claude-code-plugins',
    'frontend-mobile-development@claude-code-workflows',
    'ui-design@claude-code-workflows',
    'avoid-ai-writing@claude-code-workflows',
    'python-development@claude-code-workflows',
    'javascript-typescript@claude-code-workflows',
    'file-conversion@claude-code-workflows',
    'game-development@claude-code-workflows',
    'jvm-languages@claude-code-workflows',
    'web-quality-skills@addy-web-quality-skills'
)

$ErrorActionPreference = 'Continue'   # een mislukte plugin mag de rest niet stoppen
foreach ($m in $marketplaces) {
    Write-Host "Marketplace: $m" -ForegroundColor Cyan
    # Volledige https-link: met alleen owner/repo kloont Claude via SSH, en dat faalt
    # op een laptop die nog nooit via SSH met GitHub praatte ("Host key verification failed")
    $uit = claude plugin marketplace add "https://github.com/$m.git" 2>&1 | ForEach-Object { "$_" } | Out-String
    Write-Host $uit.Trim()
    # 'already' = stond er al, dat is geen fout
    if ($LASTEXITCODE -ne 0 -and $uit -notmatch 'already') { $mislukt.Add("Marketplace $m : $($uit.Trim())") }
}
foreach ($p in $plugins) {
    Write-Host "Plugin: $p" -ForegroundColor Cyan
    $uit = claude plugin install $p 2>&1 | ForEach-Object { "$_" } | Out-String
    Write-Host $uit.Trim()
    if ($LASTEXITCODE -ne 0 -and $uit -notmatch 'already') { $mislukt.Add("Plugin $p : $($uit.Trim())") }
}
$ErrorActionPreference = 'Stop'

# Losse skills, het /hub-commando en de klaar-melding kopieren (zelfde naam = overschrijven, niet dubbel)
foreach ($map in 'skills', 'commands', 'hub', 'hooks') {
    $doel = Join-Path $claudeMap $map
    New-Item -ItemType Directory -Force $doel | Out-Null
    Copy-Item -Recurse -Force (Join-Path $PSScriptRoot "$map\*") $doel
}
Write-Host "Skills, /hub en klaar-melding gekopieerd naar $claudeMap" -ForegroundColor Green

# settings.json bijwerken (rest van je instellingen blijft staan)
$settingsPad = Join-Path $claudeMap 'settings.json'
try {
    $s = if (Test-Path $settingsPad) { Get-Content $settingsPad -Raw | ConvertFrom-Json } else { $null }
} catch {
    Write-Host "FOUT: $settingsPad is geen geldige JSON, daarom blijft hij ongemoeid." -ForegroundColor Red
    Write-Host "Open hem in Kladblok, herstel of verwijder hem, en dubbelklik opnieuw op installeer.bat." -ForegroundColor Yellow
    exit 1
}
if (-not $s) { $s = [pscustomobject]@{} }   # bestand bestaat niet of is leeg

# PowerShell-tool aan
if (-not $s.env) { $s | Add-Member -Force env ([pscustomobject]@{}) }
$s.env | Add-Member -Force CLAUDE_CODE_USE_POWERSHELL_TOOL '1'

# Klaar-melding als Stop-hook, alleen als hij er nog niet in staat
$hookCmd = 'python "' + ((Join-Path $claudeMap 'hooks\klaar-melden.py') -replace '\\', '/') + '"'
if (-not $s.hooks) { $s | Add-Member -Force hooks ([pscustomobject]@{}) }
$stop = @($s.hooks.Stop | Where-Object { $_ })
if (-not ($stop | ConvertTo-Json -Depth 10 | Select-String -SimpleMatch 'klaar-melden.py')) {
    $stop += [pscustomobject]@{ hooks = @([pscustomobject]@{ type = 'command'; command = $hookCmd; timeout = 20 }) }
    $s.hooks | Add-Member -Force Stop $stop
}

# Nooit meer om toestemming vragen: alleen als je dat zelf kiest
if ($s.permissions.defaultMode -ne 'bypassPermissions') {
    Write-Host "`nWil je dat Claude NOOIT meer om toestemming vraagt (bestanden, commando's)?" -ForegroundColor Cyan
    Write-Host "Scheelt veel klikken, maar Claude kan dan ook zonder vragen iets verwijderen. Later terugzetten kan." -ForegroundColor Cyan
    Write-Host "Typ j voor ja, of druk Enter voor nee: " -NoNewline
    if ([Console]::ReadLine() -match '^\s*j') {
        if (-not $s.permissions) { $s | Add-Member -Force permissions ([pscustomobject]@{}) }
        $s.permissions | Add-Member -Force defaultMode 'bypassPermissions'
        $s | Add-Member -Force skipDangerousModePermissionPrompt $true
        Write-Host "Aangezet." -ForegroundColor Green
    } else { Write-Host "Niet aangezet." }
}

# UTF-8 zonder BOM, anders leest Claude Code het bestand niet
New-Item -ItemType Directory -Force $claudeMap | Out-Null
[IO.File]::WriteAllText($settingsPad, ($s | ConvertTo-Json -Depth 20), (New-Object Text.UTF8Encoding $false))
Write-Host "Instellingen bijgewerkt in $settingsPad" -ForegroundColor Green

if ($mislukt.Count) {
    Write-Host "`nKlaar, maar $($mislukt.Count) ding(en) gingen fout:" -ForegroundColor Yellow
    $mislukt | ForEach-Object { Write-Host " - $_" -ForegroundColor Yellow }
    Write-Host "Meestal is het internet of GitHub even weg: dubbelklik opnieuw op installeer.bat, wat al gelukt is blijft staan." -ForegroundColor Yellow
    exit 1
}
Write-Host "`nKlaar, alles gelukt. Open een NIEUW PowerShell-venster, typ 'claude' en log in met je eigen Claude-account." -ForegroundColor Green
