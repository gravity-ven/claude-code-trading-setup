@echo off
setlocal EnableDelayedExpansion
title Spartan Research Station - Control Panel

:: SPARTAN RESEARCH STATION CONTROL PANEL
:: Single file to START, STOP, RESTART, and CHECK status
:: Works on Windows with Docker Desktop

:: ============================================================
:: COLOR DEFINITIONS
:: ============================================================
set "GREEN=[92m"
set "RED=[91m"
set "YELLOW=[93m"
set "BLUE=[94m"
set "CYAN=[96m"
set "WHITE=[97m"
set "RESET=[0m"

:MENU
cls
echo.
echo %CYAN%╔══════════════════════════════════════════════════════════╗%RESET%
echo %CYAN%║                                                          ║%RESET%
echo %CYAN%║%RESET%        %WHITE%SPARTAN RESEARCH STATION - CONTROL PANEL%RESET%        %CYAN%║%RESET%
echo %CYAN%║                                                          ║%RESET%
echo %CYAN%╚══════════════════════════════════════════════════════════╝%RESET%
echo.
echo %YELLOW%  What would you like to do?%RESET%
echo.
echo   %GREEN%[1]%RESET% START   - Start all services
echo   %RED%[2]%RESET% STOP    - Stop all services
echo   %YELLOW%[3]%RESET% RESTART - Restart all services
echo   %BLUE%[4]%RESET% STATUS  - Check system status
echo   %CYAN%[5]%RESET% BUILD   - Rebuild containers
echo   %WHITE%[6]%RESET% LOGS    - View logs
echo   %RED%[0]%RESET% EXIT    - Exit control panel
echo.
set /p "choice=%CYAN%Enter your choice [0-6]:%RESET% "

if "%choice%"=="1" goto START
if "%choice%"=="2" goto STOP
if "%choice%"=="3" goto RESTART
if "%choice%"=="4" goto STATUS
if "%choice%"=="5" goto BUILD
if "%choice%"=="6" goto LOGS
if "%choice%"=="0" goto END
goto MENU

:: ============================================================
:: START SERVICES
:: ============================================================
:START
cls
echo.
echo %GREEN%╔══════════════════════════════════════════════════════════╗%RESET%
echo %GREEN%║         STARTING SPARTAN RESEARCH STATION                ║%RESET%
echo %GREEN%╚══════════════════════════════════════════════════════════╝%RESET%
echo.

:: Change to website directory
cd /d "%~dp0"

:: Check Docker Desktop
echo %CYAN%[1/3] Checking Docker Desktop...%RESET%
docker info >nul 2>&1
if errorlevel 1 (
    echo %RED%❌ ERROR: Docker Desktop is not running!%RESET%
    echo.
    echo %YELLOW%Please start Docker Desktop and try again.%RESET%
    pause
    goto MENU
)
echo %GREEN%✓ Docker Desktop is running%RESET%
echo.

:: Start services
echo %CYAN%[2/3] Starting all services...%RESET%
docker-compose -f docker-compose.spartan.yml up -d
if errorlevel 1 (
    echo %RED%❌ ERROR: Failed to start services!%RESET%
    pause
    goto MENU
)
echo %GREEN%✓ Services started successfully%RESET%
echo.

:: Wait for services to be ready
echo %CYAN%[3/3] Waiting for services to be ready...%RESET%
timeout /t 5 /nobreak >nul
echo %GREEN%✓ Services ready%RESET%
echo.

:: Show access info
echo %GREEN%╔══════════════════════════════════════════════════════════╗%RESET%
echo %GREEN%║                    ✓ SYSTEM STARTED                      ║%RESET%
echo %GREEN%╚══════════════════════════════════════════════════════════╝%RESET%
echo.
echo %CYAN%Access your dashboard at:%RESET%
echo   %WHITE%http://localhost:8888%RESET%
echo.
echo %CYAN%Services running:%RESET%
echo   %WHITE%• PostgreSQL  (Database)%RESET%
echo   %WHITE%• Redis       (Cache)%RESET%
echo   %WHITE%• Web Server  (Ports 8888, 9000)%RESET%
echo   %WHITE%• Grafana     (Port 3000)%RESET%
echo.
pause
goto MENU

:: ============================================================
:: STOP SERVICES
:: ============================================================
:STOP
cls
echo.
echo %RED%╔══════════════════════════════════════════════════════════╗%RESET%
echo %RED%║          STOPPING SPARTAN RESEARCH STATION               ║%RESET%
echo %RED%╚══════════════════════════════════════════════════════════╝%RESET%
echo.

cd /d "%~dp0"

echo %CYAN%Stopping all services...%RESET%
docker-compose -f docker-compose.spartan.yml down
if errorlevel 1 (
    echo %RED%❌ ERROR: Failed to stop services!%RESET%
    pause
    goto MENU
)

echo.
echo %GREEN%✓ All services stopped successfully%RESET%
echo.
pause
goto MENU

