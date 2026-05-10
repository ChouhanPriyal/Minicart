import sqlite3

DATABASE = "database.db"


# 🔥 CREATE TABLES AUTOMATICALLY
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


# 🔥 DATABASE CONNECTION
def get_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


# 🔥 QUERY EXECUTOR
def execute(query, params=(), fetchone=False, fetchall=False, commit=False):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(query, params)

    data = None

    if commit:
        conn.commit()
    if fetchone:
        data = cur.fetchone()
    if fetchall:
        data = cur.fetchall()

    conn.close()
    return data


# 🔥 RUN DB ON IMPORT
init_db()