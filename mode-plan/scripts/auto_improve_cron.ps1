# auto_improve_cron.ps1 — exécuté par la tâche planifiée hebdo (item ③ V2).
# Lance la passe d'auto-amélioration en mode mesure + log (V1 : ne commit rien).
# Utilise `python` (le `python3` de la machine est un stub cassé).
$ErrorActionPreference = "Stop"
$skillRoot = Split-Path -Parent $PSScriptRoot   # .../meta/skills/mode-plan
Set-Location $skillRoot
$date = Get-Date -Format "yyyy-MM-dd"
$log  = Join-Path $skillRoot "_mode-plan-meta\cron.log"

"[$((Get-Date).ToString('s'))] démarrage passe auto_improve --log ($date)" | Out-File -Append -Encoding utf8 $log
try {
    python scripts/auto_improve.py --log --date $date 2>&1 | Out-File -Append -Encoding utf8 $log
    "[$((Get-Date).ToString('s'))] passe terminée (exit $LASTEXITCODE)" | Out-File -Append -Encoding utf8 $log
} catch {
    "[$((Get-Date).ToString('s'))] ERREUR : $_" | Out-File -Append -Encoding utf8 $log
    exit 1
}
