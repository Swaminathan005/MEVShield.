"""
Exasol MEVShield — Step 2: In-Database Exploratory Data Analysis (EDA)
Runs high-speed parallel analytical SQL queries across all ~4M records in Exasol memory.
Profiles target class distributions, MEV priority gas auction spikes, USD volume deltas,
sequence gap mechanics, and ranks the top 10 MEV searcher bot wallets.
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

def print_header(title: str):
    print("\n" + "=" * 80)
    print(f" {title.upper()} ")
    print("=" * 80)

def print_table(df: pd.DataFrame, title: str = None):
    if title:
        print(f"\n>>> {title}:")
    print(df.to_string(index=False))

def run_eda():
    start_total = time.time()
    conn = get_connection(schema="MEV_SHIELD")
    
    print_header("EXASOL MEVSHIELD: IN-DATABASE EXPLORATORY DATA ANALYSIS (EDA)")
    print("NOTE: All statistical profiling and aggregations below run directly inside")
    print("Exasol's in-memory columnar database. Zero raw data is transferred to Python.")
    
    # -------------------------------------------------------------------------
    # 1. High-Level Cardinality & Scope
    # -------------------------------------------------------------------------
    print_header("1. High-Level Dataset Scope & Cardinality")
    t0 = time.time()
    cardinality_df = conn.export_to_pandas("""
        SELECT 
            COUNT(*)                                      AS TOTAL_TRANSACTIONS,
            COUNT(DISTINCT BLOCK_NUMBER)                  AS UNIQUE_BLOCKS,
            COUNT(DISTINCT FROM_ADDRESS)                  AS UNIQUE_SENDERS,
            COUNT(DISTINCT PROJECT_CONTRACT_ADDRESS)      AS UNIQUE_POOLS_CONTRACTS,
            MIN(BLOCK_NUMBER)                             AS MIN_BLOCK,
            MAX(BLOCK_NUMBER)                             AS MAX_BLOCK,
            MAX(BLOCK_NUMBER) - MIN(BLOCK_NUMBER) + 1    AS TOTAL_BLOCK_SPAN
        FROM MEV_SHIELD.PREPROCESSED_SANDWICH_DATA;
    """)
    print_table(cardinality_df, f"Dataset Cardinality (Computed in {time.time() - t0:.2f}s)")

    # -------------------------------------------------------------------------
    # 2. Target Class Balance (Sandwich MEV Attacks vs Normal Trades)
    # -------------------------------------------------------------------------
    print_header("2. Target Class Distribution (MEV Sandwich vs Benign)")
    t0 = time.time()
    class_df = conn.export_to_pandas("""
        SELECT 
            CASE WHEN LABEL = 1 THEN 'MEV_SANDWICH_ATTACK (Positive)' ELSE 'NORMAL_POOL_TRADE (Negative)' END AS TRANSACTION_TYPE,
            COUNT(*) AS TXN_COUNT,
            ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM MEV_SHIELD.PREPROCESSED_SANDWICH_DATA), 2) AS PERCENTAGE
        FROM MEV_SHIELD.PREPROCESSED_SANDWICH_DATA
        GROUP BY LABEL
        ORDER BY LABEL DESC;
    """)
    print_table(class_df, f"Class Imbalance Profiling (Computed in {time.time() - t0:.2f}s)")

    # -------------------------------------------------------------------------
    # 3. Gas Dynamics & Priority Fee Auctions (The MEV Smoking Gun)
    # -------------------------------------------------------------------------
    print_header("3. Gas Auction Dynamics & Priority Fee Discrepancies")
    print("Analysis: Demonstrates how MEV bots bid significantly higher priority fees to frontrun.")
    t0 = time.time()
    gas_df = conn.export_to_pandas("""
        SELECT 
            CASE WHEN LABEL = 1 THEN 'MEV_SANDWICH' ELSE 'NORMAL_TRADE' END AS TXN_TYPE,
            COUNT(*) AS COUNT_RECORDS,
            ROUND(AVG(GAS_PRICE_WEI) / 1e9, 2)              AS AVG_GAS_PRICE_GWEI,
            ROUND(MEDIAN(GAS_PRICE_WEI) / 1e9, 2)           AS MEDIAN_GAS_PRICE_GWEI,
            ROUND(PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY GAS_PRICE_WEI) / 1e9, 2) AS P95_GAS_PRICE_GWEI,
            ROUND(AVG(PRIORITY_FEE_WEI) / 1e9, 2)           AS AVG_PRIORITY_FEE_GWEI,
            ROUND(PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY PRIORITY_FEE_WEI) / 1e9, 2) AS P95_PRIORITY_FEE_GWEI,
            ROUND(AVG(GAS_USED), 0)                         AS AVG_GAS_USED
        FROM MEV_SHIELD.PREPROCESSED_SANDWICH_DATA
        GROUP BY LABEL
        ORDER BY LABEL DESC;
    """)
    print_table(gas_df, f"Gas Auction Comparison (Computed in {time.time() - t0:.2f}s)")

    # -------------------------------------------------------------------------
    # 4. Financial Trade Volume (USD & ETH)
    # -------------------------------------------------------------------------
    print_header("4. Financial Volume & Capital Distribution (USD & ETH)")
    t0 = time.time()
    volume_df = conn.export_to_pandas("""
        SELECT 
            CASE WHEN LABEL = 1 THEN 'MEV_SANDWICH' ELSE 'NORMAL_TRADE' END AS TXN_TYPE,
            ROUND(SUM(AMOUNT_USD), 2)                       AS TOTAL_VOLUME_USD,
            ROUND(AVG(AMOUNT_USD), 2)                       AS AVG_TRADE_USD,
            ROUND(MEDIAN(AMOUNT_USD), 2)                    AS MEDIAN_TRADE_USD,
            ROUND(PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY AMOUNT_USD), 2) AS P95_TRADE_USD,
            ROUND(MAX(AMOUNT_USD), 2)                       AS MAX_SINGLE_TRADE_USD,
            ROUND(AVG(VALUE_ETH), 4)                        AS AVG_ETH_VALUE
        FROM MEV_SHIELD.PREPROCESSED_SANDWICH_DATA
        GROUP BY LABEL
        ORDER BY LABEL DESC;
    """)
    print_table(volume_df, f"Capital Distribution (Computed in {time.time() - t0:.2f}s)")

    # -------------------------------------------------------------------------
    # 5. Sequence Positioning & Pool Gaps
    # -------------------------------------------------------------------------
    print_header("5. Sequential Index Positioning & Pool Trade Gaps")
    t0 = time.time()
    gaps_df = conn.export_to_pandas("""
        SELECT 
            CASE WHEN LABEL = 1 THEN 'MEV_SANDWICH' ELSE 'NORMAL_TRADE' END AS TXN_TYPE,
            ROUND(AVG(CASE WHEN PREVIOUS_GAP >= 0 THEN PREVIOUS_GAP ELSE NULL END), 2) AS AVG_PREV_GAP,
            ROUND(AVG(CASE WHEN NEXT_GAP >= 0 THEN NEXT_GAP ELSE NULL END), 2)         AS AVG_NEXT_GAP,
            ROUND(AVG(POOL_TRADES_IN_BLOCK), 2)                                         AS AVG_POOL_TRADES_IN_BLOCK,
            ROUND(SUM(IS_ISOLATED_POOL_TRADE) * 100.0 / COUNT(*), 2)                    AS ISOLATED_TRADE_PCT,
            ROUND(SUM(HAS_PREV_TRADE) * 100.0 / COUNT(*), 2)                            AS HAS_PREV_TRADE_PCT,
            ROUND(SUM(HAS_NEXT_TRADE) * 100.0 / COUNT(*), 2)                            AS HAS_NEXT_TRADE_PCT
        FROM MEV_SHIELD.PREPROCESSED_SANDWICH_DATA
        GROUP BY LABEL
        ORDER BY LABEL DESC;
    """)
    print_table(gaps_df, f"Sequence Mechanics (Computed in {time.time() - t0:.2f}s)")

    # -------------------------------------------------------------------------
    # 6. Top 10 Most Aggressive MEV Searcher Bot Wallets
    # -------------------------------------------------------------------------
    print_header("6. Top 10 MEV Searcher Wallets (Ranked by Attack Frequency)")
    t0 = time.time()
    top_bots_df = conn.export_to_pandas("""
        SELECT 
            FROM_ADDRESS                                    AS MEV_BOT_ADDRESS,
            COUNT(*)                                        AS ATTACKS_EXECUTED,
            ROUND(SUM(AMOUNT_USD), 2)                       AS TOTAL_USD_VOLUME,
            ROUND(AVG(PRIORITY_FEE_WEI) / 1e9, 2)           AS AVG_PRIORITY_FEE_GWEI,
            COUNT(DISTINCT PROJECT_CONTRACT_ADDRESS)        AS POOLS_TARGETED,
            MIN(BLOCK_NUMBER)                               AS FIRST_ACTIVE_BLOCK,
            MAX(BLOCK_NUMBER)                               AS LAST_ACTIVE_BLOCK
        FROM MEV_SHIELD.PREPROCESSED_SANDWICH_DATA
        WHERE LABEL = 1
        GROUP BY FROM_ADDRESS
        ORDER BY ATTACKS_EXECUTED DESC
        LIMIT 10;
    """)
    print_table(top_bots_df, f"Top 10 MEV Bots (Computed in {time.time() - t0:.2f}s)")

    # -------------------------------------------------------------------------
    # 7. Top 5 Targeted Liquidity Pools
    # -------------------------------------------------------------------------
    print_header("7. Top 5 Most Targeted Liquidity Pools / Contracts")
    t0 = time.time()
    top_pools_df = conn.export_to_pandas("""
        SELECT 
            PROJECT_CONTRACT_ADDRESS                        AS POOL_CONTRACT_ADDRESS,
            COUNT(*)                                        AS TOTAL_MEV_ATTACKS,
            ROUND(SUM(AMOUNT_USD), 2)                       AS TOTAL_VICTIM_USD_EXPOSED,
            COUNT(DISTINCT FROM_ADDRESS)                    AS DISTINCT_ATTACKERS
        FROM MEV_SHIELD.PREPROCESSED_SANDWICH_DATA
        WHERE LABEL = 1
        GROUP BY PROJECT_CONTRACT_ADDRESS
        ORDER BY TOTAL_MEV_ATTACKS DESC
        LIMIT 5;
    """)
    print_table(top_pools_df, f"Top Targeted Pools (Computed in {time.time() - t0:.2f}s)")

    conn.close()
    print_header(f"EDA COMPLETE — TOTAL EXASOL TIME: {time.time() - start_total:.2f} SECONDS")
    return 0

if __name__ == "__main__":
    sys.exit(run_eda())
