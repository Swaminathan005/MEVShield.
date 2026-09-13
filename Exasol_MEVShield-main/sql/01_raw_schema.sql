-- ============================================================================
-- Exasol MEVShield: Raw Dataset Schema
-- Optimized In-Memory Columnar Storage for 4M+ Ethereum Sandwich Transactions
-- ============================================================================

CREATE SCHEMA IF NOT EXISTS MEV_SHIELD;
OPEN SCHEMA MEV_SHIELD;

CREATE OR REPLACE TABLE RAW_SANDWICH_DATA (
    TX_HASH                     VARCHAR(66),
    BLOCK_NUMBER                DECIMAL(18, 0),
    TRANSACTION_INDEX           DECIMAL(9, 0),
    FROM_ADDRESS                VARCHAR(66),
    TO_ADDRESS                  VARCHAR(66),
    PROJECT_CONTRACT_ADDRESS    VARCHAR(66),
    "VALUE"                     DOUBLE,
    GAS                         DECIMAL(18, 0),
    GAS_PRICE                   DOUBLE,
    MAX_PRIORITY_FEE_PER_GAS    DOUBLE,
    INPUT_SIZE                  DECIMAL(9, 0),
    AMOUNT_USD                  DOUBLE,
    PREVIOUS_INDEX              DECIMAL(9, 0),
    NEXT_INDEX                  DECIMAL(9, 0),
    PREVIOUS_USD                DOUBLE,
    NEXT_USD                    DOUBLE,
    PREVIOUS_GAS_PRICE          DOUBLE,
    NEXT_GAS_PRICE              DOUBLE,
    PREVIOUS_PRIORITY_FEE       DOUBLE,
    NEXT_PRIORITY_FEE           DOUBLE,
    PREVIOUS_INPUT_SIZE         DECIMAL(9, 0),
    NEXT_INPUT_SIZE             DECIMAL(9, 0),
    PREVIOUS_GAP                DECIMAL(9, 0),
    NEXT_GAP                    DECIMAL(9, 0),
    PRIORITY_FEE_RATIO_PREV     DOUBLE,
    USD_RATIO_PREV              DOUBLE,
    POOL_TRADES_IN_BLOCK        DECIMAL(9, 0),
    LABEL                       DECIMAL(1, 0),
    HAS_PREV_TRADE              DECIMAL(1, 0),
    HAS_NEXT_TRADE              DECIMAL(1, 0),
    IS_ISOLATED_POOL_TRADE      DECIMAL(1, 0)
);
