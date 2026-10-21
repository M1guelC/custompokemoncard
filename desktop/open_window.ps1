param(
  [Parameter(Mandatory = $true)]
  [string]$Url
)

$ErrorActionPreference = "Stop"
$desktop = Split-Path -Parent $MyInvocation.MyCommand.Path
$version = "45.0.0"
$root = Join-Path $env:LOCALAPPDATA "card-creator"
$runtime = Join-Path $root "runtime"
$exe = Join-Path $runtime "electron.exe"
$marker = Join-Path $runtime "version"
$installed = ""
if (Test-Path $marker) { $installed = (Get-Content $marker -Raw).Trim() }

if (-not (Test-Path $exe) -or $installed -ne $version) {
  Write-Host "Downloading the Windows window..."
  if (Test-Path $runtime) { Remove-Item $runtime -Recurse -Force }
  New-Item -ItemType Directory -Path $runtime | Out-Null
  $zip = Join-Path $env:TEMP "electron-$version-win.zip"
  $release = "https://github.com/electron/electron/releases/download/v$version/electron-v$version-win32-x64.zip"
  Invoke-WebRequest -Uri $release -OutFile $zip -UseBasicParsing
  Expand-Archive -Path $zip -DestinationPath $runtime -Force
  Set-Content -Path $marker -Value $version -NoNewline
}

$app = Join-Path $root "app"
New-Item -ItemType Directory -Path $app -Force | Out-Null
Copy-Item (Join-Path $desktop "main.js") $app -Force
Copy-Item (Join-Path $desktop "package.json") $app -Force
$env:CARD_URL = $Url
$process = Start-Process -FilePath $exe -WorkingDirectory $runtime -ArgumentList @($app, "--", "--card-url=$Url") -Wait -PassThru
exit $process.ExitCode
