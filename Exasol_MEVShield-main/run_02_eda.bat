@echo off
title Exasol MEVShield - Step 2: Exploratory Data Analysis (EDA)
cd /d "%~dp0"
echo ===============================================================================
echo [STEP 2] IN-DATABASE EXPLORATORY DATA ANALYSIS (EDA)
echo ===============================================================================
.venv\Scripts\python.exe src\02_eda.py
pause
