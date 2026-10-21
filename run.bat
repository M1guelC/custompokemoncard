@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"

rem A double-click opens a black console. Hand that off to the hidden launcher.
echo %CMDCMDLINE% | find /i "/c" >nul
if not errorlevel 1 (
  if /I not "%~1"=="hidden" (
    wscript //nologo "%~dp0run.vbs"
    exit /b
  )
)

where docker >nul 2>&1
if errorlevel 1 (
  set "CARD_MSG=Docker is not available. Install Docker Desktop, start it, then try again."
  goto fail
)
docker info >nul 2>&1
if errorlevel 1 (
  set "CARD_MSG=Docker is installed, but the engine is not running. Start Docker Desktop, then try again."
  goto fail
)

set CARD_UID=0
set CARD_GID=0
for /f %%P in ('powershell -NoProfile -Command "$l = New-Object System.Net.Sockets.TcpListener([Net.IPAddress]::Loopback, 0); $l.Start(); $p = $l.LocalEndpoint.Port; $l.Stop(); Write-Output $p"') do set CARD_PORT=%%P
if not defined CARD_PORT (
  set "CARD_MSG=Could not choose a port for the card server."
  goto fail
)

echo Building the image if this is the first time, then starting the card server.
echo The first start reads the Photoshop templates and can take several minutes.
docker compose up -d --build
if errorlevel 1 (
  set "CARD_MSG=Docker could not start the card server."
  goto fail
)

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
ping -n 6 127.0.0.1 >nul
goto waitloop

:died
echo The card server stopped while starting.
docker compose logs --tail 80
docker compose down
set "CARD_MSG=The card server stopped while starting. Start Docker Desktop and try again."
goto fail

:notready
echo The card server did not start.
docker compose logs --tail 80
docker compose down
set "CARD_MSG=The card server did not start. The first launch can take several minutes. Try run.vbs again."
goto fail

:ready
echo Card server is ready. Opening the window...
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0desktop\open_window.ps1" "http://127.0.0.1:!CARD_PORT!"
set CODE=!ERRORLEVEL!
docker compose down
exit /b !CODE!

:fail
if not defined CARD_MSG set "CARD_MSG=The card creator did not start."
if /I "%~1"=="hidden" (
  powershell -NoProfile -Command "Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.MessageBox]::Show($env:CARD_MSG, 'Card creator')" >nul
  exit /b 1
)
echo.
echo !CARD_MSG!
pause
exit /b 1
