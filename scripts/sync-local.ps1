param([string]$Destination = (Join-Path $env:LOCALAPPDATA 'ClinicSystem\build'))
$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path $PSScriptRoot -Parent
$Destination = [IO.Path]::GetFullPath($Destination)
if ($Destination -eq $repoRoot) { throw 'Use a separate local build directory.' }
New-Item -ItemType Directory -Force -Path $Destination | Out-Null
Push-Location $repoRoot
try {
  $sourceFiles = @(git ls-files --cached --others --exclude-standard | Sort-Object -Unique)
  if ($LASTEXITCODE -ne 0) { throw 'Git file inventory failed.' }
  foreach ($relativePath in $sourceFiles) {
    $sourcePath = Join-Path $repoRoot $relativePath
    if (-not (Test-Path -LiteralPath $sourcePath -PathType Leaf)) { continue }
    $targetPath = [IO.Path]::GetFullPath((Join-Path $Destination $relativePath))
    if (-not $targetPath.StartsWith($Destination + [IO.Path]::DirectorySeparatorChar)) { throw 'Invalid destination path.' }
    New-Item -ItemType Directory -Force -Path (Split-Path $targetPath -Parent) | Out-Null
    Copy-Item -LiteralPath $sourcePath -Destination $targetPath -Force
  }
} finally { Pop-Location }
Write-Output "Source synchronized to $Destination. Run npm ci there; dependency folders stay local."
