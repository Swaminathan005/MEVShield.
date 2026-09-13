@echo off
title Exasol MEVShield - Complete End-to-End Pipeline
cd /d "%~dp0"
echo ===============================================================================
echo                 EXASOL MEVSHIELD: COMPLETE REPRODUCIBILITY RUNNER
echo ===============================================================================
echo This script runs the complete Exasol in-database pipeline from raw dataset
echo ingestion to in-memory EDA, chronological splitting, GPU ML training, and writeback.
echo.

:: 1. Check Virtual Environment
if not exist ".venv\Scripts\python.exe" (
    echo [SETUP] Python virtual environment not found. Creating .venv ...
    python -m venv .venv
    echo [SETUP] Installing core dependencies ...
    .venv\Scripts\python.exe -m pip install -r requirements.txt
)

:: 2. Run Step 1: Ingest & Clean
echo.
echo ===============================================================================
echo [STEP 1/4] INGESTION & DATA CLEANING IN EXASOL
echo ===============================================================================
.venv\Scripts\python.exe src\01_clean_preprocess.py
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Step 1 failed!
    pause
    exit /b %ERRORLEVEL%
)

:: 3. Run Step 2: In-Database EDA
echo.
echo ===============================================================================
echo [STEP 2/4] IN-DATABASE EXPLORATORY DATA ANALYSIS (EDA)
echo ===============================================================================
.venv\Scripts\python.exe src\02_eda.py
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Step 2 failed!
    pause
    exit /b %ERRORLEVEL%
)

:: 4. Run Step 3: Feature Engineering & Chronological Split
echo.
echo ===============================================================================
echo [STEP 3/4] IN-DATABASE FEATURE ENGINEERING & 3-WAY CHRONOLOGICAL SPLIT
echo ===============================================================================
.venv\Scripts\python.exe src\03_feature_engineering_and_split.py
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Step 3 failed!
    pause
    exit /b %ERRORLEVEL%
)

:: 5. Run Step 4: ML Benchmark & Exasol Writeback
echo.
echo ===============================================================================
echo [STEP 4/4] ML BENCHMARK (XGBoost GPU, LightGBM, CatBoost) & EXASOL WRITEBACK
echo ===============================================================================
.venv\Scripts\python.exe src\04_train_evaluate.py
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Step 4 failed!
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo ===============================================================================
echo [CONGRATULATIONS] ENTIRE EXASOL MEVSHIELD PIPELINE COMPLETED SUCCESSFULLY!
echo - Dataset Ingested & Cleaned: MEV_SHIELD.PREPROCESSED_SANDWICH_DATA
echo - EDA Statistics Profiled:    3.4M records across 136,088 blocks
echo - Holdout Exported:           data\live_demo_holdout.csv (117 MB)
echo - Champion Model Serialized:  models\champion_mev_model.joblib (1.74 MB)
echo - Predictions Written Back:   MEV_SHIELD.SANDWICH_PREDICTIONS (611,106 rows)
echo - Benchmark Report Generated: MODEL_BENCHMARK_REPORT.md
echo ===============================================================================
pause
