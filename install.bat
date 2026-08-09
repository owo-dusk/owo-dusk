@echo off
setlocal EnableDelayedExpansion

title owo-dusk Installer

echo.
echo  owo-dusk Installer - Windows
echo  ==============================
echo.

set "OWO_REPO_URL=https://github.com/owo-dusk/owo-dusk.git"
set "INSTALL_DIR=%USERPROFILE%\Desktop\owo-dusk"

set "GIT_VERSION=2.55.0.windows.3"
set "GIT_PORTABLE_ASSET=PortableGit-2.55.0.3-64-bit.7z.exe"
set "GIT_INSTALL_DIR=%LocalAppData%\Programs\Git"
set "GIT_CMD="

set "PYTHON_VERSION=3.12.8"
set "PYTHON_INSTALL_DIR=%LocalAppData%\Programs\Python\Python312"
set "PY_CMD="

:: ---------------------------------------------------------------
:: 1) Make sure Git is available. An existing install is reused;
::    otherwise a portable Git is downloaded and extracted silently
::    (per-user, no admin rights required).
:: ---------------------------------------------------------------
echo [*] Checking for Git...
call :find_git
if errorlevel 1 (
    echo [^!] Git not found. Installing portable Git %GIT_VERSION% silently...
    call :install_git
    if errorlevel 1 (
        echo [x] Failed to install Git automatically.
        echo     Please install it manually from https://git-scm.com/download/win
        echo     and make sure "Add git to PATH" is checked.
        pause
        exit /b 1
    )
    call :find_git
    if errorlevel 1 (
        echo [x] Git is still not usable, cannot continue.
        pause
        exit /b 1
    )
)
echo [*] Using Git: "%GIT_CMD%"
echo.

:: ---------------------------------------------------------------
:: 2) Make sure Python 3.12 is available. An existing 3.12.x is
::    reused; otherwise Python %PYTHON_VERSION% is downloaded and
::    installed silently (per-user, no admin rights required).
:: ---------------------------------------------------------------
echo [*] Checking for Python %PYTHON_VERSION%...
call :find_python
if errorlevel 1 (
    echo [^!] Python %PYTHON_VERSION% not found. Installing it silently...
    call :install_python
    if errorlevel 1 (
        echo [x] Failed to install Python automatically.
        echo     Please install it manually from https://www.python.org/downloads/
        echo     and make sure "Add Python to PATH" is checked.
        pause
        exit /b 1
    )
    call :find_python
    if errorlevel 1 (
        echo [x] Python is still not usable, cannot continue.
        pause
        exit /b 1
    )
)
echo [*] Using Python: "%PY_CMD%"
"%PY_CMD%" --version
echo.

:: ---------------------------------------------------------------
:: 3) Clone (or reuse) the repository
:: ---------------------------------------------------------------
if exist "%INSTALL_DIR%" (
    echo [^!] Folder "%INSTALL_DIR%" already exists.
    set /p CONFIRM="    Re-clone and overwrite? [y/N]: "
    if /i "!CONFIRM!"=="y" (
        rmdir /s /q "%INSTALL_DIR%"
    ) else (
        echo [*] Skipping clone - using existing directory.
        goto :run_setup
    )
)

echo [*] Cloning owo-dusk to your Desktop...
"%GIT_CMD%" clone --depth 1 "%OWO_REPO_URL%" "%INSTALL_DIR%"
if errorlevel 1 (
    echo [^!] Failed to clone repository. Check your internet connection.
    pause
    exit /b 1
)

:run_setup
cd /d "%INSTALL_DIR%"
echo.
echo [*] Running setup.py...
"%PY_CMD%" setup.py
if errorlevel 1 (
    echo [^!] setup.py exited with an error.
    pause
    exit /b 1
)

:: launch
echo.
echo [OK] Setup complete^! Launching owo-dusk...
echo.
if defined OWO_INSTALLER_SKIP_LAUNCH (
    echo [i] OWO_INSTALLER_SKIP_LAUNCH is set - skipping the app launch.
) else (
    "%PY_CMD%" uwu.py
)

:: re-run command
echo.
echo -------------------------------------------------------
echo  To run owo-dusk again next time, open CMD and run:
echo    cd "%INSTALL_DIR%" ^&^& python uwu.py
echo -------------------------------------------------------
echo.
pause
exit /b 0

:: ================================================================
:: Subroutines
:: ================================================================

