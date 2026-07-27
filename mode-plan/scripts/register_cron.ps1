# register_cron.ps1 — installe (ou retire) la tâche planifiée hebdo mode-plan auto-improve.
# Trigger TEMPOREL (dimanche 03:00) + StartWhenAvailable => survit à la veille Windows
# (le pattern éprouvé de Sébastien). Tâche au niveau UTILISATEUR (pas d'admin requis).
# Rien n'est enregistré tant qu'on ne lance pas ce script.
#
# Installer :  powershell -ExecutionPolicy Bypass -File scripts\register_cron.ps1
# Retirer   :  powershell -ExecutionPolicy Bypass -File scripts\register_cron.ps1 -Remove
param([switch]$Remove)

$ErrorActionPreference = "Stop"
$taskName = "mode-plan-auto-improve"
$wrapper  = Join-Path $PSScriptRoot "auto_improve_cron.ps1"

if ($Remove) {
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction SilentlyContinue
    Write-Host "Tâche '$taskName' retirée (si elle existait)."
    return
}

if (-not (Test-Path $wrapper)) { throw "Wrapper introuvable : $wrapper" }

$action   = New-ScheduledTaskAction -Execute "powershell.exe" `
              -Argument "-NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File `"$wrapper`""
$trigger  = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Sunday -At 3am
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable `
              -ExecutionTimeLimit (New-TimeSpan -Minutes 30) -MultipleInstances IgnoreNew

Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Settings $settings `
    -Description "mode-plan : passe hebdo d'auto-amélioration (mesure + log, ne commit rien en V1)" -Force | Out-Null

Write-Host "Tâche '$taskName' installée : dimanche 03:00, survit à la veille (StartWhenAvailable)."
Write-Host "Vérifier : Get-ScheduledTask -TaskName $taskName ; log dans _mode-plan-meta\cron.log"
