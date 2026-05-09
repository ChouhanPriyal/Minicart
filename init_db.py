import sqlite3

conn = sqlite3.connect("database.db")
cur = conn.cursor()

# USERS
cur.execute("""
CREATE TABLE users (
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

# PRODUCTS
cur.execute("""
CREATE TABLE products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    price REAL,
    description TEXT,
    image_url TEXT,
    merchant_id INTEGER,
    category TEXT,
    category_id INTEGER
)
""")

# CART
cur.execute("""
CREATE TABLE cart (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    product_id INTEGER,
    quantity INTEGER DEFAULT 1
)
""")

# ORDERS
cur.execute("""
CREATE TABLE orders (
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

# FEEDBACK
cur.execute("""
CREATE TABLE feedback (
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
CREATE TABLE wishlist (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    product_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

# CATEGORIES
cur.execute("""
CREATE TABLE categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL
)
""")

conn.commit()
conn.close()

print("✅ DATABASE CREATED SUCCESSFULLY")