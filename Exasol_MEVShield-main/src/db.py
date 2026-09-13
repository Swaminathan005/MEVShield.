"""
Database Connection Utility for Local Exasol in Docker
"""
import os
import ssl
from pathlib import Path
from dotenv import load_dotenv
import pyexasol

# Load environment variables from .env
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

def get_connection(autocommit: bool = True, schema: str = None):
    """
    Establish a secure pyexasol connection to the local Docker Exasol instance.
    Uses TLS with self-signed certificate verification bypass for local development.
    """
    dsn = os.getenv("EXASOL_DSN", "127.0.0.1:8563")
    user = os.getenv("EXASOL_USER", "sys")
    password = os.getenv("EXASOL_PASSWORD", "")
    target_schema = schema or os.getenv("EXASOL_SCHEMA", None)

    # If password is empty, fallback to starter kit credentials file if available
    if not password:
        pw_file = Path.home() / ".exasol-starter-kit" / "credentials" / "nano_sys_password"
        if pw_file.exists():
            password = pw_file.read_text(encoding="utf-8").strip()

    connect_params = {
        "dsn": dsn,
        "user": user,
        "password": password,
        "autocommit": autocommit,
        "encryption": True,
        "websocket_sslopt": {"cert_reqs": ssl.CERT_NONE}
    }

    connection = pyexasol.connect(**connect_params)
    if target_schema:
        try:
            connection.execute(f"CREATE SCHEMA IF NOT EXISTS {target_schema};")
            connection.execute(f"OPEN SCHEMA {target_schema};")
        except Exception:
            pass
    return connection

if __name__ == "__main__":
    conn = get_connection()
    res = conn.execute("SELECT 1 AS TEST_COL").fetchall()
    print("Self-test connection successful:", res)
    conn.close()
