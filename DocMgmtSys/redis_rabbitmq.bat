@echo off
setlocal

REM ----------- Container Configurations -----------
set REDIS_CONTAINER=redis-server
set REDIS_IMAGE=redis:latest

set RABBIT_CONTAINER=rabbitmq-server
set RABBIT_IMAGE=rabbitmq:3-management

REM ----------- Check for Podman -----------
where podman >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Podman CLI is not installed or not in PATH.
    pause
    exit /b 1
)

REM ----------- Start Podman Machine if Needed -----------
echo Checking Podman machine status...
podman machine info >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Podman machine not running. Starting...
    podman machine start
    if %ERRORLEVEL% NEQ 0 (
        echo Failed to start Podman machine.
        pause
        exit /b 1
    )
)

REM ----------- REDIS CONTAINER -----------
echo.
echo === Setting up Redis ===
echo Checking for existing container "%REDIS_CONTAINER%"...
podman container exists %REDIS_CONTAINER%
IF %ERRORLEVEL% EQU 0 (
    echo Container "%REDIS_CONTAINER%" already exists. Starting...
    podman start %REDIS_CONTAINER%
) ELSE (
    echo Container "%REDIS_CONTAINER%" does not exist.
    echo Pulling image: %REDIS_IMAGE% ...
    podman pull %REDIS_IMAGE%
    echo Running new Redis container...
    podman run -d --name %REDIS_CONTAINER% -p 6379:6379 %REDIS_IMAGE%
)

REM ----------- RABBITMQ CONTAINER -----------
echo.
echo === Setting up RabbitMQ ===
echo Checking for existing container "%RABBIT_CONTAINER%"...
podman container exists %RABBIT_CONTAINER%
IF %ERRORLEVEL% EQU 0 (
    echo Container "%RABBIT_CONTAINER%" already exists. Starting...
    podman start %RABBIT_CONTAINER%
) ELSE (
    echo Container "%RABBIT_CONTAINER%" does not exist.
    echo Pulling image: %RABBIT_IMAGE% ...
    podman pull %RABBIT_IMAGE%
    echo Running new RabbitMQ container...
    podman run -d --name %RABBIT_CONTAINER% -p 5672:5672 -p 15672:15672 %RABBIT_IMAGE%
)

REM ----------- Final Status Output -----------
echo.
echo === Container Status ===
podman ps -a --filter name=%REDIS_CONTAINER%
podman ps -a --filter name=%RABBIT_CONTAINER%
echo.
echo Redis is available on port 6379
echo RabbitMQ is available on:
echo    - AMQP:     localhost:5672
echo    - Web UI:   http://localhost:15672 (user: guest, pass: guest)
echo.

pause
