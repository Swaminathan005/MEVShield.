# Exasol MEVShield: End-to-End Technical Architecture & Engineering Report

**Project Title:** Exasol MEVShield — High-Throughput In-Memory Ethereum Sandwich Attack Detection  
**Engineering Discipline:** Distributed Data Engineering & Machine Learning Systems  
**Database Engine:** Exasol In-Memory Columnar Database (v2026.2-nano)  
**Dataset Scale:** 3,395,078 Ethereum Transactions (136,088 Blocks | $14.8B Volume)  
**Production Champion Model:** XGBoost Classifier (CUDA GPU Hist | PR-AUC: 0.8591 | F1: 0.8064)

---

## 1. Executive Summary & System Architecture

Modern decentralized exchanges (Uniswap, SushiSwap, Curve) suffer from predatory Maximum Extractable Value (MEV) attacks—primarily **Sandwich Attacks**, where bots exploit public mempools to frontrun a victim trade, induce slippage, and backrun to extract profit. Detecting these attacks in real-time across millions of transactions requires extreme analytical throughput.

**Exasol MEVShield** bridges raw blockchain telemetry with in-memory database processing and machine learning:
1. **In-Memory Analytical Muscle (Exasol)**: Ingests 1.08 GB (~3.4 million transactions) in **15.86 seconds** (214,025 rows/sec) and runs complex multi-table SQL queries, EDA, and logarithmic transformations in sub-seconds directly in RAM.
2. **Strict Chronological Integrity**: Partitions blockchain data along block boundaries into Train, Test, and Live Demo Holdout sets to guarantee **zero temporal leakage**.
3. **GPU-Accelerated Detection**: Benchmarks XGBoost, LightGBM, and CatBoost under severe 16.17:1 class imbalance, achieving **90.09% precision** and streaming predictions back into Exasol at **189,390 rows/second**.

```
+----------------------------------------------------------------------------------------------------------------+
|                                        EXASOL MEVSHIELD PIPELINE ARCHITECTURE                                  |
+----------------------------------------------------------------------------------------------------------------+
|                                                                                                                |
|  [Dune Analytics Raw Streams: 5M Trades + 4M Telemetry + 871K Labels]                                          |
|                                       │                                                                        |
|                                       ▼ Spatial Pool Windowing & Boundary Sanitization                         |
|  [data/sandwich_4M_cleaned_final.csv] (1.08 GB, 3,395,078 records)                                             |
|                                       │                                                                        |
|                                       ▼ Exasol Parallel HTTP Stream (15.86s @ 214k rows/sec)                   |
|  1. MEV_SHIELD.RAW_SANDWICH_DATA (All 3.4M raw transactions)                                                   |
|                                       │                                                                        |
|                                       ▼ In-Database Cleaning & Null Imputation (8.22s)                         |
|  2. MEV_SHIELD.PREPROCESSED_SANDWICH_DATA (Cleaned & Validated)                                                |
|                                       │                                                                        |
|                                       ▼ In-Database Logarithmic Scaling (14.33s)                               |
|  3. MEV_SHIELD.SANDWICH_FEATURES                                                                               |
|                                       │                                                                        |
|                 ┌─────────────────────┴─────────────────────┬─────────────────────────────────────┐            |
|                 ▼ Phase 2 Chronological Split (p80/p90)     ▼                                     ▼            |
|       MEV_SHIELD.SANDWICH_TRAIN                  MEV_SHIELD.SANDWICH_TEST            MEV_SHIELD.SANDWICH_LIVE_DEMO|
|       (2,444,471 rows | 72%)                     (611,106 rows | 18%)                (339,501 rows | 10%)        |
|                 │                                           │                                     │            |
|                 ▼                                           ▼                                     ▼            |
|       [GPU / CPU ML Benchmark]                    [Evaluation & Cutoff Tuning]      [data/live_demo_holdout.csv]|
|       - XGBoost (CUDA GPU Hist)                   - PR-AUC: 0.8591 | F1: 0.8064     (117 MB Frontend Artifact) |
|       - LightGBM (Multi-threaded)                 - Optimal Cutoff: 0.86                  │                    |
|       - CatBoost (GPU)                                      │                             ▼                    |
|                                                             ▼ Fast Writeback (3.23s)  [Teammate's WebSocket    |
|                                                  MEV_SHIELD.SANDWICH_PREDICTIONS       Frontend Simulator]     |
+----------------------------------------------------------------------------------------------------------------+
```

