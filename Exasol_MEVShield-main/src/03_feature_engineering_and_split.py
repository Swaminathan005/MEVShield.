"""
Exasol MEVShield — Phase 1 to 4: In-Database Feature Engineering & Chronological Split
Principal Data Engineer Pipeline:
1. In-Database Feature Engineering with Logarithmic Scaling in MEV_SHIELD.SANDWICH_FEATURES
2. Strict 3-way chronological split on BLOCK_NUMBER (Zero temporal leakage):
   - 10% Live Demo Holdout (BLOCK_NUMBER > p90)
   - 80/20 Train/Test Split on remaining 90% (Train <= p80, Test > p80)
3. Export pristine holdout dataset to data/live_demo_holdout.csv for live frontend simulation
4. Comprehensive logging of row counts, block ranges, and class distributions
"""
import sys
import time
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

def print_section(title: str):
    print("\n" + "=" * 80)
    print(f" {title.upper()} ")
    print("=" * 80)

def main():
    start_total = time.time()
    conn = get_connection(schema="MEV_SHIELD")
    
    print_section("EXASOL MEVSHIELD: FEATURE ENGINEERING & CHRONOLOGICAL SPLIT")
    print("Role: Principal Data Engineer")
    print("Executing in-memory SQL transformations and strict temporal partitioning.")

    # -------------------------------------------------------------------------
    # PHASE 1: In-Database Feature Engineering (Exasol SQL)
    # -------------------------------------------------------------------------
    print_section("Phase 1: Feature Engineering (MEV_SHIELD.SANDWICH_FEATURES)")
    print("Applying logarithmic scaling LN(GREATEST(col, 0) + 1) to high-variance USD/WEI features...")
    
    t0 = time.time()
    feature_sql = """
    CREATE OR REPLACE TABLE MEV_SHIELD.SANDWICH_FEATURES AS
    SELECT 
        -- Identifiers & Target
        TX_HASH,
        BLOCK_NUMBER,
        TRANSACTION_INDEX,
        LABEL,

        -- Contextual Metadata
        FROM_ADDRESS,
        TO_ADDRESS,
        PROJECT_CONTRACT_ADDRESS,

        -- Logarithmic Scaling (Handles massive Ethereum WEI & USD variances)
        LN(GREATEST(CAST(VALUE_ETH AS DOUBLE), 0) + 1)              AS LOG_VALUE_ETH,
        LN(GREATEST(CAST(AMOUNT_USD AS DOUBLE), 0) + 1)             AS LOG_AMOUNT_USD,
        LN(GREATEST(CAST(PREVIOUS_USD AS DOUBLE), 0) + 1)           AS LOG_PREVIOUS_USD,
        LN(GREATEST(CAST(NEXT_USD AS DOUBLE), 0) + 1)               AS LOG_NEXT_USD,
        LN(GREATEST(CAST(GAS_PRICE_WEI AS DOUBLE), 0) + 1)          AS LOG_GAS_PRICE,
        LN(GREATEST(CAST(PRIORITY_FEE_WEI AS DOUBLE), 0) + 1)       AS LOG_PRIORITY_FEE,

        -- Raw Metrics for Hybrid Modeling & Analysis
        VALUE_ETH,
        AMOUNT_USD,
        GAS_USED,
        GAS_PRICE_WEI,
        PRIORITY_FEE_WEI,
        INPUT_SIZE_BYTES,
        POOL_TRADES_IN_BLOCK,

        -- Engineered Boundary Indicators & Gaps (Pass-Through)
        HAS_PREV_TRADE,
        HAS_NEXT_TRADE,
        IS_ISOLATED_POOL_TRADE,
        PREVIOUS_GAP,
        NEXT_GAP,
        PRIORITY_FEE_RATIO_PREV,
        USD_RATIO_PREV,
        PREVIOUS_INPUT_SIZE,
        NEXT_INPUT_SIZE

    FROM MEV_SHIELD.PREPROCESSED_SANDWICH_DATA;
    """
    
    conn.execute(feature_sql)
    conn.commit()
    t_feat = time.time() - t0
    
    feature_count = conn.execute("SELECT COUNT(*) FROM MEV_SHIELD.SANDWICH_FEATURES;").fetchone()[0]
    print(f"[OK] Table MEV_SHIELD.SANDWICH_FEATURES materialized: {feature_count:,} rows in {t_feat:.2f}s!")

    # -------------------------------------------------------------------------
    # PHASE 2: The 3-Way Chronological Split (Exasol SQL)
    # -------------------------------------------------------------------------
    print_section("Phase 2: 3-Way Chronological Split (Zero Temporal Leakage)")
    
    # Step 2A: The 10% Live Demo Holdout (Top 10% blocks)
    print("Step 2A: Computing 90th percentile block across dataset...")
    t0 = time.time()
    p90_block = int(conn.execute(
        "SELECT PERCENTILE_CONT(0.90) WITHIN GROUP (ORDER BY BLOCK_NUMBER) FROM MEV_SHIELD.SANDWICH_FEATURES;"
    ).fetchone()[0])
    print(f"-> 90th Percentile Cutoff Block: {p90_block:,}")

    print(f"Creating MEV_SHIELD.SANDWICH_LIVE_DEMO (BLOCK_NUMBER > {p90_block:,})...")
    conn.execute(f"""
        CREATE OR REPLACE TABLE MEV_SHIELD.SANDWICH_LIVE_DEMO AS
        SELECT * 
        FROM MEV_SHIELD.SANDWICH_FEATURES
        WHERE BLOCK_NUMBER > {p90_block};
    """)
    conn.commit()

    print(f"Creating MEV_SHIELD.SANDWICH_ML_BASE (BLOCK_NUMBER <= {p90_block:,})...")
    conn.execute(f"""
        CREATE OR REPLACE TABLE MEV_SHIELD.SANDWICH_ML_BASE AS
        SELECT * 
        FROM MEV_SHIELD.SANDWICH_FEATURES
        WHERE BLOCK_NUMBER <= {p90_block};
    """)
    conn.commit()
    print(f"[OK] Step 2A Complete in {time.time() - t0:.2f}s.")

    # Step 2B: 80/20 Train/Test Split on SANDWICH_ML_BASE
    print("\nStep 2B: Computing 80th percentile block on SANDWICH_ML_BASE...")
    t0 = time.time()
    p80_block = int(conn.execute(
        "SELECT PERCENTILE_CONT(0.80) WITHIN GROUP (ORDER BY BLOCK_NUMBER) FROM MEV_SHIELD.SANDWICH_ML_BASE;"
    ).fetchone()[0])
    print(f"-> 80th Percentile Cutoff Block: {p80_block:,}")

    print(f"Creating MEV_SHIELD.SANDWICH_TRAIN (BLOCK_NUMBER <= {p80_block:,})...")
    conn.execute(f"""
        CREATE OR REPLACE TABLE MEV_SHIELD.SANDWICH_TRAIN AS
        SELECT * 
        FROM MEV_SHIELD.SANDWICH_ML_BASE
        WHERE BLOCK_NUMBER <= {p80_block};
    """)
    conn.commit()

    print(f"Creating MEV_SHIELD.SANDWICH_TEST (BLOCK_NUMBER > {p80_block:,})...")
    conn.execute(f"""
        CREATE OR REPLACE TABLE MEV_SHIELD.SANDWICH_TEST AS
        SELECT * 
        FROM MEV_SHIELD.SANDWICH_ML_BASE
        WHERE BLOCK_NUMBER > {p80_block};
    """)
    conn.commit()
    print(f"[OK] Step 2B Complete in {time.time() - t0:.2f}s.")

    # -------------------------------------------------------------------------
    # PHASE 3: Exporting the Teammate's Artifact (Python)
    # -------------------------------------------------------------------------
    print_section("Phase 3: Exporting Live Demo Holdout CSV")
    print("Querying MEV_SHIELD.SANDWICH_LIVE_DEMO ordered chronologically (BLOCK_NUMBER ASC, TRANSACTION_INDEX ASC)...")
    
    t0 = time.time()
    holdout_query = """
        SELECT * 
        FROM MEV_SHIELD.SANDWICH_LIVE_DEMO
        ORDER BY BLOCK_NUMBER ASC, TRANSACTION_INDEX ASC;
    """
    df_holdout = conn.export_to_pandas(holdout_query)
    t_export = time.time() - t0
    print(f"[OK] Streamed {len(df_holdout):,} rows from Exasol in {t_export:.2f}s.")

    output_csv = Path(__file__).resolve().parent.parent / "data" / "live_demo_holdout.csv"
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"Saving to {output_csv}...")
    t0 = time.time()
    df_holdout.to_csv(output_csv, index=False)
    csv_size_mb = output_csv.stat().st_size / (1024 * 1024)
    print(f"[OK] Pristine holdout artifact saved in {time.time() - t0:.2f}s ({csv_size_mb:.2f} MB).")

    # -------------------------------------------------------------------------
    # PHASE 4: Final Validation and Console Summary
    # -------------------------------------------------------------------------
    print_section("Phase 4: Chronological Split Audit & Metrics")

    # Query metrics for each split table
    splits_audit_df = conn.export_to_pandas("""
        SELECT 
            'SANDWICH_TRAIN' AS SPLIT_NAME,
            COUNT(*) AS TOTAL_ROWS,
            MIN(BLOCK_NUMBER) AS MIN_BLOCK,
            MAX(BLOCK_NUMBER) AS MAX_BLOCK,
            MAX(BLOCK_NUMBER) - MIN(BLOCK_NUMBER) + 1 AS BLOCK_SPAN,
            SUM(CASE WHEN LABEL = 1 THEN 1 ELSE 0 END) AS POSITIVE_MEV_CASES,
            ROUND(SUM(CASE WHEN LABEL = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS MEV_PCT
        FROM MEV_SHIELD.SANDWICH_TRAIN

        UNION ALL

        SELECT 
            'SANDWICH_TEST' AS SPLIT_NAME,
            COUNT(*) AS TOTAL_ROWS,
            MIN(BLOCK_NUMBER) AS MIN_BLOCK,
            MAX(BLOCK_NUMBER) AS MAX_BLOCK,
            MAX(BLOCK_NUMBER) - MIN(BLOCK_NUMBER) + 1 AS BLOCK_SPAN,
            SUM(CASE WHEN LABEL = 1 THEN 1 ELSE 0 END) AS POSITIVE_MEV_CASES,
            ROUND(SUM(CASE WHEN LABEL = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS MEV_PCT
        FROM MEV_SHIELD.SANDWICH_TEST

        UNION ALL

        SELECT 
            'SANDWICH_LIVE_DEMO' AS SPLIT_NAME,
            COUNT(*) AS TOTAL_ROWS,
            MIN(BLOCK_NUMBER) AS MIN_BLOCK,
            MAX(BLOCK_NUMBER) AS MAX_BLOCK,
            MAX(BLOCK_NUMBER) - MIN(BLOCK_NUMBER) + 1 AS BLOCK_SPAN,
            SUM(CASE WHEN LABEL = 1 THEN 1 ELSE 0 END) AS POSITIVE_MEV_CASES,
            ROUND(SUM(CASE WHEN LABEL = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS MEV_PCT
        FROM MEV_SHIELD.SANDWICH_LIVE_DEMO;
    """)

    print("\n>>> Chronological Partition Summary:")
    print(splits_audit_df.to_string(index=False))

    print("\n" + "-" * 80)
    print("CHRONOLOGICAL INTEGRITY VERIFICATION:")
    train_max = splits_audit_df.loc[splits_audit_df['SPLIT_NAME'] == 'SANDWICH_TRAIN', 'MAX_BLOCK'].values[0]
    test_min = splits_audit_df.loc[splits_audit_df['SPLIT_NAME'] == 'SANDWICH_TEST', 'MIN_BLOCK'].values[0]
    test_max = splits_audit_df.loc[splits_audit_df['SPLIT_NAME'] == 'SANDWICH_TEST', 'MAX_BLOCK'].values[0]
    demo_min = splits_audit_df.loc[splits_audit_df['SPLIT_NAME'] == 'SANDWICH_LIVE_DEMO', 'MIN_BLOCK'].values[0]
    
    assert train_max < test_min, f"Temporal Leakage: Train max block {train_max} >= Test min block {test_min}"
    assert test_max < demo_min, f"Temporal Leakage: Test max block {test_max} >= Demo min block {demo_min}"
    
    print(f"  [OK] Train Max Block ({train_max:,}) < Test Min Block ({test_min:,})")
    print(f"  [OK] Test Max Block ({test_max:,}) < Live Demo Min Block ({demo_min:,})")
    print(f"  [OK] Zero temporal leakage confirmed across all 3 splits!")
    print(f"  [OK] Live Demo CSV artifact verified at: {output_csv}")
    print(f"  [OK] Total Pipeline Execution Time: {time.time() - start_total:.2f}s")
    print("-" * 80)

    conn.close()
    return 0

if __name__ == "__main__":
    sys.exit(main())
