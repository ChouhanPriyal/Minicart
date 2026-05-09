import sqlite3

DATABASE = "database.db"

def get_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def execute(query, params=(), fetchone=False, fetchall=False, commit=False):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(query, params)

    data = None

    if fetchone:
        data = cur.fetchone()

    if fetchall:
        data = cur.fetchall()

    if commit:
        conn.commit()

    conn.close()

    return data