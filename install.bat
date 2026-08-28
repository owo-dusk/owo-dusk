@echo off
setlocal EnableExtensions EnableDelayedExpansion

title OwO-Dusk Installer

echo.
echo  OwO-Dusk Installer - Windows
echo  ==============================
echo.

set "OWO_REPO_URL=https://github.com/owo-dusk/owo-dusk.git"
set "INSTALL_DIR=%USERPROFILE%\Desktop\owo-dusk"

set "GIT_VERSION=2.55.0.windows.5"
set "GIT_PORTABLE_ASSET=PortableGit-2.55.0.5-64-bit.7z.exe"
set "GIT_INSTALL_DIR=%LocalAppData%\Programs\Git"
set "GIT_CMD="
set "GIT_SHA256=5aa8a20f6e9abb2c755f0e73c91c687701a46b309ad84a0ca6509380fa4ae290"

set "PYTHON_VERSION=3.13.15"
set "MIN_PYTHON_VERSION=3.12"
set "PYTHON_INSTALL_DIR=%LocalAppData%\Programs\Python\Python313"
set "PYTHON_SHA256=edec09c4853aeae9ac36efb8c9f95b6b8e2fee65eee56d9767a8b7c69c574403"
:: Will be set later
set "PY_CMD="


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

echo [*] Checking for Python %MIN_PYTHON_VERSION%+...
call :find_python
if errorlevel 1 (
    echo [^!] Python %MIN_PYTHON_VERSION%+ not found. Installing Python %PYTHON_VERSION% silently...
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

:: Clone OwO-Dusk repo.
if exist "%INSTALL_DIR%" (
    echo [^!] Folder "%INSTALL_DIR%" already exists.
    set "CONFIRM="
    set /p CONFIRM="    Re-clone and overwrite? [y/N]: "
    if /i "!CONFIRM!"=="y" (
        echo "%INSTALL_DIR%" | findstr /i "\owo-dusk" >nul 2>&1
        if errorlevel 1 (
            echo [x] Safety check failed - install path doesn't look right. Aborting.
            pause
            exit /b 1
        )
        echo     If owo-dusk is currently running, please close it first.
        rmdir /s /q "%INSTALL_DIR%"
        if exist "%INSTALL_DIR%" (
            :: Windows prevents deletion of files that are active
            echo [x] Failed to delete existing directory. Close any open files/terminals and try again.
            pause
            exit /b 1
        )
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
cd /d "%INSTALL_DIR%" || (
    echo [x] Failed to enter "%INSTALL_DIR%".
    pause
    exit /b 1
)
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
echo    cd "%INSTALL_DIR%" ^&^& "%PY_CMD%" uwu.py
echo -------------------------------------------------------
echo.
pause
endlocal & set "PATH=%PATH%"
exit /b 0

:: Try to locate an existing Git install; sets GIT_CMD on success.
:find_git
set "GIT_CMD="
git --version >nul 2>&1
if not errorlevel 1 ( set "GIT_CMD=git" & exit /b 0 )
if exist "%ProgramFiles%\Git\cmd\git.exe" ( set "GIT_CMD=%ProgramFiles%\Git\cmd\git.exe" & set "PATH=%ProgramFiles%\Git\cmd;%PATH%" & exit /b 0 )
if exist "%GIT_INSTALL_DIR%\cmd\git.exe" ( set "GIT_CMD=%GIT_INSTALL_DIR%\cmd\git.exe" & set "PATH=%GIT_INSTALL_DIR%\cmd;%PATH%" & exit /b 0 )
exit /b 1

:: Install Git if not installed
:install_git
set "GIT_INSTALLER=%TEMP%\%GIT_PORTABLE_ASSET%"
set "GIT_HAVE_GOOD_INSTALLER=0"

if exist "%GIT_INSTALLER%" (
    call :verify_sha256 "%GIT_INSTALLER%" "%GIT_SHA256%"
    if not errorlevel 1 set "GIT_HAVE_GOOD_INSTALLER=1"
)

if "%GIT_HAVE_GOOD_INSTALLER%"=="0" (
    echo     Downloading %GIT_PORTABLE_ASSET%...
    call :download "https://github.com/git-for-windows/git/releases/download/v%GIT_VERSION%/%GIT_PORTABLE_ASSET%" "%GIT_INSTALLER%"
    if errorlevel 1 ( exit /b 1 )
    call :verify_sha256 "%GIT_INSTALLER%" "%GIT_SHA256%"
    if errorlevel 1 (
        echo     Downloaded file failed checksum verification - aborting.
        del /f /q "%GIT_INSTALLER%" >nul 2>&1
        exit /b 1
    )
)

echo     Extracting to "%GIT_INSTALL_DIR%"...
if not exist "%GIT_INSTALL_DIR%" mkdir "%GIT_INSTALL_DIR%"
"%GIT_INSTALLER%" -o"%GIT_INSTALL_DIR%" -y >nul 2>&1
if errorlevel 1 ( exit /b 1 )
if not exist "%GIT_INSTALL_DIR%\cmd\git.exe" ( exit /b 1 )

:: Update current session PATH
set "PATH=%GIT_INSTALL_DIR%\cmd;%PATH%"

:: Permanently update User PATH in Windows Registry
powershell.exe -NoProfile -NonInteractive -Command "$p = [Environment]::GetEnvironmentVariable('PATH', 'User'); if ($p -notlike '*' + $env:GIT_INSTALL_DIR + '\cmd*') { [Environment]::SetEnvironmentVariable('PATH', $env:GIT_INSTALL_DIR + '\cmd;' + $p, 'User') }"

exit /b 0

:: Attempts to find any python version installed
:find_python
set "PY_CMD="

:: 1) Standard `py` launcher (locates any registered Python, even if off PATH)
for /f "delims=" %%P in ('py -3 -c "import sys; sys.version_info >= (%MIN_PYTHON_VERSION:.=, %) and print(sys.executable)" 2^>nul') do set "PY_CMD=%%P"
if defined PY_CMD goto :prompt_add_path

:: 2) Check `python` on PATH (skipping WindowsApps Store execution alias)
set "PY_CMD="
for /f "delims=" %%W in ('where python 2^>nul') do (
    if not defined PY_CMD (
        echo %%W | findstr /i "WindowsApps" >nul 2>&1
        if errorlevel 1 (
            for /f "delims=" %%P in ('"%%W" -c "import sys; sys.version_info >= (%MIN_PYTHON_VERSION:.=, %) and print(sys.executable)" 2^>nul') do (
                set "PY_CMD=%%W"
            )
        )
    )
)
if defined PY_CMD exit /b 0

:: 3) Check Windows Registry (finds official installs not added to PATH)
for /f "tokens=2*" %%A in ('reg query "HKCU\Software\Python\PythonCore" /s /v InstallPath 2^>nul ^| findstr /i "REG_SZ"') do (
    if exist "%%B\python.exe" (
        for /f "delims=" %%P in ('"%%B\python.exe" -c "import sys; sys.version_info >= (%MIN_PYTHON_VERSION:.=, %) and print(sys.executable)" 2^>nul') do set "PY_CMD=%%B\python.exe"
        if defined PY_CMD goto :prompt_add_path
    )
)
for /f "tokens=2*" %%A in ('reg query "HKLM\Software\Python\PythonCore" /s /v InstallPath 2^>nul ^| findstr /i "REG_SZ"') do (
    if exist "%%B\python.exe" (
        for /f "delims=" %%P in ('"%%B\python.exe" -c "import sys; sys.version_info >= (%MIN_PYTHON_VERSION:.=, %) and print(sys.executable)" 2^>nul') do set "PY_CMD=%%B\python.exe"
        if defined PY_CMD goto :prompt_add_path
    )
)

