@echo off
title Exasol MEVShield - Rapid 5-Second Judge Evaluation
cd /d "%~dp0"
echo ===============================================================================
echo            EXASOL MEVSHIELD: RAPID JUDGE EVALUATION RUNNER (5 SECONDS)
echo ===============================================================================
echo Checking Python environment...
echo.

:: 1. Check if local virtual environment exists
if exist ".venv\Scripts\python.exe" (
    set "PY_CMD=.venv\Scripts\python.exe"
    goto RUN_EVAL
)

:: 2. If .venv doesn't exist, try to create it using python or py
echo [SETUP] Virtual environment (.venv) not found. Attempting auto-creation...
where python >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    python -m venv .venv
    if exist ".venv\Scripts\python.exe" (
        echo [SETUP] Installing required dependencies into .venv...
        .venv\Scripts\python.exe -m pip install -r requirements.txt
        set "PY_CMD=.venv\Scripts\python.exe"
        goto RUN_EVAL
    )
    set "PY_CMD=python"
    goto RUN_EVAL
)

where py >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    py -3 -m venv .venv
    if exist ".venv\Scripts\python.exe" (
        echo [SETUP] Installing required dependencies into .venv...
        .venv\Scripts\python.exe -m pip install -r requirements.txt
        set "PY_CMD=.venv\Scripts\python.exe"
        goto RUN_EVAL
    )
    set "PY_CMD=py -3"
    goto RUN_EVAL
)

echo [ERROR] Neither 'python' nor 'py' was found in your PATH!
echo Please install Python 3.10+ or run with an active Python environment.
pause
exit /b 1

:RUN_EVAL
echo [+] Running evaluator using: %PY_CMD%
%PY_CMD% judge_quick_eval.py

echo.
pause
