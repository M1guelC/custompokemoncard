@echo off
setlocal EnableExtensions
cd /d "%~dp0"

where docker >nul 2>&1
if errorlevel 1 (
  echo Docker is not available. Install Docker Desktop, start it, then run run.bat again.
  goto fail
)
docker info >nul 2>&1
if errorlevel 1 (
  echo Docker is installed, but the engine is not running. Start Docker Desktop, then run run.bat again.
  goto fail
)

set CARD_UID=0
set CARD_GID=0
for /f %%P in ('powershell -NoProfile -Command "$l = New-Object System.Net.Sockets.TcpListener([Net.IPAddress]::Loopback, 0); $l.Start(); $p = $l.LocalEndpoint.Port; $l.Stop(); Write-Output $p"') do set CARD_PORT=%%P
if not defined CARD_PORT (
  echo Could not choose a port.
  goto fail
)

docker compose up -d --build
if errorlevel 1 goto fail

echo Waiting for the card server...
for /l %%I in (1,1,180) do (
  curl.exe -sf -o NUL "http://127.0.0.1:%CARD_PORT%/"
  if not errorlevel 1 goto ready
  timeout /t 2 /nobreak >nul
)
echo The card server did not start.
docker compose logs
docker compose down
goto fail

:ready
where py >nul 2>&1
if not errorlevel 1 (
  py -3 desktop\open_window.py "http://127.0.0.1:%CARD_PORT%"
) else (
  python desktop\open_window.py "http://127.0.0.1:%CARD_PORT%"
)
set CODE=%ERRORLEVEL%
docker compose down
exit /b %CODE%

:fail
echo.
pause
exit /b 1
