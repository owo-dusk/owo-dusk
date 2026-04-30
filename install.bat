@echo off
setlocal EnableDelayedExpansion

title owo-dusk Installer

echo.
echo  owo-dusk Installer - Windows
echo  ==============================
echo.

:: check git
git --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [!] git is not installed or not in PATH.
    echo     Download it from: https://git-scm.com/download/win
    echo     Make sure to check "Add git to PATH" during install.
    pause
    exit /b 1
)

:: check python
python --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [!] Python is not installed or not in PATH.
    echo     Download it from: https://www.python.org/downloads/
    echo     Make sure to check "Add Python to PATH" during install.
    pause
    exit /b 1
)

echo [*] git and Python found. Continuing...
echo.

set INSTALL_DIR=%USERPROFILE%\Desktop\owo-dusk

::clone
if exist "%INSTALL_DIR%" (
    echo [!] Folder "%INSTALL_DIR%" already exists.
    set /p CONFIRM="    Re-clone and overwrite? [y/N]: "
    if /i "!CONFIRM!"=="y" (
        rmdir /s /q "%INSTALL_DIR%"
    ) else (
        echo [*] Skipping clone - using existing directory.
        goto :run_setup
    )
)

echo [*] Cloning owo-dusk to your Desktop...
git clone https://github.com/echoquill/owo-dusk.git "%INSTALL_DIR%"
if %ERRORLEVEL% neq 0 (
    echo [!] Failed to clone repository. Check your internet connection.
    pause
    exit /b 1
)

:run_setup
::setup
cd /d "%INSTALL_DIR%"
echo.
echo [*] Running setup.py...
python setup.py
if %ERRORLEVEL% neq 0 (
    echo [!] setup.py exited with an error.
    pause
    exit /b 1
)

:: launch
echo.
echo [OK] Setup complete! Launching owo-dusk...
echo.
python uwu.py

:: re-run command
echo.
echo -------------------------------------------------------
echo  To run owo-dusk again next time, open CMD and run:
echo    cd "%INSTALL_DIR%" ^&^& python uwu.py
echo -------------------------------------------------------
echo.
pause