:: 4) Fallback: Search standard install folders off PATH
:: Per-user installation directory (default installer location when non-admin)
for /d %%D in ("%LOCALAPPDATA%\Programs\Python\Python*") do (
    if exist "%%D\python.exe" (
        for /f "delims=" %%P in ('"%%D\python.exe" -c "import sys; sys.version_info >= (%MIN_PYTHON_VERSION:.=, %) and print(sys.executable)" 2^>nul') do set "PY_CMD=%%D\python.exe"
        if defined PY_CMD goto :prompt_add_path
    )
)
:: System-wide installation directories
for /d %%D in ("%ProgramFiles%\Python*") do (
    if exist "%%D\python.exe" (
        for /f "delims=" %%P in ('"%%D\python.exe" -c "import sys; sys.version_info >= (%MIN_PYTHON_VERSION:.=, %) and print(sys.executable)" 2^>nul') do set "PY_CMD=%%D\python.exe"
        if defined PY_CMD goto :prompt_add_path
    )
)
for /d %%D in ("%ProgramFiles(x86)%\Python*") do (
    if exist "%%D\python.exe" (
        for /f "delims=" %%P in ('"%%D\python.exe" -c "import sys; sys.version_info >= (%MIN_PYTHON_VERSION:.=, %) and print(sys.executable)" 2^>nul') do set "PY_CMD=%%D\python.exe"
        if defined PY_CMD goto :prompt_add_path
    )
)