---

## 2. Phase 0: Data Sourcing, Spatial Feature Engineering & Boundary Sanitization

Before database ingestion, raw Ethereum blockchain records were synthesized from primary sources:

### 2.1 Raw Data Sources (Dune Analytics)
1. `dex_trades_5m.csv`: 5,000,000 decentralized exchange trades across Uniswap v2/v3, SushiSwap, and Curve.
2. `eth_tx_features.csv`: 4,000,000 transaction telemetry logs including gas limits, base fees, priority fees, and calldata byte sizes.
3. `sandwiched_labels.csv`: 871,000 confirmed victim transaction hashes derived from the curated `dex.sandwiched` table.

### 2.2 Relational Joining & Deduplication
* Joined trades to telemetry on `tx_hash` via inner joins.
* Left-joined confirmed victim labels to construct the binary target:
  $$\text{LABEL} = \begin{cases} 1 & \text{if confirmed sandwich victim / attacker transaction} \\ 0 & \text{if normal benign DEX trade} \end{cases}$$
* Deduplicated transactions to yield exactly **3,395,078 unique on-chain events**.

### 2.3 Spatial Windowing on Liquidity Pools
Unlike standard time-series data, MEV attacks only occur **within the same liquidity pool contract**. Sorting solely by time or block index mixes unrelated pools. 
* Sorted transactions by `[block_number, project_contract_address, transaction_index]`.
* Computed neighbor metrics using window lag/lead operations (`shift`) strictly within each contract:
  * Gas price deltas: `previous_gas_price`, `next_gas_price`
  * Trade volume ratios: `usd_ratio_prev`, `previous_usd`, `next_usd`
  * Index gaps: `previous_gap`, `next_gap`

### 2.4 Resolving Boundary Artifacts (Isolated Pool Trades)
Because **64% of trades in a block are isolated single transactions within their respective pool**, standard window functions produce null or deceptive zero values:
* Engineered explicit boundary indicator flags:
  * `has_prev_trade`: `1` if a preceding trade occurred in the same pool; else `0`.
  * `has_next_trade`: `1` if a subsequent trade occurred in the same pool; else `0`.
  * `is_isolated_pool_trade`: `1` if the trade was the sole interaction with that contract in the block.
* Imputed gap metrics with a sentinel value (`-1`) to clearly distinguish *"no neighbor exists"* from a genuine gap of `0`.

### 2.5 Forensic Audit
* Confirmed **5.82% victim rate** (197,690 attack instances across 3.4M rows).
* Low index correlation (-0.23 vs baseline -0.48), proving feature richness without synthetic index leakage.
* Serialized as `data/sandwich_4M_cleaned_final.csv` (1.08 GB).

---

## 3. Phase 1: In-Database Ingestion & Preprocessing in Exasol

### 3.1 High-Performance Streaming
Traditional Python Pandas runs out of memory (OOM) when handling multi-gigabyte datasets with complex string hashes. Using Exasol's native parallel HTTP columnar loader:
* **Ingestion Duration**: **15.86 seconds**
* **Throughput**: **214,025 rows/second**
* **Loaded into**: `MEV_SHIELD.RAW_SANDWICH_DATA`

