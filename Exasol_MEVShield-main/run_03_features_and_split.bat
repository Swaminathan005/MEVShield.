@echo off
title Exasol MEVShield - Step 3: Feature Engineering & Split
cd /d "%~dp0"
echo ===============================================================================
echo [STEP 3] IN-DATABASE FEATURE ENGINEERING & 3-WAY CHRONOLOGICAL SPLIT
echo ===============================================================================
.venv\Scripts\python.exe src\03_feature_engineering_and_split.py
pause
