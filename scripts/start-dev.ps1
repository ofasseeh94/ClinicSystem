param([string]$BuildDirectory = (Join-Path $env:LOCALAPPDATA 'ClinicSystem\build'),
      [string]$RuntimeDirectory = (Join-Path $env:LOCALAPPDATA 'ClinicSystem\runtime'))
$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path $PSScriptRoot -Parent
$envFile = Join-Path $repoRoot '.env'
if (Test-Path -LiteralPath $envFile) {
  foreach ($line in Get-Content -LiteralPath $envFile) {
    if ($line -match '^([A-Z][A-Z0-9_]*)=(.*)$') { Set-Item -Path ('Env:' + $Matches[1]) -Value $Matches[2] }
  }
}
if (-not $env:DATABASE_URL) { throw 'Set DATABASE_URL in your environment or local .env first.' }
if ($env:APP_ENV -and $env:APP_ENV -ne 'development') { throw 'This launcher is for synthetic development only.' }
$env:APP_ENV = 'development'
New-Item -ItemType Directory -Force -Path $RuntimeDirectory | Out-Null
$pythonExe = Join-Path $RuntimeDirectory 'venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $pythonExe)) { $pythonExe = Join-Path $repoRoot '.venv\Scripts\python.exe' }
if (-not (Test-Path -LiteralPath $pythonExe)) { throw 'Create a Python venv and install services/api[dev] first.' }
$nodeExe = (Get-Command node).Source
$viteScript = Join-Path $BuildDirectory 'node_modules\vite\bin\vite.js'
if (-not (Test-Path -LiteralPath $viteScript)) { throw 'Run scripts/sync-local.ps1 then npm ci in the local build directory.' }
if (-not $env:DEV_AUTH_TOKEN) { $env:DEV_AUTH_TOKEN = [Convert]::ToHexString([Security.Cryptography.RandomNumberGenerator]::GetBytes(32)) }
Set-Content -LiteralPath (Join-Path $RuntimeDirectory 'development-access-key.txt') -Value $env:DEV_AUTH_TOKEN -NoNewline
& $pythonExe (Join-Path $repoRoot 'scripts\migrate.py')
if ($LASTEXITCODE -ne 0) { throw 'Database migration failed; servers were not started.' }
foreach ($port in @(8000,5173)) {
  if (Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue) { throw "Port $port is already in use; do not launch a second instance." }
}
$api = Start-Process -FilePath $pythonExe -ArgumentList @('-m','uvicorn','clinic_api.main:app','--app-dir',('"' + (Join-Path $repoRoot 'services\api\src') + '"'),'--host','127.0.0.1','--port','8000','--no-access-log') -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $RuntimeDirectory 'api.out.log') -RedirectStandardError (Join-Path $RuntimeDirectory 'api.err.log')
$web = Start-Process -FilePath $nodeExe -ArgumentList @(('"' + $viteScript + '"'),'--host','127.0.0.1','--port','5173','--strictPort') -WorkingDirectory (Join-Path $BuildDirectory 'apps\web') -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $RuntimeDirectory 'web.out.log') -RedirectStandardError (Join-Path $RuntimeDirectory 'web.err.log')
@(@{ Id=$api.Id; Started=$api.StartTime.ToUniversalTime().ToString('o') },@{ Id=$web.Id; Started=$web.StartTime.ToUniversalTime().ToString('o') }) | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $RuntimeDirectory 'dev-processes.json')
Write-Output 'Local registry: http://127.0.0.1:5173'
Write-Output "Development key file: $(Join-Path $RuntimeDirectory 'development-access-key.txt')"
Write-Output 'Use fictional patients only. Check readiness at http://127.0.0.1:8000/ready.'