:: ============================================================
:: RESTART SERVICES
:: ============================================================
:RESTART
cls
echo.
echo %YELLOW%╔══════════════════════════════════════════════════════════╗%RESET%
echo %YELLOW%║         RESTARTING SPARTAN RESEARCH STATION              ║%RESET%
echo %YELLOW%╚══════════════════════════════════════════════════════════╝%RESET%
echo.

cd /d "%~dp0"

echo %CYAN%[1/2] Stopping services...%RESET%
docker-compose -f docker-compose.spartan.yml down
echo %GREEN%✓ Services stopped%RESET%
echo.

echo %CYAN%[2/2] Starting services...%RESET%
docker-compose -f docker-compose.spartan.yml up -d
if errorlevel 1 (
    echo %RED%❌ ERROR: Failed to restart services!%RESET%
    pause
    goto MENU
)
echo %GREEN%✓ Services restarted%RESET%
echo.

timeout /t 3 /nobreak >nul
echo %GREEN%System ready at http://localhost:8888%RESET%
echo.
pause
goto MENU

:: ============================================================
:: CHECK STATUS
:: ============================================================
:STATUS
cls
echo.
echo %BLUE%╔══════════════════════════════════════════════════════════╗%RESET%
echo %BLUE%║              SPARTAN SYSTEM STATUS                       ║%RESET%
echo %BLUE%╚══════════════════════════════════════════════════════════╝%RESET%
echo.

cd /d "%~dp0"

:: Check Docker
echo %CYAN%Docker Desktop Status:%RESET%
docker info >nul 2>&1
if errorlevel 1 (
    echo   %RED%❌ Docker Desktop is NOT running%RESET%
) else (
    echo   %GREEN%✓ Docker Desktop is running%RESET%
)
echo.

:: Check containers
echo %CYAN%Container Status:%RESET%
docker-compose -f docker-compose.spartan.yml ps
echo.

:: Check website accessibility
echo %CYAN%Website Accessibility:%RESET%
curl -s http://localhost:8888/health >nul 2>&1
if errorlevel 1 (
    echo   %RED%❌ Website is NOT accessible%RESET%
) else (
    echo   %GREEN%✓ Website is accessible at http://localhost:8888%RESET%
)
echo.

pause
goto MENU

:: ============================================================
:: BUILD CONTAINERS
:: ============================================================
:BUILD
cls
echo.
echo %YELLOW%╔══════════════════════════════════════════════════════════╗%RESET%
echo %YELLOW%║           REBUILDING DOCKER CONTAINERS                   ║%RESET%
echo %YELLOW%╚══════════════════════════════════════════════════════════╝%RESET%
echo.

cd /d "%~dp0"

echo %CYAN%This will rebuild all containers from scratch.%RESET%
echo %YELLOW%This may take several minutes...%RESET%
echo.
set /p "confirm=Continue? (Y/N): "
if /i not "%confirm%"=="Y" goto MENU

echo.
echo %CYAN%Building containers...%RESET%
docker-compose -f docker-compose.spartan.yml build
if errorlevel 1 (
    echo %RED%❌ ERROR: Build failed!%RESET%
    pause
    goto MENU
)

echo.
echo %GREEN%✓ Build completed successfully%RESET%
echo.
echo %YELLOW%Run START to launch the rebuilt containers.%RESET%
echo.
pause
goto MENU

:: ============================================================
:: VIEW LOGS
:: ============================================================
:LOGS
cls
echo.
echo %CYAN%╔══════════════════════════════════════════════════════════╗%RESET%
echo %CYAN%║                   VIEW CONTAINER LOGS                    ║%RESET%
echo %CYAN%╚══════════════════════════════════════════════════════════╝%RESET%
echo.

cd /d "%~dp0"

echo %WHITE%Available containers:%RESET%
echo   %CYAN%[1]%RESET% spartan_web
echo   %CYAN%[2]%RESET% spartan_postgres
echo   %CYAN%[3]%RESET% spartan_redis
echo   %CYAN%[4]%RESET% spartan_preloader
echo   %CYAN%[5]%RESET% spartan_grafana
echo   %CYAN%[0]%RESET% Back to main menu
echo.
set /p "logchoice=Select container: "

if "%logchoice%"=="1" docker logs spartan_web --tail 50
if "%logchoice%"=="2" docker logs spartan_postgres --tail 50
if "%logchoice%"=="3" docker logs spartan_redis --tail 50
if "%logchoice%"=="4" docker logs spartan_preloader --tail 50
if "%logchoice%"=="5" docker logs spartan_grafana --tail 50
if "%logchoice%"=="0" goto MENU

echo.
pause
goto LOGS

:: ============================================================
:: EXIT
:: ============================================================
:END
cls
echo.
echo %GREEN%Thank you for using Spartan Research Station!%RESET%
echo.
timeout /t 2 /nobreak >nul
exit /b 0