:: Try to locate an existing Git install; sets GIT_CMD on success.
:find_git
set "GIT_CMD="
git --version >nul 2>&1
if not errorlevel 1 ( set "GIT_CMD=git" & exit /b 0 )
if exist "%ProgramFiles%\Git\cmd\git.exe" ( set "GIT_CMD=%ProgramFiles%\Git\cmd\git.exe" & set "PATH=%ProgramFiles%\Git\cmd;%PATH%" & exit /b 0 )
if exist "%GIT_INSTALL_DIR%\cmd\git.exe" ( set "GIT_CMD=%GIT_INSTALL_DIR%\cmd\git.exe" & set "PATH=%GIT_INSTALL_DIR%\cmd;%PATH%" & exit /b 0 )
exit /b 1

:: Download and extract a portable Git (no admin rights required).
:install_git
set "GIT_INSTALLER=%TEMP%\%GIT_PORTABLE_ASSET%"
if not exist "%GIT_INSTALLER%" (
    echo     Downloading %GIT_PORTABLE_ASSET%...
    call :download "https://github.com/git-for-windows/git/releases/download/v%GIT_VERSION%/%GIT_PORTABLE_ASSET%" "%GIT_INSTALLER%"
    if errorlevel 1 ( exit /b 1 )
)
echo     Extracting to "%GIT_INSTALL_DIR%"...
if not exist "%GIT_INSTALL_DIR%" mkdir "%GIT_INSTALL_DIR%"
"%GIT_INSTALLER%" -o"%GIT_INSTALL_DIR%" -y >nul 2>&1
if errorlevel 1 ( exit /b 1 )
if not exist "%GIT_INSTALL_DIR%\cmd\git.exe" ( exit /b 1 )
:: make git available to this session (and to pip subprocesses) immediately
set "PATH=%GIT_INSTALL_DIR%\cmd;%PATH%"
exit /b 0

:: Try to locate a usable Python 3.12.x; sets PY_CMD on success.
:find_python
set "PY_CMD="
:: 1) the py launcher, if a 3.12 is registered
for /f "delims=" %%P in ('py -3.12 -c "import sys;print(sys.executable)" 2^>nul') do set "PY_CMD=%%P"
if defined PY_CMD ( exit /b 0 )
:: 2) a bare `python` that is already a 3.12.x
set "PY_VER="
for /f "tokens=2 delims= " %%v in ('python --version 2^>^&1') do set "PY_VER=%%v"
if defined PY_VER (
    echo !PY_VER! | findstr /b "3.12." >nul 2>&1
    if not errorlevel 1 ( set "PY_CMD=python" & exit /b 0 )
)
:: 3) common install locations
if exist "%PYTHON_INSTALL_DIR%\python.exe" ( set "PY_CMD=%PYTHON_INSTALL_DIR%\python.exe" & set "PATH=%PYTHON_INSTALL_DIR%;%PATH%" & exit /b 0 )
if exist "%ProgramFiles%\Python312\python.exe" ( set "PY_CMD=%ProgramFiles%\Python312\python.exe" & set "PATH=%ProgramFiles%\Python312;%PATH%" & exit /b 0 )
exit /b 1

:: Download and silently install Python %PYTHON_VERSION% per-user (no admin).
:install_python
set "PYTHON_INSTALLER=%TEMP%\python-%PYTHON_VERSION%-amd64.exe"
if not exist "%PYTHON_INSTALLER%" (
    echo     Downloading Python %PYTHON_VERSION%...
    call :download "https://www.python.org/ftp/python/%PYTHON_VERSION%/python-%PYTHON_VERSION%-amd64.exe" "%PYTHON_INSTALLER%"
    if errorlevel 1 ( exit /b 1 )
)
echo     Installing Python %PYTHON_VERSION% silently (per-user)...
"%PYTHON_INSTALLER%" /quiet InstallAllUsers=0 PrependPath=1 Include_test=0 Include_doc=0 Include_launcher=0 Shortcuts=0 AssociateFiles=0 InstallDir="%PYTHON_INSTALL_DIR%"
if errorlevel 1 ( exit /b 1 )
if not exist "%PYTHON_INSTALL_DIR%\python.exe" ( exit /b 1 )
:: make python available to this session (and to the app) immediately
set "PATH=%PYTHON_INSTALL_DIR%;%PATH%"
exit /b 0

:: Download helper - tries curl (bundled with Win10+), falls back to PowerShell.
:download
set "DL_URL=%~1"
set "DL_OUT=%~2"
curl.exe -fSL --retry 3 -o "%DL_OUT%" "%DL_URL%" >nul 2>&1
if not errorlevel 1 ( exit /b 0 )
powershell.exe -NoProfile -NonInteractive -Command "Invoke-WebRequest -UseBasicParsing -Uri '%DL_URL%' -OutFile '%DL_OUT%'" >nul 2>&1
if not errorlevel 1 ( exit /b 0 )
exit /b 1
