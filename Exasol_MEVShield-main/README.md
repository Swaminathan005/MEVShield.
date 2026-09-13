# 🛡️ Exasol MEVShield

> **In-Database Real-Time MEV Sandwich Attack Detection & Exploitation Prevention Engine**  
> Powered by **Exasol In-Memory Columnar Database**, GPU-Accelerated Machine Learning, and On-Chain Telemetry.

[![Exasol](https://img.shields.io/badge/Exasol-In--Memory%20Analytics-blue?style=for-the-badge&logo=database)](https://www.exasol.com/)
[![Dataset](https://img.shields.io/badge/Dataset-3.4M%20Transactions-orange?style=for-the-badge)](https://dune.com/)
[![Model](https://img.shields.io/badge/Champion%20Model-XGBoost%20GPU-green?style=for-the-badge)](https://xgboost.readthedocs.io/)
[![PR-AUC](https://img.shields.io/badge/PR--AUC-0.8591-brightgreen?style=for-the-badge)](#benchmark-results)
[![Precision](https://img.shields.io/badge/Precision-90.09%25-success?style=for-the-badge)](#benchmark-results)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python)](https://python.org)

---

## 📌 Executive Summary

**Exasol MEVShield** is an industrial-grade machine learning and in-memory analytical solution engineered to detect, classify, and mitigate **Maximal Extractable Value (MEV) Sandwich Attacks** on the Ethereum blockchain.

Sandwich attacks occur when malicious searchers front-run and back-run an unsuspecting victim trader's decentralized exchange (DEX) transaction, extracting slippage profit and degrading trade execution. Detecting these attacks in real time requires processing massive transaction volumes, calculating spatial and temporal liquidity pool metrics, and scoring probabilistic models within milliseconds.

By combining **Exasol's ultra-low latency in-memory columnar database** with **GPU-accelerated gradient boosting**, MEVShield achieves:
- ⚡ **Ingestion & Data Sanitization**: 3,395,078 transactions ingested in **15.86 seconds** (~214,000 rows/sec).
- 🧠 **In-Database Feature Engineering**: Logarithmic scaling and temporal windowing calculated directly in Exasol in **49.36 seconds**.
- 🎯 **High-Precision ML Classification**: **0.8591 PR-AUC**, **0.9660 ROC-AUC**, and **90.09% Precision** on imbalanced data (16.17:1 ratio).
- 🔄 **Bidirectional In-Memory Writeback**: 611,106 batch predictions written back into Exasol in **3.23 seconds**.
- 🚀 **Zero-Leakage Holdout Stream**: 339,501 unseen holdout transactions exported for live frontend simulation.

---

## 📊 Project Progress & Status Tracker

| Phase | Description | Key Deliverables & Achievements | Status |
|---|---|---|:---:|
| **Phase 0** | **Dataset Curation & Windowing** | Sourced Dune Analytics datasets (5M trades + 4M telemetry + 871K labels). Formatted pool-specific spatial windows, resolved isolated trade boundaries with `-1` sentinels, and generated `sandwich_4M_cleaned_final.csv` (1.08 GB, 3,395,078 rows). | ✅ **Completed** |
| **Phase 1** | **In-Database Ingestion & Preprocessing** | Created `MEV_SHIELD` schema. Ingested 3.4M records into `RAW_SANDWICH_DATA` (15.86s). Sanitized nulls, gas metrics, and non-ASCII characters into `PREPROCESSED_SANDWICH_DATA`. Automated via [`src/01_clean_preprocess.py`](file:///c:/Users/lavan/OneDrive/Desktop/Exasol_MEVShield/src/01_clean_preprocess.py). | ✅ **Completed** |
| **Phase 2** | **In-Memory SQL EDA** | Analyzed 136,088 blocks in 10.90s via Exasol SQL. Profiled 16.17:1 class imbalance (197,690 victims, 5.82%), gas auction spikes, pool trade gaps, and top MEV searcher contracts. Automated via [`src/02_eda.py`](file:///c:/Users/lavan/OneDrive/Desktop/Exasol_MEVShield/src/02_eda.py). | ✅ **Completed** |
| **Phase 3** | **Feature Engineering & Split** | Executed in-database logarithmic scaling `LN(GREATEST(col, 0) + 1)` on WEI/USD values. Enforced strict chronological block split into `SANDWICH_TRAIN` (72%), `SANDWICH_TEST` (18%), and `SANDWICH_LIVE_DEMO` (10%). Exported [`data/live_demo_holdout.csv`](file:///c:/Users/lavan/OneDrive/Desktop/Exasol_MEVShield/data/live_demo_holdout.csv) (117 MB). Automated via [`src/03_feature_engineering_and_split.py`](file:///c:/Users/lavan/OneDrive/Desktop/Exasol_MEVShield/src/03_feature_engineering_and_split.py). | ✅ **Completed** |
| **Phase 4** | **ML Benchmark & Writeback** | Trained XGBoost (GPU), LightGBM (CPU), CatBoost (GPU). Selected **XGBoost Champion** (PR-AUC 0.8591, Precision 90.09%). Serialized [`models/champion_mev_model.joblib`](file:///c:/Users/lavan/OneDrive/Desktop/Exasol_MEVShield/models/champion_mev_model.joblib) (1.74 MB). Wrote 611,106 predictions back to Exasol in 3.23s. Automated via [`src/04_train_evaluate.py`](file:///c:/Users/lavan/OneDrive/Desktop/Exasol_MEVShield/src/04_train_evaluate.py). | ✅ **Completed** |
| **Phase 5** | **Frontend Integration & Live Stream** | Connect live holdout stream (`live_demo_holdout.csv`) to a real-time monitoring dashboard, querying historical pool metrics from Exasol and alerting on sandwich attacks. | 🔄 **In Handoff** |

---

## 🏗️ System Architecture

```
                                    ┌──────────────────────────────────────────────┐
                                    │          ETHEREUM ON-CHAIN MEMPOOL           │
                                    │    (Dune Analytics: 3.4M DEX Transactions)   │
                                    └──────────────────────┬───────────────────────┘
                                                           │
                                                           ▼
                             ┌───────────────────────────────────────────────────────────┐
                             │               EXASOL IN-MEMORY DATABASE                   │
                             │                  (Docker Container :8563)                 │
                             ├───────────────────────────────────────────────────────────┤
                             │ • MEV_SHIELD.RAW_SANDWICH_DATA (3.4M records)             │
                             │ • MEV_SHIELD.PREPROCESSED_SANDWICH_DATA (Cleaned)         │
                             │ • MEV_SHIELD.SANDWICH_FEATURES (Log Scaling & Bounds)     │
                             │ • Strict Chronological Block Splitting:                   │
                             │    ├── SANDWICH_TRAIN (2,444,471 rows - 72%)              │
                             │    ├── SANDWICH_TEST  (  611,106 rows - 18%)              │
                             │    └── SANDWICH_LIVE_DEMO (339,501 rows - 10%)            │
                             │ • MEV_SHIELD.SANDWICH_PREDICTIONS (Writeback results)     │
                             └─────────────┬───────────────────────────────▲─────────────┘
                                           │                               │
                      pyexasol             │ Fast Chunked                  │ 3.23s Bulk
                      Connection           │ In-Memory Read                │ Parallel Write
                                           ▼                               │
                             ┌───────────────────────────────┐             │
                             │   PYTHON ORCHESTRATION LAYER  │             │
                             │     (.venv / CUDA Enabled)    │             │
                             ├───────────────────────────────┤             │
                             │ • 01_clean_preprocess.py      │             │
                             │ • 02_eda.py                   │             │
                             │ • 03_feature_engineering.py   │             │
                             │ • 04_train_evaluate.py        ├─────────────┘
                             └─────────────┬─────────────────┘
                                           │
                        ┌──────────────────┴──────────────────┐
                        ▼                                     ▼
      ┌─────────────────────────────────┐   ┌───────────────────────────────────┐
      │      GPU-ACCELERATED ML CORE    │   │         SERIALIZED ARTIFACTS      │
      ├─────────────────────────────────┤   ├───────────────────────────────────┤
      │ • XGBoost (CUDA 13.1 GPU Engine)│   │ • models/champion_mev_model.joblib│
      │ • LightGBM (Histogram Engine)   │   │ • data/live_demo_holdout.csv      │
      │ • CatBoost (Symmetric Trees GPU)│   │ • MODEL_BENCHMARK_REPORT.md       │
      │ • PR-AUC & Cost-Sensitive Loss  │   │ • END_TO_END_TECHNICAL_REPORT.md  │
      └─────────────────────────────────┘   └─────────────────┬─────────────────┘
                                                              │
                                                              ▼
                                            ┌───────────────────────────────────┐
                                            │      LIVE FRONTEND / DASHBOARD    │
                                            │  (Real-Time MEV Attack Shield)    │
                                            └───────────────────────────────────┘
```

---

## 🏆 Model Benchmark Results

Models were evaluated on **611,106 unseen chronological test transactions** under severe class imbalance (**16.17:1** negative to positive ratio). Because false positives block legitimate trades and false negatives allow trader funds to be drained, **PR-AUC** and **Precision** were the primary evaluation metrics.

| Rank | Model Architecture | Hardware | ROC-AUC | PR-AUC | Optimal Threshold | Precision | Recall | F1-Score | Train Time |
|:---:|---|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| 🥇 | **XGBoost (Champion)** | **GPU (CUDA)** | **0.9660** | **0.8591** | **0.86** | **90.09%** | **72.99%** | **0.8064** | **9.87s** |
| 🥈 | LightGBM | CPU (16 Thr) | 0.9657 | 0.8582 | 0.84 | 88.67% | 74.07% | 0.8072 | 10.97s |
| 🥉 | CatBoost | GPU (CUDA) | 0.9634 | 0.8488 | 0.83 | 87.20% | 74.31% | 0.8024 | 54.61s |

### Why XGBoost Won:
1. **Highest PR-AUC (0.8591)**: Dominates Precision-Recall space under extreme imbalance.
2. **Superior Precision (90.09%)**: At the optimal decision boundary of **0.86**, 9 out of 10 flagged transactions are genuine sandwich attacks, minimizing false alarms for DEX users.
3. **Lightning Fast Training**: 2.44 million rows trained in just **9.87 seconds** on GPU.

---

## 🚀 Judge's Evaluation Guide (Choose Your Fast-Track)

We respect your time. Depending on how much time you have to review, choose the path that best suits your evaluation workflow:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       CHOOSE YOUR EVALUATION PATH                           │
├─────────────────────────────────────────────────────────────────────────────┤
│ ⚡ PATH 1: 5-Second Rapid Verification (Zero Setup / Instant Live Metrics)   │
│    👉 Double-click `run_judge_eval.bat` (or run `python judge_quick_eval.py`) │
│                                                                             │
│ 🔬 PATH 2: Full End-to-End Pipeline Reproduction (3.4M Ingest & ML Train)   │
│    👉 Double-click `run_all_pipeline.bat`                                    │
│                                                                             │
│ 🔎 PATH 3: Direct In-Database SQL Audit (EXAplus / DBeaver Queries)         │
│    👉 Copy-paste pre-written verification queries into your database client │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

### ⚡ Path 1: 5-Second Rapid Evaluation (Zero Configuration)
**Target:** Judges with 2–3 minutes who want immediate proof of model performance, metrics, and live attack detection without waiting for database loads.

Simply run:
```cmd
run_judge_eval.bat
```
*(Or on Linux/macOS: `python judge_quick_eval.py`)*

#### What this does automatically in ~2 seconds:
1. **Auto-Detects Exasol**: Checks live database connectivity and prints row counts of all 6 in-memory tables. *(Gracefully skips if Docker is offline)*.
2. **Loads Pre-Trained Champion Model**: Reads [`models/champion_mev_model.joblib`](file:///c:/Users/lavan/OneDrive/Desktop/Exasol_MEVShield/models/champion_mev_model.joblib) (1.74 MB).
3. **Streams Unseen Holdout Data**: Ingests 50,000 holdout transactions in 0.3s and scores them at **>450,000 tx/sec**.
4. **Validates Benchmark Metrics**: Displays live ROC-AUC (`0.9622`), PR-AUC (`0.8604`), Precision (`92.9%`), Recall (`72.0%`), and Confusion Matrix.
5. **Emits Live Attack Alerts**: Displays sample flagged Ethereum transactions with tx hashes, gas auction telemetry, and simulated DEX slippage mitigation.

---

### 🔬 Path 2: Full End-to-End Pipeline Reproduction
**Target:** Technical judges who want to audit the entire ETL, in-database feature engineering, and GPU training pipeline from scratch.

#### Prerequisites:
- Docker Desktop running with Exasol container on `localhost:8563`.
- Python 3.10+ (Dependencies auto-install upon first run via `pip install -r requirements.txt`).

#### 1-Click Master Execution:
Double-click or run:
```cmd
run_all_pipeline.bat
```
*(Executes all 4 stages sequentially, displaying timings and Exasol execution logs)*

#### Modular Stage Execution:
| Step | 1-Click Batch Runner | Direct Python Command | What It Does | Runtime |
|---|---|---|---|:---:|
| **Step 1** | `run_01_ingest_and_clean.bat` | `python src/01_clean_preprocess.py` | Ingests 3.4M rows into Exasol & sanitizes nulls/gas metrics | ~16s |
| **Step 2** | `run_02_eda.bat` | `python src/02_eda.py` | Computes in-memory class distributions & gas spikes in Exasol | ~11s |
| **Step 3** | `run_03_features_and_split.bat` | `python src/03_feature_engineering_and_split.py` | In-memory log scaling & strict chronological block split | ~50s |
| **Step 4** | `run_04_train_evaluate.bat` | `python src/04_train_evaluate.py` | Trains XGBoost GPU, LightGBM, CatBoost & writes back to Exasol | ~85s |

---

### 🔎 Path 3: Direct In-Database SQL Audit (For Database Judges)
Judges can connect to the running Exasol instance using **EXAplus**, **DBeaver**, or any JDBC/ODBC client (`localhost:8563`, user `sys`, schema `MEV_SHIELD`) to audit in-database tables and execution results:

### 1. Verify Table Ingestion & Row Counts
```sql
OPEN SCHEMA MEV_SHIELD;

-- Confirm all tables and exact row allocations
SELECT 'RAW_SANDWICH_DATA' AS TABLE_NAME, COUNT(*) AS ROW_COUNT FROM RAW_SANDWICH_DATA
UNION ALL
SELECT 'PREPROCESSED_SANDWICH_DATA', COUNT(*) FROM PREPROCESSED_SANDWICH_DATA
UNION ALL
SELECT 'SANDWICH_FEATURES', COUNT(*) FROM SANDWICH_FEATURES
UNION ALL
SELECT 'SANDWICH_TRAIN', COUNT(*) FROM SANDWICH_TRAIN
UNION ALL
SELECT 'SANDWICH_TEST', COUNT(*) FROM SANDWICH_TEST
UNION ALL
SELECT 'SANDWICH_LIVE_DEMO', COUNT(*) FROM SANDWICH_LIVE_DEMO
UNION ALL
SELECT 'SANDWICH_PREDICTIONS', COUNT(*) FROM SANDWICH_PREDICTIONS;
```
**Expected Row Counts:**
- `PREPROCESSED_SANDWICH_DATA`: **3,395,078**
- `SANDWICH_TRAIN`: **2,444,471** (72.0%)
- `SANDWICH_TEST`: **611,106** (18.0%)
- `SANDWICH_LIVE_DEMO`: **339,501** (10.0%)
- `SANDWICH_PREDICTIONS`: **611,106** (100% of test set scored)

---

### 2. Verify Zero Data Leakage Across Chronological Splits
Confirm that the block numbers across Train, Test, and Live Demo are strictly monotonic:
```sql
SELECT 
    'TRAIN' AS SPLIT, MIN(BLOCK_NUMBER) AS MIN_BLOCK, MAX(BLOCK_NUMBER) AS MAX_BLOCK 
FROM SANDWICH_TRAIN
UNION ALL
SELECT 
    'TEST' AS SPLIT, MIN(BLOCK_NUMBER) AS MIN_BLOCK, MAX(BLOCK_NUMBER) AS MAX_BLOCK 
FROM SANDWICH_TEST
UNION ALL
SELECT 
    'LIVE_DEMO' AS SPLIT, MIN(BLOCK_NUMBER) AS MIN_BLOCK, MAX(BLOCK_NUMBER) AS MAX_BLOCK 
FROM SANDWICH_LIVE_DEMO
ORDER BY MIN_BLOCK;
```
*Verification: The maximum block of Train (`17,999,999`) is strictly lower than the minimum block of Test (`18,000,000`), and Test's maximum is strictly lower than Live Demo's minimum.*

---

### 3. Verify Champion Model Predictions Written to Exasol
Inspect the live predictions written back by Python into Exasol:
```sql
SELECT 
    PREDICTED_LABEL,
    COUNT(*) AS TOTAL_PREDICTED,
    ROUND(AVG(PREDICTION_PROBABILITY), 4) AS AVG_PROBABILITY,
    ROUND(MIN(PREDICTION_PROBABILITY), 4) AS MIN_PROBABILITY,
    ROUND(MAX(PREDICTION_PROBABILITY), 4) AS MAX_PROBABILITY
FROM MEV_SHIELD.SANDWICH_PREDICTIONS
GROUP BY PREDICTED_LABEL;
```

---

### 4. Inspect High-Risk Sandwich Attack Detections
Examine specific test transactions flagged as attacks by the champion model:
```sql
SELECT 
    P.TX_HASH,
    P.BLOCK_NUMBER,
    P.PREDICTION_PROBABILITY,
    F.LOG_AMOUNT_USD,
    F.LOG_GAS_PRICE,
    F.PREVIOUS_GAP,
    F.NEXT_GAP,
    F.LABEL AS GROUND_TRUTH
FROM MEV_SHIELD.SANDWICH_PREDICTIONS P
JOIN MEV_SHIELD.SANDWICH_FEATURES F ON P.TX_HASH = F.TX_HASH
WHERE P.PREDICTED_LABEL = 1
ORDER BY P.PREDICTION_PROBABILITY DESC
LIMIT 10;
```

---

## 💡 Evaluation Tips & Key Highlights for Judges

1. **True In-Database Analytics**:
   Notice that filtering, null replacements, boundary handling, and logarithmic transformations are not handled by bottlenecked Python loops; they are compiled and executed directly inside Exasol's in-memory columnar engine across millions of rows.
2. **Realistic Chronological Splitting**:
   Standard random train/test splits cause severe temporal leakage in blockchain mempools (where future gas prices leak into past trades). We strictly split on block heights so models are evaluated on true future conditions.
3. **Extreme Imbalance Handling**:
   Sandwich victims make up only **5.82%** of the dataset. Using `scale_pos_weight` and threshold optimization on Precision-Recall curves yielded a model with **90.09% precision**, preventing costly false positives in DeFi trading environments.
4. **Sub-4-Second Batch Writeback**:
   Demonstrates how Exasol serves as both the feature store and the operational inference store, ingesting 611,106 predictions from Python back into Exasol in just **3.23 seconds**.

---

## 📁 Repository Structure

```
Exasol_MEVShield/
├── .env                                # Exasol DSN, credentials & schema config
├── .gitignore                          # Excludes venv, cache, raw gigabyte CSVs
├── requirements.txt                    # Verified production dependencies
├── README.md                           # Master project guide & judge walkthrough
├── MODEL_BENCHMARK_REPORT.md           # Detailed ML benchmark report & curves
├── END_TO_END_TECHNICAL_REPORT.md      # Comprehensive engineering architecture report
│
├── run_judge_eval.bat                # ⚡ 1-Click 5-second rapid evaluation for judges
├── judge_quick_eval.py                 # Instant holdout evaluator & live alert inspector
├── run_all_pipeline.bat                # ⚡ 1-Click master runner for all 4 phases
├── run_01_ingest_and_clean.bat         # 1-Click Step 1 runner
├── run_02_eda.bat                      # 1-Click Step 2 runner
├── run_03_features_and_split.bat       # 1-Click Step 3 runner
├── run_04_train_evaluate.bat           # 1-Click Step 4 runner
│
├── data/
│   ├── holdout_sample_10k.csv          # 10k Holdout sample for instant GitHub clone eval (3.6 MB)
│   ├── live_demo_holdout.csv           # 10% Unseen holdout set for frontend stream (117 MB)
│   └── sandwich_4M_cleaned_final.csv   # Master 3.4M raw transaction dataset (1.08 GB)
│
├── models/
│   └── champion_mev_model.joblib       # Persisted Champion XGBoost Model artifact (1.74 MB)
│
├── sql/
│   └── 01_raw_schema.sql               # Production Exasol DDL for 3.4M raw transaction schema
│
├── src/
│   ├── db.py                           # Reusable Exasol TLS connection factory
│   ├── 01_clean_preprocess.py          # Phase 1: In-database table creation & cleaning
│   ├── 02_eda.py                       # Phase 2: In-database exploratory data analysis
│   ├── 03_feature_engineering_and_split.py # Phase 3: SQL log scaling & block split
│   └── 04_train_evaluate.py            # Phase 4: XGBoost, LightGBM, CatBoost & writeback
│
└── tests/
    └── COMMANDS.md                     # Quick reference verification SQL cheat-sheet
```

---

## 🤝 Teammate & Frontend Handoff Contract

For team members building the UI/UX frontend or streaming dashboard:
1. **Model Artifact**: [`models/champion_mev_model.joblib`](file:///c:/Users/lavan/OneDrive/Desktop/Exasol_MEVShield/models/champion_mev_model.joblib) contains the pre-fitted XGBoost model and pre-configured classification threshold (`0.86`).
2. **Simulation Holdout Data**: [`data/live_demo_holdout.csv`](file:///c:/Users/lavan/OneDrive/Desktop/Exasol_MEVShield/data/live_demo_holdout.csv) (339,501 transactions) represents chronologically unseen future transactions. Stream lines row-by-row into the model to simulate real-time mempool inspection and trigger live UI alerts.
3. **No Database Dependencies for Frontend**: The frontend demo can run completely standalone by scoring rows from `live_demo_holdout.csv` against `champion_mev_model.joblib` using lightweight Python or a REST microservice.

---

## 📜 License
This project was developed for the Exasol Hackathon Challenge. Open-source under the [MIT License](LICENSE).
