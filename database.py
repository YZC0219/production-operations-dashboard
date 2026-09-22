import sqlite3
from contextlib import contextmanager
from config import DATABASE_PATH

SCHEMA = """
CREATE TABLE IF NOT EXISTS workshops (id INTEGER PRIMARY KEY, workshop_code TEXT UNIQUE NOT NULL, workshop_name TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS machines (id INTEGER PRIMARY KEY, machine_code TEXT UNIQUE NOT NULL, machine_name TEXT NOT NULL, workshop_code TEXT NOT NULL, status TEXT NOT NULL CHECK(status IN ('运行','停机','故障')), current_product TEXT NOT NULL DEFAULT '', updated_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS products (id INTEGER PRIMARY KEY, product_code TEXT UNIQUE NOT NULL, product_name TEXT NOT NULL, product_category TEXT NOT NULL, unit TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS production_records (id INTEGER PRIMARY KEY, record_date TEXT NOT NULL, machine_code TEXT NOT NULL, product_code TEXT NOT NULL, planned_quantity INTEGER NOT NULL, actual_quantity INTEGER NOT NULL, qualified_quantity INTEGER NOT NULL, defective_quantity INTEGER NOT NULL, start_time TEXT, end_time TEXT, UNIQUE(record_date,machine_code,product_code));
CREATE TABLE IF NOT EXISTS production_plans (id INTEGER PRIMARY KEY, plan_code TEXT UNIQUE NOT NULL, plan_date TEXT NOT NULL, machine_code TEXT NOT NULL, product_code TEXT NOT NULL, planned_quantity INTEGER NOT NULL, completed_quantity INTEGER NOT NULL, status TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS orders (id INTEGER PRIMARY KEY, order_code TEXT UNIQUE NOT NULL, customer_name TEXT NOT NULL, product_code TEXT NOT NULL, order_quantity INTEGER NOT NULL, produced_quantity INTEGER NOT NULL, delivered_quantity INTEGER NOT NULL, order_date TEXT NOT NULL, delivery_date TEXT NOT NULL, status TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS inventory (id INTEGER PRIMARY KEY, material_code TEXT UNIQUE NOT NULL, material_name TEXT NOT NULL, material_type TEXT NOT NULL, current_stock REAL NOT NULL, safety_stock REAL NOT NULL, maximum_stock REAL NOT NULL, unit TEXT NOT NULL, warehouse_location TEXT NOT NULL, updated_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS machine_realtime (
 machine_code TEXT PRIMARY KEY NOT NULL,
 status TEXT NOT NULL,
 actual_quantity INTEGER NOT NULL DEFAULT 0,
 qualified_quantity INTEGER NOT NULL DEFAULT 0,
 defective_quantity INTEGER NOT NULL DEFAULT 0,
 fault_code INTEGER NOT NULL DEFAULT 0,
 collected_at TEXT NOT NULL,
 data_source TEXT NOT NULL,
 connection_status TEXT NOT NULL,
 last_error TEXT NOT NULL DEFAULT ''
);
"""

def connect():
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@contextmanager
def transaction():
    conn = connect()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def init_database():
    with transaction() as conn:
        conn.executescript(SCHEMA)
