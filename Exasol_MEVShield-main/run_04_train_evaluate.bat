@echo off
title Exasol MEVShield - Step 4: ML Benchmark & Exasol Writeback
cd /d "%~dp0"
echo ===============================================================================
echo [STEP 4] ML BENCHMARK (XGBoost GPU, LightGBM, CatBoost) & PREDICTION WRITEBACK
echo ===============================================================================
.venv\Scripts\python.exe src\04_train_evaluate.py
pause
