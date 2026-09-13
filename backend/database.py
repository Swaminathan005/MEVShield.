import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

import os
import csv
from pathlib import Path
from typing import Dict, List, Generator, Optional
import model  # Now we can import model directly

# Base directory: project root (contains backend and Exasol_MEVShield-main)
BASE_DIR = Path(__file__).parent.parent
# Path to the holdout CSV data (relative to this file)
DATA_PATH = BASE_DIR / "Exasol_MEVShield-main" / "data" / "holdout_sample_10k.csv"

def _get_feature_order() -> List[str]:
    """Return the list of feature names in the order expected by the model."""
    return model.get_feature_names()

def _load_holdout_data() -> List[Dict]:
    """
    Load the holdout CSV and return a list of dictionaries sorted by BLOCK_NUMBER and TRANSACTION_INDEX.
    Each dictionary maps column name to value (as string).
    """
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Holdout data not found at {DATA_PATH}")

    with open(DATA_PATH, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    # Convert BLOCK_NUMBER and TRANSACTION_INDEX to int for sorting
    for row in rows:
        row['BLOCK_NUMBER'] = int(row['BLOCK_NUMBER'])
        row['TRANSACTION_INDEX'] = int(row['TRANSACTION_INDEX'])

    # Sort by BLOCK_NUMBER then TRANSACTION_INDEX
    rows.sort(key=lambda r: (r['BLOCK_NUMBER'], r['TRANSACTION_INDEX']))
    return rows

def get_holdout_data_generator() -> Generator[Dict, None, None]:
    """
    Generator that yields each transaction in chronological order.
    Each yielded dict contains:
        - tx_hash: str
        - block_number: int
        - transaction_index: int
        - features: List[float] (in the order of model.get_feature_names())
    """
    rows = _load_holdout_data()
    feature_names = _get_feature_order()

    for row in rows:
        # Extract the feature values in the correct order
        try:
            features = [float(row[feat]) for feat in feature_names]
        except KeyError as e:
            raise KeyError(f"Feature {e} not found in CSV columns. Available columns: {list(row.keys())}")
        except ValueError as e:
            raise ValueError(f"Could not convert feature value to float for transaction {row['TX_HASH']}: {e}")

        yield {
            'tx_hash': row['TX_HASH'],
            'block_number': row['BLOCK_NUMBER'],
            'transaction_index': row['TRANSACTION_INDEX'],
            'features': features
        }

# Exasol support (optional)
def get_exasol_connection():
    """
    Establish a connection to Exasol using environment variables.
    Returns a pyexasol connection object or None if not configured.
    """
    try:
        import pyexasol
    except ImportError:
        return None

    dsn = os.getenv("EXASOL_DSN")
    user = os.getenv("EXASOL_USER")
    password = os.getenv("EXASOL_PASSWORD")
    schema = os.getenv("EXASOL_SCHEMA", "MEV_SHIELD")

    if not all([dsn, user, password]):
        return None

    try:
        connection = pyexasol.connect(
            dsn=dsn,
            user=user,
            password=password,
            schema=schema,
            encryption=True,
            websocket_sslopt={"cert_reqs": 0}  # CERT_NONE for local dev
        )
        return connection
    except Exception:
        return None

def get_exasol_data_generator() -> Optional[Generator[Dict, None, None]]:
    """
    If Exasol is configured, return a generator that fetches transactions from the live-demo table.
    Otherwise, return None.
    """
    conn = get_exasol_connection()
    if conn is None:
        return None

    feature_names = _get_feature_order()
    # We assume the table name is LIVE_DEMO_HOLDOUT or similar; adjust as needed.
    # The plan says the backend retrieves the live-demo holdout data.
    # We'll use a table that has at least TX_HASH, BLOCK_NUMBER, TRANSACTION_INDEX, and the feature columns.
    # We'll order by BLOCK_NUMBER, TRANSACTION_INDEX.
    try:
        stmt = f"""
            SELECT TX_HASH, BLOCK_NUMBER, TRANSACTION_INDEX, {', '.join(feature_names)}
            FROM LIVE_DEMO_HOLDOUT
            ORDER BY BLOCK_NUMBER, TRANSACTION_INDEX
        """
        stmt = stmt.replace('\n', ' ').strip()
        result = conn.execute(stmt)
        for row in result:
            # row is a tuple; we know the order: TX_HASH, BLOCK_NUMBER, TRANSACTION_INDEX, then features
            tx_hash = row[0]
            block_number = int(row[1])
            transaction_index = int(row[2])
            features = [float(row[i]) for i in range(3, 3 + len(feature_names))]
            yield {
                'tx_hash': tx_hash,
                'block_number': block_number,
                'transaction_index': transaction_index,
                'features': features
            }
    except Exception as e:
        print(f"Error fetching from Exasol: {e}")
        return None
    finally:
        conn.close()