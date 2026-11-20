@echo off
setlocal EnableDelayedExpansion
cd /d "%~dp0"

echo.
echo  gh-install setup
echo  =================
echo.

set "MISSING=0"

where python >nul 2>&1
if errorlevel 1 (
  echo  [X] Python 3 not found on PATH.
  echo      Install: https://www.python.org/downloads/
  echo      Enable "Add python.exe to PATH" during setup.
  set "MISSING=1"
) else (
  for /f "delims=" %%v in ('python --version 2^>^&1') do echo  [OK] %%v
)

where git >nul 2>&1
if errorlevel 1 (
  echo  [X] git not found on PATH.
  echo      Install: https://git-scm.com/download/win
  set "MISSING=1"
) else (
  for /f "delims=" %%v in ('git --version 2^>^&1') do echo  [OK] %%v
)

if "%MISSING%"=="1" (
  echo.
  echo  Fix the missing tools, then run setup.cmd again.
  exit /b 1
)

if not exist "%~dp0hosts.json" (
  if exist "%~dp0hosts.example.json" (
    copy /y "%~dp0hosts.example.json" "%~dp0hosts.json" >nul
    echo  [OK] Created hosts.json from hosts.example.json
  ) else (
    echo  [!] hosts.example.json missing; run gh-install once to seed config.
  )
) else (
  echo  [OK] hosts.json already exists
)

set "TOOL_DIR=%~dp0"
if "%TOOL_DIR:~-1%"=="\" set "TOOL_DIR=%TOOL_DIR:~0,-1%"

echo.
set /p ADD_PATH="  Add this folder to your user PATH so you can run gh-install anywhere? [Y/n]: "
if /i "!ADD_PATH!"=="" set "ADD_PATH=Y"
if /i "!ADD_PATH!"=="Y" (
  for /f "tokens=2*" %%a in ('reg query "HKCU\Environment" /v Path 2^>nul') do set "USER_PATH=%%b"
  if not defined USER_PATH set "USER_PATH="
  echo ;"%USER_PATH%" | find /i /c ";%TOOL_DIR%;" >nul
  if errorlevel 1 (
    echo "%USER_PATH%" | find /i /c "%TOOL_DIR%" >nul
    if errorlevel 1 (
      if defined USER_PATH (
        set "NEW_PATH=%USER_PATH%;%TOOL_DIR%"
      ) else (
        set "NEW_PATH=%TOOL_DIR%"
      )
      setx PATH "!NEW_PATH!" >nul
      echo  [OK] PATH updated. Open a new terminal for it to apply.
    ) else (
      echo  [OK] Folder already on PATH
    )
  ) else (
    echo  [OK] Folder already on PATH
  )
) else (
  echo  Skipped PATH. Run from this folder: gh-install.cmd ...
)

echo.
echo  Where to run installs
echo  ---------------------
echo   Setup (this script):  %TOOL_DIR%
echo   Installs:             Any new PowerShell, cmd, or Windows Terminal
echo   Not:                  Inside Claude, Grok, ChatGPT, or DeepSeek chat windows
echo.
echo  Next steps
echo  ----------
echo   1. gh-install --scan
echo   2. gh-install --help-hosts
echo   3. gh-install --dry-run ^<paste GitHub URL^>
echo   4. gh-install ^<paste GitHub URL^>   ^(detected apps only in menu^)
echo.
exit /b 0