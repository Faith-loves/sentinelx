param(
  [string]$ApiUrl = "http://localhost:8000",
  [string]$ApiKey = $env:SENTINELX_API_KEY,
  [string]$InputPath = ".\network-events.json"
)

$events = Get-Content -Raw $InputPath | ConvertFrom-Json
Invoke-RestMethod "$ApiUrl/api/logs/collectors/network/bulk" `
  -Method Post `
  -Headers @{ "X-API-Key" = $ApiKey } `
  -ContentType "application/json" `
  -Body ($events | ConvertTo-Json -Depth 8)
