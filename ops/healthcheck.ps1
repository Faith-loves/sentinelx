param(
  [string]$BackendUrl = "http://localhost:8000"
)

$health = Invoke-RestMethod "$BackendUrl/health"
$ready = Invoke-RestMethod "$BackendUrl/ready"

[pscustomobject]@{
  Health = $health.status
  Ready = $ready.status
  Search = $ready.search.engine
  Database = $ready.database.dialect
}
