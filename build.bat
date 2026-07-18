@echo off
setlocal
REM ============================================================
REM  InternetGuard - Robust Nuitka build script (root)
REM  Run from a regular (non-elevated) Windows shell, from inside
REM  the internetguard\ project folder.
REM      pip install -r requirements.txt
REM      pip install nuitka
REM ============================================================

if not exist "main.py" (
  echo [ERROR] main.py not found in the current directory.
  echo         Run this script from inside the internetguard\ folder.
  exit /b 1
)
if not exist "icon.ico" (
  echo [ERROR] icon.ico not found in the current directory.
  exit /b 1
)

where python >nul 2>nul
if errorlevel 1 (
  echo [ERROR] python is not on PATH.
  exit /b 1
)

python -c "import nuitka" 2>nul
if errorlevel 1 (
  echo [ERROR] nuitka is not installed. Run: pip install nuitka
  exit /b 1
)

python -c "import PyQt6" 2>nul
if errorlevel 1 (
  echo [ERROR] PyQt6 is not installed. Run: pip install -r requirements.txt
  exit /b 1
)

REM Single-line invocation on purpose -- avoids any chance of a caret
REM line-continuation silently breaking due to trailing whitespace.
set NUITKA_ARGS=--standalone --onefile --enable-plugin=pyqt6 --windows-console-mode=disable --windows-icon-from-ico=icon.ico --company-name="Dain Corp" --product-name="InternetGuard" --file-version=2026.1.0.0 --product-version=2026.1.0.0 --file-description="InternetGuard - internet access gate" --copyright="Copyright (c) 2026 Dain Corp" --include-data-files=icon.ico=icon.ico --include-data-files=icon.png=icon.png --output-filename=InternetGuard.exe --output-dir=dist main.py

echo Running: python -m nuitka %NUITKA_ARGS%
python -m nuitka %NUITKA_ARGS%

if errorlevel 1 (
  echo.
  echo [ERROR] Nuitka build failed -- see output above for the actual cause.
  echo         Common causes: no C compiler available and no internet
  echo         access for Nuitka to fetch MinGW; no internet access for
  echo         the --onefile bootstrap/zstandard download on first run.
  exit /b 1
)

if not exist "dist\InternetGuard.exe" (
  echo [ERROR] Build reported success but dist\InternetGuard.exe is missing.
  exit /b 1
)

echo.
echo Build finished. Output: dist\InternetGuard.exe
echo Next: run installer.iss with Inno Setup to produce the installer.