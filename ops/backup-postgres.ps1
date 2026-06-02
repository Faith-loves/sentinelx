param(
  [string]$Container = "sentinelx-postgres-1",
  [string]$Database = "sentinelx",
  [string]$User = "sentinel",
  [string]$OutputDir = ".\backups"
)

$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null
$output = Join-Path $OutputDir "$Database-$timestamp.sql"

docker exec $Container pg_dump -U $User $Database | Out-File -Encoding utf8 $output
Write-Host "Backup written to $output"
