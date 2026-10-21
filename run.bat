@echo off
setlocal EnableExtensions EnableDelayedExpansion
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

echo Building the image if this is the first time, then starting the card server.
echo The first start reads the Photoshop templates and can take several minutes.
docker compose up -d --build
if errorlevel 1 goto fail

echo Waiting for the card server on port !CARD_PORT!...
set /a TRIES=0

:waitloop
set /a TRIES+=1
if !TRIES! GTR 180 goto notready
curl.exe -sf -o NUL "http://127.0.0.1:!CARD_PORT!/"
if not errorlevel 1 goto ready
docker compose ps -a --format "{{.State}}" | findstr /i "exited" >nul
if not errorlevel 1 goto died
echo Still starting. Preparing the card frames can take several minutes.
docker compose logs --tail 6
timeout /t 5 /nobreak >nul
goto waitloop

:died
echo The card server stopped while starting.
docker compose logs --tail 80
docker compose down
goto fail

:notready
echo The card server did not start.
docker compose logs --tail 80
docker compose down
goto fail

:ready
echo Card server is ready. Opening the window...
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0desktop\open_window.ps1" "http://127.0.0.1:!CARD_PORT!"
set CODE=!ERRORLEVEL!
docker compose down
exit /b !CODE!

:fail
echo.
pause
exit /b 1
