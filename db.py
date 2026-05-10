import sqlite3
import os

# 🔥 Render-safe absolute path
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE = os.path.join(BASE_DIR, "database.db")


# -------------------------
# INIT DATABASE (FULL FIXED)
# -------------------------
def init_db():
    conn = sqlite3.connect(DATABASE)
    cur = conn.cursor()

    # USERS (FIXED FOR PROFILE PAGE)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT UNIQUE,
        password TEXT,
        role TEXT DEFAULT 'user',
        address1 TEXT,
        address2 TEXT,
        city TEXT,
        pincode TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # PRODUCTS (FIXED FOR MERCHANT + USER)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        price REAL,
        description TEXT,
        image_url TEXT,
        merchant_id INTEGER,
        category TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # CART
    cur.execute("""
    CREATE TABLE IF NOT EXISTS cart (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        product_id INTEGER,
        quantity INTEGER DEFAULT 1
    )
    """)

    # ORDERS (FIXED FOR CHECKOUT + STATUS + MERCHANT)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER,
        quantity INTEGER,
        total_price REAL,
        user_id INTEGER,
        merchant_id INTEGER,
        order_group TEXT,
        status TEXT DEFAULT 'Pending',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # FEEDBACK (USED IN MERCHANT PAGE)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS feedback (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER,
        order_id INTEGER,
        user_name TEXT,
        rating INTEGER,
        comment TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # WISHLIST
    cur.execute("""
    CREATE TABLE IF NOT EXISTS wishlist (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        product_id INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # CATEGORIES (FOR ALL PRODUCTS PAGE)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT
    )
    """)

    conn.commit()
    conn.close()


# -------------------------
# CONNECTION
# -------------------------
def get_connection():
    conn = sqlite3.connect(DATABASE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


# -------------------------
# EXECUTE HELPER
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
# INIT ON IMPORT (RENDER SAFE)
# -------------------------
init_db()