exit /b 1

:prompt_add_path
for %%I in ("!PY_CMD!") do set "PY_DIR=%%~dpI"
set "PY_DIR=!PY_DIR:~0,-1!"
echo !PATH! | findstr /i /c:"!PY_DIR!" >nul 2>&1
if errorlevel 1 (
    echo [^!] Found Python at "!PY_CMD!", but its directory is not in PATH.
    set "ADD_PATH_CHOICE="
    set /p ADD_PATH_CHOICE="    Add "!PY_DIR!" to current session PATH? [y/N]: "
    if /i "!ADD_PATH_CHOICE!"=="y" (
        set "PATH=!PY_DIR!;!PATH!"
        echo [*] Added Python directory to session PATH.
    )
)
exit /b 0

:: Install Python v3.13.15
:install_python
set "PYTHON_INSTALLER=%TEMP%\python-%PYTHON_VERSION%-amd64.exe"
set "PY_HAVE_GOOD_INSTALLER=0"

if exist "%PYTHON_INSTALLER%" (
    call :verify_sha256 "%PYTHON_INSTALLER%" "%PYTHON_SHA256%"
    if not errorlevel 1 set "PY_HAVE_GOOD_INSTALLER=1"
)

if "%PY_HAVE_GOOD_INSTALLER%"=="0" (
    echo     Downloading Python %PYTHON_VERSION%...
    call :download "https://www.python.org/ftp/python/%PYTHON_VERSION%/python-%PYTHON_VERSION%-amd64.exe" "%PYTHON_INSTALLER%"
    if errorlevel 1 ( exit /b 1 )
    call :verify_sha256 "%PYTHON_INSTALLER%" "%PYTHON_SHA256%"
    if errorlevel 1 (
        echo     Downloaded file failed checksum verification - aborting.
        del /f /q "%PYTHON_INSTALLER%" >nul 2>&1
        exit /b 1
    )
)

echo     Installing Python %PYTHON_VERSION% silently (per-user)...
"%PYTHON_INSTALLER%" /quiet InstallAllUsers=0 InstallLauncherAllUsers=0 PrependPath=1 Include_test=0 Include_doc=0 Include_launcher=1 Shortcuts=0 AssociateFiles=0 TargetDir="%PYTHON_INSTALL_DIR%"
if errorlevel 1 ( exit /b 1 )
if not exist "%PYTHON_INSTALL_DIR%\python.exe" ( exit /b 1 )
set "PATH=%PYTHON_INSTALL_DIR%;%PATH%"
exit /b 0

:: Verify a downloaded file's SHA256 against an expected value.
:verify_sha256
set "VERIFY_FILE=%~1"
set "EXPECTED_HASH=%~2"
if not exist "%VERIFY_FILE%" ( exit /b 1 )
powershell.exe -NoProfile -NonInteractive -Command "if ((Get-FileHash -LiteralPath $env:VERIFY_FILE -Algorithm SHA256).Hash.ToLower() -ne $env:EXPECTED_HASH.ToLower()) { exit 1 }" 2>nul
if errorlevel 1 ( exit /b 1 )
exit /b 0

:: Download helper - tries curl (bundled with Win10+), falls back to PowerShell.
:download
set "DL_URL=%~1"
set "DL_OUT=%~2"
curl.exe -fSL --max-time 300 --retry 3 -o "%DL_OUT%" "%DL_URL%" >nul 2>&1
if not errorlevel 1 ( exit /b 0 )
powershell.exe -NoProfile -NonInteractive -Command "Invoke-WebRequest -UseBasicParsing -TimeoutSec 300 -Uri $env:DL_URL -OutFile $env:DL_OUT" >nul 2>&1
if not errorlevel 1 ( exit /b 0 )
exit /b 1