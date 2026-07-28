# auto_improve_cron.ps1 — exécuté par la tâche planifiée hebdo (item ③ V2).
# Lance la passe d'auto-amélioration en mode mesure + log (V1 : ne commit rien).
# Utilise `python` (le `python3` de la machine est un stub cassé).
$ErrorActionPreference = "Stop"
$skillRoot = Split-Path -Parent $PSScriptRoot   # .../meta/skills/mode-plan
Set-Location $skillRoot
$date = Get-Date -Format "yyyy-MM-dd"
$log  = Join-Path $skillRoot "_mode-plan-meta\cron.log"

"[$((Get-Date).ToString('s'))] demarrage passe auto_improve --log ($date)" | Out-File -Append -Encoding utf8 $log

# auto_improve.py ecrit ses lignes d'information sur stderr (decision=NO_COMMIT, alerte
# progressive disclosure...). Avec ErrorActionPreference=Stop, le `2>&1` transformait
# CHAQUE ligne de stderr en erreur terminante : la tache aurait signale un echec toutes
# les semaines, y compris quand la passe se deroule normalement (une passe a sec qui ne
# commit rien N'EST PAS un echec - c'est ecrit dans auto_improve.py:302).
# Une alerte qui sonne toujours est une alerte qu'on ignore.
# Le verdict, c'est le code de sortie du script, pas la presence de stderr.
$ErrorActionPreference = "Continue"
python scripts/auto_improve.py --log --date $date 2>&1 | Out-File -Append -Encoding utf8 $log
$code = $LASTEXITCODE
"[$((Get-Date).ToString('s'))] passe terminee (exit $code)" | Out-File -Append -Encoding utf8 $log
exit $code
