@echo off
REM Run the expense tracker on Windows and free the port on exit.
REM Stop with Ctrl+C — the port is released afterwards.

if "%PORT%"=="" set PORT=8001
if "%CONDA_ENV%"=="" set CONDA_ENV=expense_tracker

call conda activate %CONDA_ENV%

echo Starting expense tracker on http://localhost:%PORT% (Ctrl+C to stop)
python main.py

REM After Python exits (e.g. Ctrl+C), kill anything still on the port.
echo Freeing port %PORT%...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :%PORT% ^| findstr LISTENING') do taskkill /F /PID %%a >nul 2>&1