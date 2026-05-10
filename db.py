import sqlite3
import os

# 🔥 IMPORTANT: absolute path fix for Render
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE = os.path.join(BASE_DIR, "database.db")


# -------------------------
# CREATE TABLES
# -------------------------
def init_db():
    conn = sqlite3.connect(DATABASE)
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT UNIQUE,
        password TEXT,
        role TEXT DEFAULT 'user'
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        price REAL
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS cart (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        product_id INTEGER,
        quantity INTEGER DEFAULT 1
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        product_id INTEGER,
        quantity INTEGER
    )
    """)

    conn.commit()
    conn.close()


# -------------------------
# DB CONNECTION
# -------------------------
def get_connection():
    conn = sqlite3.connect(DATABASE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


# -------------------------
# EXECUTE QUERY
# -------------------------
def execute(query, params=(), fetchone=False, fetchall=False, commit=False):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(query, params)

    data = None

    if fetchone:
        data = cur.fetchone()
    elif fetchall:
        data = cur.fetchall()

    if commit:
        conn.commit()

    conn.close()
    return data


# -------------------------
# INIT DB SAFELY (NO AUTO CRASH)
# -------------------------
if __name__ != "__main__":
    init_db()