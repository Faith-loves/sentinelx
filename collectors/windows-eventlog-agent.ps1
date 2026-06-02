param(
  [string]$ApiUrl = "http://localhost:8000",
  [string]$ApiKey = $env:SENTINELX_API_KEY,
  [int]$MinutesBack = 5
)

$since = (Get-Date).AddMinutes(-$MinutesBack)
$events = Get-WinEvent -FilterHashtable @{
  LogName = "Security"
  StartTime = $since
  Id = 4624, 4625, 4670, 4720, 4732
} -ErrorAction SilentlyContinue | Select-Object -First 250

$payload = foreach ($event in $events) {
  @{
    event_id = $event.Id
    timestamp = $event.TimeCreated.ToUniversalTime().ToString("o")
    computer = $event.MachineName
    message = $event.Message
    host = $env:COMPUTERNAME
  }
}

if ($payload.Count -gt 0) {
  Invoke-RestMethod "$ApiUrl/api/logs/collectors/windows/bulk" `
    -Method Post `
    -Headers @{ "X-API-Key" = $ApiKey } `
    -ContentType "application/json" `
    -Body ($payload | ConvertTo-Json -Depth 6)
}
