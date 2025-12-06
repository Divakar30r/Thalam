@echo off
echo Clearing Python cache files...

cd /d "%~dp0\.."

REM Delete all __pycache__ directories
for /d /r %%i in (__pycache__) do (
    if exist "%%i" (
        echo Removing: %%i
        rmdir /s /q "%%i"
    )
)

REM Delete all .pyc files
for /r %%i in (*.pyc) do (
    if exist "%%i" (
        echo Removing: %%i
        del /q "%%i"
    )
)

echo.
echo Cache cleared successfully!
echo Please restart your Python services.
pause
