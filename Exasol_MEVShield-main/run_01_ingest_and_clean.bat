@echo off
title Exasol MEVShield - Step 1: Ingestion & Data Cleaning
cd /d "%~dp0"
echo ===============================================================================
echo [STEP 1] INGESTION & DATA CLEANING IN EXASOL
echo ===============================================================================
.venv\Scripts\python.exe src\01_clean_preprocess.py
pause
