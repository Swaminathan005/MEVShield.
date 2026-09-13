# Exasol MEVShield — Test & Verification Commands

This document lists all the exact commands to test connections, load the demo database, and run the pipeline scripts.

---

## 1. Quick Environment Activation

Before running commands, activate the virtual environment in your terminal:

### PowerShell (Windows):
```powershell
.\.venv\Scripts\Activate.ps1
```
*(If PowerShell execution policy prevents activation, run: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`)*

### Command Prompt (cmd.exe):
```cmd
.venv\Scripts\activate.bat
```

> [!TIP]
> You can also run any script directly without activating the environment by calling `.venv\Scripts\python.exe` directly, as shown in the commands below!

---

## 2. Test Connection Commands

### Option A: Quick One-Liner Connection Test
Runs a quick `SELECT 1;` query directly from your terminal:
```powershell
.venv\Scripts\python.exe -c "from src.db import get_connection; conn = get_connection(); print('Connected to Exasol! Version:', conn.execute('SELECT PARAM_VALUE FROM SYS.EXA_METADATA WHERE PARAM_NAME = \'databaseProductVersion\';').fetchone()[0]); conn.close()"
```

### Option B: Dedicated Step 1 Verification Script
Verifies connection, prints session info, user, and schema:
```powershell
.venv\Scripts\python.exe tests\demo_pipeline\01_test_conn.py
```

---

## 3. Demo Pipeline Verification Commands

All 5 demo scripts are located in `tests/demo_pipeline/` and can be run independently or sequentially.

### Step 1: Test Connection
```powershell
.venv\Scripts\python.exe tests\demo_pipeline\01_test_conn.py
```
* **What it does**: Verifies Python can communicate with Exasol inside Docker on `127.0.0.1:8563`.

### Step 2: Load Synthetic Demo Database
```powershell
.venv\Scripts\python.exe tests\demo_pipeline\02_load_data.py
```
* **What it does**: Creates schema `DEMO_DB`, creates table `USER_TRANSACTIONS`, generates 1,000 synthetic rows, bulk-ingests them into Exasol, and runs `SELECT COUNT(*)`.

### Step 3: Run In-Database SQL Analytics
```powershell
.venv\Scripts\python.exe tests\demo_pipeline\03_sql_analytics.py
```
* **What it does**: Sends SQL aggregation queries (`COUNT`, `AVG`, `GROUP BY`, `HAVING`) to Exasol. Proves that computations occur in Exasol's memory.

### Step 4: In-Database Feature Engineering & ML Training
```powershell
.venv\Scripts\python.exe tests\demo_pipeline\04_train.py
```
* **What it does**: Computes window functions in SQL inside Exasol, passes the matrix to Scikit-Learn, trains a `RandomForestClassifier`, and saves `risk_model.joblib`.

### Step 5: Live Real-Time Prediction Flow
```powershell
.venv\Scripts\python.exe tests\demo_pipeline\05_predict.py
```
* **What it does**: Simulates an incoming transaction, queries Exasol for the user's historical profile, scores fraud risk with the model, and outputs classification.

---

## 4. Run Everything in One Command

To run all 5 steps sequentially in one shot:
```powershell
.venv\Scripts\python.exe tests\demo_pipeline\run_demo.py
```

---

## 5. Exasol Database Inspection Commands

### Check Available Schemas in Exasol
```powershell
.venv\Scripts\python.exe -c "from src.db import get_connection; conn = get_connection(); print(conn.execute('SELECT SCHEMA_NAME FROM EXA_ALL_SCHEMAS;').fetchall()); conn.close()"
```

### Check Tables & Row Counts in DEMO_DB
```powershell
.venv\Scripts\python.exe -c "from src.db import get_connection; conn = get_connection(); print(conn.execute('SELECT TABLE_NAME, TABLE_ROW_COUNT FROM EXA_ALL_TABLES WHERE TABLE_SCHEMA = \'DEMO_DB\';').fetchall()); conn.close()"
```

### Clean Up / Wipe Old DEMO_DB (When Ready)
```powershell
.venv\Scripts\python.exe -c "from src.db import get_connection; conn = get_connection(); conn.execute('DROP SCHEMA IF EXISTS DEMO_DB CASCADE;'); print('DEMO_DB schema dropped.'); conn.close()"
```

---

## 6. Directory Reference

* `tests/demo_pipeline/`: Complete self-contained verification suite.
* `tests/temp_old_db/`: Backup of the old test database schema DDL (`sql/`) and synthetic dataset (`data/`).