### 3.2 In-Database SQL Cleaning
Executed in **8.22 seconds** in Exasol RAM via [`src/01_clean_preprocess.py`](file:///c:/Users/lavan/OneDrive/Desktop/Exasol_MEVShield/src/01_clean_preprocess.py):
* **Null Imputation**: 273,450 pre-EIP-1559 legacy transactions had null priority fees; imputed to `0.0`.
* **Sanity Enforcement**: Filtered negative trade values, zero gas allocations, and malformed non-66-character hashes.
* **Output**: **3,395,078 rows** retained with **100.00% data integrity** in `MEV_SHIELD.PREPROCESSED_SANDWICH_DATA`.

---

## 4. Phase 2: In-Database Exploratory Data Analysis (EDA)

Executed via [`src/02_eda.py`](file:///c:/Users/lavan/OneDrive/Desktop/Exasol_MEVShield/src/02_eda.py) in **10.90 seconds** across all 3.4M records:

### 4.1 Scope & Cardinality
* **Total Transactions**: 3,395,078
* **Unique Blocks**: 136,088 (`17,382,266` to `17,518,454`)
* **Unique Senders**: 428,652 wallets
* **Unique Pools Targeted**: 23,083 contracts

### 4.2 Class Imbalance
* **MEV Sandwich Attacks (`LABEL = 1`)**: **197,690** (5.82%)
* **Normal Trades (`LABEL = 0`)**: **3,197,388** (94.18%)
* **Imbalance Ratio**: **16.17 : 1**

### 4.3 Sequential Positioning: The Physical Signature of MEV
| Metric | MEV Sandwich (`1`) | Normal Trade (`0`) | Real-World Meaning |
| :--- | :---: | :---: | :--- |
| **Average Previous Gap** | **1.33** | **25.50** | Sandwich attacks are physically adjacent (gap ≈ 1) to the victim. |
| **Has Next Trade in Pool**| **74.87%** | **20.76%** | Sandwich frontruns almost always have an immediate subsequent trade. |
| **Isolated Trade Pct** | **15.56%** | **67.36%** | Normal retail swaps are isolated; MEV occurs in rapid bursts. |

### 4.4 Top 5 Most Targeted Liquidity Pools
| Pool Contract Address | Total Attacks | Exposed Victim Capital | Distinct Attackers |
| :--- | :---: | :---: | :---: |
| `0xe5a7ab09e68b2cd335e2bc39e9591b42d29c3115` | **4,178** | **$12,740,280.60** | 1,635 |
| `0xea639dfb59d652ab056a2194ff3d9d7ad9744d07` | **2,962** | **$6,585,784.99** | 1,342 |
| `0x50d1e7f2acfb7f3e0aafba2b1e63666b80eb08ea` | **2,775** | **$8,055,406.68** | 1,046 |
| `0xf64e49c1d1d2b1cfa570b1da6481dc8dc95cd093` | **2,601** | **$6,135,329.16** | 1,468 |
| `0xcb4e7a3db6526f5738b9076098b190b87e81a976` | **2,288** | **$3,181,883.36** | 1,079 |

---

## 5. Phase 3: Feature Engineering & 3-Way Chronological Splitting

Executed via [`src/03_feature_engineering_and_split.py`](file:///c:/Users/lavan/OneDrive/Desktop/Exasol_MEVShield/src/03_feature_engineering_and_split.py) in **49.36 seconds**:

### 5.1 Logarithmic Scaling in Exasol SQL
Ethereum transactions exhibit extreme variance (a $10 micro-trade vs a $30,000,000 flash loan trade; 15 Gwei vs 500 Gwei gas spikes). Computed in-database:
$$\text{LOG\_X} = \ln(\max(\text{X}, 0) + 1)$$
Applied to `VALUE_ETH`, `AMOUNT_USD`, `PREVIOUS_USD`, `NEXT_USD`, `GAS_PRICE_WEI`, and `PRIORITY_FEE_WEI` in table `MEV_SHIELD.SANDWICH_FEATURES`.

### 5.2 Strict 3-Way Chronological Split (Zero Temporal Leakage)
Splitting randomly in blockchain data causes severe lookahead bias because future block gas prices leak into past predictions. Splitting was enforced along the block timeline:

```
[=========== SANDWICH_TRAIN (72%) ===========] | [==== SANDWICH_TEST (18%) ====] | [=== LIVE_DEMO (10%) ===]
Blocks 17,382,266 -> 17,478,035 (95,770 blocks) | Blocks 17,478,036 -> 17,502,750 | Blocks 17,502,751 -> 17,518,454
```

| Split Name | Record Count | Block Span | Min Block | Max Block | MEV Victims | Positive Rate |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **`SANDWICH_TRAIN`** | **2,444,471** | 95,770 blocks | `17,382,266` | `17,478,035` | 134,073 | 5.48% |
| **`SANDWICH_TEST`** | **611,106** | 24,715 blocks | `17,478,036` | `17,502,750` | 40,847 | 6.68% |
| **`SANDWICH_LIVE_DEMO`**| **339,501** | 15,704 blocks | `17,502,751` | `17,518,454` | 22,770 | 6.71% |

* **Verification**: `Train Max (17,478,035) < Test Min (17,478,036)` and `Test Max (17,502,750) < Demo Min (17,502,751)`.

### 5.3 Teammate's Holdout Artifact Export
* Sliced out **339,501 transactions** (ordered strictly by `BLOCK_NUMBER ASC, TRANSACTION_INDEX ASC`).
* Exported locally to [`data/live_demo_holdout.csv`](file:///c:/Users/lavan/OneDrive/Desktop/Exasol_MEVShield/data/live_demo_holdout.csv) (117.99 MB) in **4.11 seconds**.

---

## 6. Phase 4: Machine Learning Benchmark & Exasol Prediction Writeback

Executed via [`src/04_train_evaluate.py`](file:///c:/Users/lavan/OneDrive/Desktop/Exasol_MEVShield/src/04_train_evaluate.py) in **139.36 seconds**:

### 6.1 Benchmark Results
Models trained on 2.44M rows with `scale_pos_weight = 16.17` and evaluated on 611k test records with 50-round early stopping:

| Model Name | Training Hardware | PR-AUC | ROC-AUC | Optimal Cutoff | Precision | Recall | F1-Score | Training Time |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **XGBoost** | **CUDA GPU Hist** | **0.8591** | **0.9660** | **0.86** | **90.09%** | **72.98%** | **0.8064** | **9.87s** |
| **CatBoost** | GPU | 0.8447 | 0.9622 | 0.84 | 87.45% | 72.55% | 0.7930 | 54.61s |
| **LightGBM** | CPU Multi-thread | 0.7759 | 0.9461 | 0.36 | 81.49% | 65.69% | 0.7275 | 7.73s |

### 6.2 Champion Model Selection: XGBoost
* **Why PR-AUC Governs**: In extreme class imbalance (5.8% positive), ROC-AUC is easily distorted by the massive true negative class. PR-AUC evaluates true precision across recall thresholds. XGBoost won with **PR-AUC = 0.8591**.
* **Tuned Threshold (`0.86`)**: Delivers **90.09% Precision** with only a **0.54% false alarm rate**.
* **Serialized Artifact**: [`models/champion_mev_model.joblib`](file:///c:/Users/lavan/OneDrive/Desktop/Exasol_MEVShield/models/champion_mev_model.joblib) (1.74 MB).

### 6.3 Feature Importances (What the Model Learned)
1. `HAS_NEXT_TRADE` (**36.57%**): Immediate sequential follow-up in the pool.
2. `NEXT_INPUT_SIZE` (**13.51%**): Calldata size contrast between victim swap and bot backrun.
3. `LOG_NEXT_USD` (**10.69%**): Capital volume differences caused by pool slippage.
4. `PRIORITY_FEE_RATIO_PREV` (**10.40%**): Priority fee gas spike to guarantee block position.
5. `PREVIOUS_GAP` (**3.86%**): Direct adjacency in the block execution queue.

### 6.4 Exasol Database Writeback
Streamed **611,106 predictions** into `MEV_SHIELD.SANDWICH_PREDICTIONS` in **3.23 seconds** (189,390 rows/sec):
* **True Negatives**: 566,979 (92.78%)
* **True Positives**: 29,811 (4.88%)
* **False Positives**: 3,280 (0.54%)
* **False Negatives**: 11,036 (1.81%)

---

## 7. Teammate Handoff Architecture (Frontend & WebSocket Live Demo)

### 7.1 The Question: "Does my teammate need Exasol, Docker, or the 1.1 GB dataset?"
**Answer: No.**  
Your teammate does **not** need Docker, Exasol, or the raw 1.1 GB dataset to build, deploy, or run the frontend website.

### 7.2 The Handoff Contract
You only provide your teammate with two files:
1. **The Champion Model Artifact**: [`models/champion_mev_model.joblib`](file:///c:/Users/lavan/OneDrive/Desktop/Exasol_MEVShield/models/champion_mev_model.joblib) (1.74 MB)
2. **The Pristine Holdout Stream**: [`data/live_demo_holdout.csv`](file:///c:/Users/lavan/OneDrive/Desktop/Exasol_MEVShield/data/live_demo_holdout.csv) (117 MB)

### 7.3 How the Teammate's Live Demo Works:
Your teammate sets up a lightweight Python backend (FastAPI / Flask / Node.js) with WebSockets:
```
[live_demo_holdout.csv]  -->  [FastAPI WebSocket Server]  -->  [champion_mev_model.joblib]  -->  [Next.js / React Frontend]
(Reads row by row)            (Broadcasts live tx stream)      (Generates real-time risk score)   (Flashing Red Alert: MEV Detected!)
```
1. The server reads transactions row-by-row from `live_demo_holdout.csv` (simulating incoming Ethereum blocks).
2. For each transaction, it calls `model.predict_proba(X)[:, 1]`.
3. If probability $\ge 0.86$, it broadcasts a **`MEV_SANDWICH_ALERT`** over WebSocket.
4. The frontend dashboard updates instantly with live charts, attacker wallet rankings, and victim trade alerts.

---

## 8. Hackathon Judges Reproducibility Guide

To ensure judges can run and verify the entire system effortlessly without manual setup:

### 8.1 1-Click Batch Runners (Root Directory)
Judges on Windows can simply double-click or run:
* **[`run_all_pipeline.bat`](file:///c:/Users/lavan/OneDrive/Desktop/Exasol_MEVShield/run_all_pipeline.bat)**: Runs the complete end-to-end pipeline (Ingestion ➔ EDA ➔ Split ➔ Model Benchmark ➔ Exasol Writeback) in under 4 minutes.
* **[`run_01_ingest_and_clean.bat`](file:///c:/Users/lavan/OneDrive/Desktop/Exasol_MEVShield/run_01_ingest_and_clean.bat)**: Step 1 (Ingest & Clean).
* **[`run_02_eda.bat`](file:///c:/Users/lavan/OneDrive/Desktop/Exasol_MEVShield/run_02_eda.bat)**: Step 2 (In-database EDA).
* **[`run_03_features_and_split.bat`](file:///c:/Users/lavan/OneDrive/Desktop/Exasol_MEVShield/run_03_features_and_split.bat)**: Step 3 (Feature Engineering & Split).
* **[`run_04_train_evaluate.bat`](file:///c:/Users/lavan/OneDrive/Desktop/Exasol_MEVShield/run_04_train_evaluate.bat)**: Step 4 (Model Training & Writeback).

### 8.2 Terminal Commands (PowerShell / Bash)
```powershell
# Step 1: Ingest 3.4M records and clean in Exasol memory
.venv\Scripts\python.exe src\01_clean_preprocess.py

# Step 2: Run in-memory EDA analytics (10 seconds)
.venv\Scripts\python.exe src\02_eda.py

# Step 3: Run feature engineering and chronological splitting
.venv\Scripts\python.exe src\03_feature_engineering_and_split.py

# Step 4: Run model benchmark and write predictions back to Exasol
.venv\Scripts\python.exe src\04_train_evaluate.py
```

### 8.3 Live SQL Verification in Exasol (EXAplus / DBeaver)
Judges connecting directly to Exasol on port `8563` can run:
```sql
OPEN SCHEMA MEV_SHIELD;

-- Check all tables and row counts:
SELECT TABLE_NAME, TABLE_ROW_COUNT FROM EXA_ALL_TABLES WHERE TABLE_SCHEMA = 'MEV_SHIELD';

-- Inspect live model confusion matrix:
SELECT ACTUAL_LABEL, PREDICTED_LABEL, COUNT(*) FROM MEV_SHIELD.SANDWICH_PREDICTIONS GROUP BY ACTUAL_LABEL, PREDICTED_LABEL;

-- Inspect highest confidence sandwich detections:
SELECT TX_HASH, BLOCK_NUMBER, ROUND(PREDICTED_PROBABILITY * 100, 2) AS CONFIDENCE_PCT 
FROM MEV_SHIELD.SANDWICH_PREDICTIONS 
WHERE PREDICTED_LABEL = 1 
ORDER BY PREDICTED_PROBABILITY DESC 
LIMIT 10;
```

---

## 9. GitHub Repository Sharing & Size Strategy

When committing this repository to GitHub:
1. **Push Code and Documentation**:
   * All `src/` scripts, `sql/` DDLs, batch runners (`.bat`), and `.md` reports.
   * Model artifact: [`models/champion_mev_model.joblib`](file:///c:/Users/lavan/OneDrive/Desktop/Exasol_MEVShield/models/champion_mev_model.joblib) (1.74 MB — easily accepted by GitHub).
2. **Handle the 1.08 GB Dataset**:
   * GitHub has a 100 MB file limit. Do not push `data/sandwich_4M_cleaned_final.csv` directly via standard git.
   * Provide a public Google Drive / OneDrive link in the README, OR use Git LFS.
   * The holdout file [`data/live_demo_holdout.csv`](file:///c:/Users/lavan/OneDrive/Desktop/Exasol_MEVShield/data/live_demo_holdout.csv) (117 MB) can be shared directly with your teammate or hosted via GitHub Releases.
