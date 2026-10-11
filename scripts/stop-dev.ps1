param([string]$RuntimeDirectory = (Join-Path $env:LOCALAPPDATA 'ClinicSystem\runtime'))
$ErrorActionPreference = 'Stop'
$stateFile = Join-Path $RuntimeDirectory 'dev-processes.json'
if (-not (Test-Path -LiteralPath $stateFile)) { Write-Output 'No recorded development processes.'; return }
function Stop-DevelopmentTree([int]$ProcessId) {
  foreach ($child in (Get-CimInstance Win32_Process -Filter "ParentProcessId = $ProcessId")) {
    Stop-DevelopmentTree -ProcessId $child.ProcessId
  }
  Stop-Process -Id $ProcessId -ErrorAction SilentlyContinue
}
foreach ($record in (Get-Content -LiteralPath $stateFile -Raw | ConvertFrom-Json)) {
  $process = Get-Process -Id $record.Id -ErrorAction SilentlyContinue
  $expectedStart = ([datetime]$record.Started).ToUniversalTime()
  if ($process -and $process.StartTime.ToUniversalTime().Ticks -eq $expectedStart.Ticks) {
    Stop-DevelopmentTree -ProcessId $record.Id
  }
}
Write-Output 'Recorded API and web processes stopped. PostgreSQL data is preserved.'
