import psycopg2
import psycopg2.extras
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")


# -------------------------
# CONNECTION
# -------------------------
def get_connection():
    try:
        conn = psycopg2.connect(
            DATABASE_URL,
            sslmode="require"
        )
        return conn

    except Exception as e:
        print("DB Connection Error:", e)
        return None


# -------------------------
# INIT DATABASE
# (run manually once if needed)
# -------------------------
def init_db():
    conn = get_connection()
    if conn is None:
        return

    cur = conn.cursor()

    try:
        cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
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

        cur.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id SERIAL PRIMARY KEY,
            name TEXT,
            price REAL,
            description TEXT,
            image_url TEXT,
            merchant_id INTEGER,
            category TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS cart (
            id SERIAL PRIMARY KEY,
            user_id INTEGER,
            product_id INTEGER,
            quantity INTEGER DEFAULT 1
        )
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id SERIAL PRIMARY KEY,
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

        cur.execute("""
        CREATE TABLE IF NOT EXISTS feedback (
            id SERIAL PRIMARY KEY,
            product_id INTEGER,
            order_id INTEGER,
            user_name TEXT,
            rating INTEGER,
            comment TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS wishlist (
            id SERIAL PRIMARY KEY,
            user_id INTEGER,
            product_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id SERIAL PRIMARY KEY,
            name TEXT
        )
        """)

        conn.commit()

    except Exception as e:
        conn.rollback()
        print("Init DB Error:", e)

    finally:
        cur.close()
        conn.close()


# -------------------------
# EXECUTE HELPER
# -------------------------
def execute(query, params=(), fetchone=False, fetchall=False, commit=False):
    conn = get_connection()
    if conn is None:
        return None

    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    try:
        cur.execute(query, params)

        data = None

        if fetchone:
            data = cur.fetchone()

        elif fetchall:
            data = cur.fetchall()

        if commit:
            conn.commit()

        return data

    except Exception as e:
        conn.rollback()
        print("Query Error:", e)
        return None

    finally:
        cur.close()
        conn.close()