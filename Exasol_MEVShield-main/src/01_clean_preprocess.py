"""
Exasol MEVShield — Step 1: Real Dataset Upload, Cleaning & Preprocessing
Loads 1.12 GB (~4M records) of Ethereum sandwich attack transactions into Exasol in-memory,
performs high-speed in-database SQL cleaning, null imputation, and data validation,
and materializes the production table MEV_SHIELD.PREPROCESSED_SANDWICH_DATA.
"""
import time
import sys
from pathlib import Path
import pandas as pd

# Add src to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from db import get_connection

# Ensure Windows terminal handles UTF-8 cleanly
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

def run_step1():
    print("=" * 75)
    print("EXASOL MEVSHIELD: DATA INGESTION, CLEANING & PREPROCESSING")
    print("=" * 75)
    
    start_total = time.time()
    conn = get_connection(schema="MEV_SHIELD")
    
    # -------------------------------------------------------------------------
    # 1. Ensure Schema and Raw Table Exist
    # -------------------------------------------------------------------------
    print("\n>>> [1/4] Ensuring MEV_SHIELD schema and RAW_SANDWICH_DATA table exist...")
    schema_sql_path = Path(__file__).resolve().parent.parent / "sql" / "01_raw_schema.sql"
    if schema_sql_path.exists():
        sql_content = schema_sql_path.read_text(encoding="utf-8")
        for stmt in sql_content.split(";"):
            clean_stmt = stmt.strip()
            if clean_stmt:
                conn.execute(clean_stmt)
    print("[OK] Schema and Table DDL confirmed in Exasol.")

    # -------------------------------------------------------------------------
    # 2. Check If Dataset Already Uploaded; If Not, Ingest CSV
    # -------------------------------------------------------------------------
    print("\n>>> [2/4] Checking RAW_SANDWICH_DATA row count in Exasol...")
    current_count = conn.execute("SELECT COUNT(*) FROM MEV_SHIELD.RAW_SANDWICH_DATA;").fetchone()[0]
    
    csv_file = Path(__file__).resolve().parent.parent / "data" / "sandwich_4M_cleaned_final.csv"
    if not csv_file.exists():
        print(f"[ERROR] Dataset file not found at: {csv_file}")
        conn.close()
        return 1

    file_size_mb = csv_file.stat().st_size / (1024 * 1024)
    print(f"Dataset on disk: {csv_file.name} ({file_size_mb:.2f} MB)")

    if current_count == 0:
        print(f"\nIngesting ~4 Million rows into Exasol in-memory columnar engine...")
        print("Using Exasol native parallel HTTP transport...")
        t0 = time.time()
        
        # Pyexasol import_from_file with fast HTTP streaming
        conn.import_from_file(
            csv_file,
            ("MEV_SHIELD", "RAW_SANDWICH_DATA"),
            import_params={
                "column_separator": ",",
                "row_separator": "CRLF",
                "skip": 1,
                "null": ""
            }
        )
        conn.commit()
        t_ingest = time.time() - t0
        
        new_count = conn.execute("SELECT COUNT(*) FROM MEV_SHIELD.RAW_SANDWICH_DATA;").fetchone()[0]
        print(f"[OK] Ingestion Complete in {t_ingest:.2f}s ({new_count:,} rows loaded at {new_count/t_ingest:,.0f} rows/sec)!")
    else:
        print(f"[OK] Dataset already present in Exasol memory ({current_count:,} rows). Skipping raw re-upload.")

    # -------------------------------------------------------------------------
    # 3. In-Database Data Cleaning & Preprocessing
    # -------------------------------------------------------------------------
    print("\n>>> [3/4] Executing In-Database SQL Cleaning & Preprocessing in Exasol RAM...")
    t_clean_start = time.time()
    
    # Execute in-database cleaning, null imputation, and sanity validation
    clean_sql = """
    CREATE OR REPLACE TABLE MEV_SHIELD.PREPROCESSED_SANDWICH_DATA AS
    SELECT 
        TRIM(TX_HASH)                                      AS TX_HASH,
        CAST(BLOCK_NUMBER AS DECIMAL(18, 0))               AS BLOCK_NUMBER,
        CAST(TRANSACTION_INDEX AS DECIMAL(9, 0))          AS TRANSACTION_INDEX,
        TRIM(LOWER(FROM_ADDRESS))                          AS FROM_ADDRESS,
        TRIM(LOWER(COALESCE(TO_ADDRESS, '')))              AS TO_ADDRESS,
        TRIM(LOWER(COALESCE(PROJECT_CONTRACT_ADDRESS, '')))AS PROJECT_CONTRACT_ADDRESS,
        CAST(COALESCE("VALUE", 0.0) AS DOUBLE)             AS VALUE_ETH,
        CAST(GAS AS DECIMAL(18, 0))                        AS GAS_USED,
        CAST(GAS_PRICE AS DOUBLE)                          AS GAS_PRICE_WEI,
        CAST(COALESCE(MAX_PRIORITY_FEE_PER_GAS, 0.0) AS DOUBLE) AS PRIORITY_FEE_WEI,
        CAST(INPUT_SIZE AS DECIMAL(9, 0))                  AS INPUT_SIZE_BYTES,
        CAST(COALESCE(AMOUNT_USD, 0.0) AS DOUBLE)          AS AMOUNT_USD,
        CAST(COALESCE(PREVIOUS_INDEX, -1) AS DECIMAL(9, 0)) AS PREVIOUS_INDEX,
        CAST(COALESCE(NEXT_INDEX, -1) AS DECIMAL(9, 0))     AS NEXT_INDEX,
        CAST(COALESCE(PREVIOUS_USD, 0.0) AS DOUBLE)        AS PREVIOUS_USD,
        CAST(COALESCE(NEXT_USD, 0.0) AS DOUBLE)            AS NEXT_USD,
        CAST(COALESCE(PREVIOUS_GAS_PRICE, 0.0) AS DOUBLE)  AS PREVIOUS_GAS_PRICE_WEI,
        CAST(COALESCE(NEXT_GAS_PRICE, 0.0) AS DOUBLE)      AS NEXT_GAS_PRICE_WEI,
        CAST(COALESCE(PREVIOUS_PRIORITY_FEE, 0.0) AS DOUBLE) AS PREVIOUS_PRIORITY_FEE_WEI,
        CAST(COALESCE(NEXT_PRIORITY_FEE, 0.0) AS DOUBLE)   AS NEXT_PRIORITY_FEE_WEI,
        CAST(COALESCE(PREVIOUS_INPUT_SIZE, 0) AS DECIMAL(9, 0)) AS PREVIOUS_INPUT_SIZE,
        CAST(COALESCE(NEXT_INPUT_SIZE, 0) AS DECIMAL(9, 0))     AS NEXT_INPUT_SIZE,
        CAST(COALESCE(PREVIOUS_GAP, -1) AS DECIMAL(9, 0))  AS PREVIOUS_GAP,
        CAST(COALESCE(NEXT_GAP, -1) AS DECIMAL(9, 0))      AS NEXT_GAP,
        CAST(COALESCE(PRIORITY_FEE_RATIO_PREV, 0.0) AS DOUBLE) AS PRIORITY_FEE_RATIO_PREV,
        CAST(COALESCE(USD_RATIO_PREV, 0.0) AS DOUBLE)      AS USD_RATIO_PREV,
        CAST(POOL_TRADES_IN_BLOCK AS DECIMAL(9, 0))        AS POOL_TRADES_IN_BLOCK,
        CAST(LABEL AS DECIMAL(1, 0))                       AS LABEL,
        CAST(HAS_PREV_TRADE AS DECIMAL(1, 0))              AS HAS_PREV_TRADE,
        CAST(HAS_NEXT_TRADE AS DECIMAL(1, 0))              AS HAS_NEXT_TRADE,
        CAST(IS_ISOLATED_POOL_TRADE AS DECIMAL(1, 0))      AS IS_ISOLATED_POOL_TRADE
    FROM MEV_SHIELD.RAW_SANDWICH_DATA
    WHERE TX_HASH IS NOT NULL
      AND LENGTH(TRIM(TX_HASH)) = 66
      AND BLOCK_NUMBER > 0
      AND GAS > 0
      AND GAS_PRICE >= 0
      AND COALESCE("VALUE", 0.0) >= 0
      AND COALESCE(AMOUNT_USD, 0.0) >= 0;
    """
    
    conn.execute(clean_sql)
    conn.commit()
    t_clean = time.time() - t_clean_start
    print(f"[OK] Preprocessing completed in {t_clean:.2f}s in Exasol memory!")

    # -------------------------------------------------------------------------
    # 4. Verification & Summary Metrics
    # -------------------------------------------------------------------------
    print("\n>>> [4/4] Verifying Preprocessed Dataset Integrity...")
    
    raw_total = conn.execute("SELECT COUNT(*) FROM MEV_SHIELD.RAW_SANDWICH_DATA;").fetchone()[0]
    clean_total = conn.execute("SELECT COUNT(*) FROM MEV_SHIELD.PREPROCESSED_SANDWICH_DATA;").fetchone()[0]
    rejected_rows = raw_total - clean_total
    
    null_priority_fees = conn.execute(
        "SELECT COUNT(*) FROM MEV_SHIELD.RAW_SANDWICH_DATA WHERE MAX_PRIORITY_FEE_PER_GAS IS NULL;"
    ).fetchone()[0]
    
    print("-" * 75)
    print(f"  • Raw Transactions Ingested:        {raw_total:,}")
    print(f"  • Preprocessed Clean Transactions:  {clean_total:,} ({(clean_total/raw_total)*100:.2f}%)")
    print(f"  • Rejected Corrupt/Malformed Rows:  {rejected_rows:,}")
    print(f"  • Null Priority Fees Imputed to 0:  {null_priority_fees:,}")
    print(f"  • Total Exasol Processing Time:     {time.time() - start_total:.2f}s")
    print("-" * 75)

    print("\nSample Preprocessed Records (5 Rows):")
    preview_df = conn.export_to_pandas("""
        SELECT 
            TX_HASH, 
            BLOCK_NUMBER, 
            TRANSACTION_INDEX, 
            FROM_ADDRESS, 
            AMOUNT_USD, 
            GAS_PRICE_WEI, 
            PRIORITY_FEE_WEI, 
            LABEL, 
            IS_ISOLATED_POOL_TRADE
        FROM MEV_SHIELD.PREPROCESSED_SANDWICH_DATA 
        LIMIT 5;
    """)
    print(preview_df.to_string(index=False))
    
    conn.close()
    print("\n" + "=" * 75)
    print("STEP 1 COMPLETE: DATASET READY FOR EDA (src/02_eda.py)")
    print("=" * 75)
    return 0

if __name__ == "__main__":
    sys.exit(run_step1())
