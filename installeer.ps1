# Installeert Josh' Claude Code plugins + skills en zet de PowerShell-tool aan.
# Starten: dubbelklik op installeer.bat

$ErrorActionPreference = 'Stop'
$mislukt = [Collections.Generic.List[string]]::new()   # alles wat fout ging, voor het overzicht aan het eind

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

# Git is nodig om plugins van GitHub te halen, Python voor graphify en Python-werk. Beide gratis.
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
    $uit = claude plugin marketplace add $m 2>&1 | Out-String
    Write-Host $uit.Trim()
    # 'already' = stond er al, dat is geen fout
    if ($LASTEXITCODE -ne 0 -and $uit -notmatch 'already') { $mislukt.Add("Marketplace $m : $($uit.Trim())") }
}
foreach ($p in $plugins) {
    Write-Host "Plugin: $p" -ForegroundColor Cyan
    $uit = claude plugin install $p 2>&1 | Out-String
    Write-Host $uit.Trim()
    if ($LASTEXITCODE -ne 0 -and $uit -notmatch 'already') { $mislukt.Add("Plugin $p : $($uit.Trim())") }
}
$ErrorActionPreference = 'Stop'

# Losse skills kopieren (bestaande met dezelfde naam worden overschreven)
$skillsDoel = Join-Path $HOME '.claude\skills'
New-Item -ItemType Directory -Force $skillsDoel | Out-Null
Copy-Item -Recurse -Force (Join-Path $PSScriptRoot 'skills\*') $skillsDoel
Write-Host "Skills gekopieerd naar $skillsDoel" -ForegroundColor Green

# PowerShell-tool aanzetten in settings.json (rest van je instellingen blijft staan)
$settingsPad = Join-Path $HOME '.claude\settings.json'
try {
    $s = if (Test-Path $settingsPad) { Get-Content $settingsPad -Raw | ConvertFrom-Json } else { $null }
} catch {
    Write-Host "FOUT: $settingsPad is geen geldige JSON, daarom blijft hij ongemoeid." -ForegroundColor Red
    Write-Host "Open hem in Kladblok, herstel of verwijder hem, en dubbelklik opnieuw op installeer.bat." -ForegroundColor Yellow
    exit 1
}
if (-not $s) { $s = [pscustomobject]@{} }   # bestand bestaat niet of is leeg
if (-not $s.env) { $s | Add-Member -Force env ([pscustomobject]@{}) }
$s.env | Add-Member -Force CLAUDE_CODE_USE_POWERSHELL_TOOL '1'
# UTF-8 zonder BOM, anders leest Claude Code het bestand niet
[IO.File]::WriteAllText($settingsPad, ($s | ConvertTo-Json -Depth 20), (New-Object Text.UTF8Encoding $false))
Write-Host "PowerShell-tool aangezet in $settingsPad" -ForegroundColor Green

if ($mislukt.Count) {
    Write-Host "`nKlaar, maar $($mislukt.Count) ding(en) gingen fout:" -ForegroundColor Yellow
    $mislukt | ForEach-Object { Write-Host " - $_" -ForegroundColor Yellow }
    Write-Host "Meestal is het internet of GitHub even weg: dubbelklik opnieuw op installeer.bat, wat al gelukt is blijft staan." -ForegroundColor Yellow
    exit 1
}
Write-Host "`nKlaar, alles gelukt. Open een NIEUW PowerShell-venster, typ 'claude' en log in met je eigen Claude-account." -ForegroundColor Green
