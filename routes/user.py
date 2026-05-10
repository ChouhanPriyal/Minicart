from flask import Blueprint, render_template, request, redirect, url_for, session, flash
import sqlite3
import uuid
import os

user_bp = Blueprint("user", __name__)

DB_PATH = os.path.join(os.getcwd(), "database.db")


# -------------------------
# DB CONNECTION (RENDER SAFE)
# -------------------------
def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ======================
# HOME PAGE
# ======================
@user_bp.route("/user-home")
def home():

    if "user_id" not in session or session.get("role") != "user":
        return redirect("/login")

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT id, name, price, description, image_url FROM products ORDER BY id DESC")

    products = cur.fetchall()
    conn.close()

    return render_template("user/home.html", products=products)


# ======================
# ADD TO CART
# ======================
@user_bp.route("/add_to_cart/<int:product_id>")
def add_to_cart(product_id):

    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT id FROM cart
        WHERE product_id = ? AND user_id = ?
    """, (product_id, user_id))

    existing = cur.fetchone()

    if existing:
        cur.execute("""
            UPDATE cart
            SET quantity = quantity + 1
            WHERE product_id = ? AND user_id = ?
        """, (product_id, user_id))
    else:
        cur.execute("""
            INSERT INTO cart (product_id, quantity, user_id)
            VALUES (?, ?, ?)
        """, (product_id, 1, user_id))

    conn.commit()
    conn.close()

    flash("Added to Cart 🛒", "success")
    return redirect(url_for("user.cart"))


# ======================
# CART PAGE
# ======================
@user_bp.route("/cart")
def cart():

    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT p.id, p.name, p.price, p.description, p.image_url, c.quantity
        FROM cart c
        JOIN products p ON c.product_id = p.id
        WHERE c.user_id = ?
    """, (user_id,))

    cart_items = cur.fetchall()

    total = 0
    for item in cart_items:
        total += float(item["price"]) * int(item["quantity"])

    conn.close()

    return render_template("user/cart.html", cart_items=cart_items, total=total)


# ======================
# REMOVE FROM CART
# ======================
@user_bp.route("/remove_from_cart/<int:product_id>")
def remove_from_cart(product_id):

    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        DELETE FROM cart
        WHERE product_id = ? AND user_id = ?
    """, (product_id, user_id))

    conn.commit()
    conn.close()

    flash("Item removed ❌", "success")
    return redirect(url_for("user.cart"))


# ======================
# INCREASE
# ======================
@user_bp.route("/increase/<int:product_id>")
def increase(product_id):

    if "user_id" not in session:
        return redirect("/login")

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE cart
        SET quantity = quantity + 1
        WHERE product_id = ? AND user_id = ?
    """, (product_id, session["user_id"]))

    conn.commit()
    conn.close()

    return redirect(url_for("user.cart"))


# ======================
# DECREASE
# ======================
@user_bp.route("/decrease/<int:product_id>")
def decrease(product_id):

    if "user_id" not in session:
        return redirect("/login")

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE cart
        SET quantity = quantity - 1
        WHERE product_id = ? AND user_id = ? AND quantity > 1
    """, (product_id, session["user_id"]))

    conn.commit()
    conn.close()

    return redirect(url_for("user.cart"))


# ======================
# CHECKOUT (FIXED FOR RENDER)
# ======================
@user_bp.route("/checkout")
def checkout():

    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]
    order_group = str(uuid.uuid4())

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT c.product_id, c.quantity, p.price, p.merchant_id
        FROM cart c
        JOIN products p ON c.product_id = p.id
        WHERE c.user_id = ?
    """, (user_id,))

    cart_items = cur.fetchall()

    if not cart_items:
        flash("Cart is empty ❌", "error")
        conn.close()
        return redirect("/cart")

    for item in cart_items:
        cur.execute("""
            INSERT INTO orders (
                product_id, quantity, total_price,
                user_id, merchant_id, order_group
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            item["product_id"],
            item["quantity"],
            float(item["price"]) * int(item["quantity"]),
            user_id,
            item["merchant_id"],
            order_group
        ))

    cur.execute("DELETE FROM cart WHERE user_id = ?", (user_id,))

    conn.commit()
    conn.close()

    flash("Order Placed 🎉", "success")
    return redirect("/order-success")


# ======================
# PROFILE
# ======================
@user_bp.route("/profile", methods=["GET", "POST"])
def profile():

    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = cur.fetchone()

    if not user:
        conn.close()
        return redirect("/login")

    cur.execute("""
        SELECT o.id, p.name, p.image_url, o.quantity, o.total_price, o.status
        FROM orders o
        JOIN products p ON o.product_id = p.id
        WHERE o.user_id = ?
    """, (user_id,))

    orders = cur.fetchall()

    if request.method == "POST":
        cur.execute("""
            UPDATE users
            SET name=?, address1=?, address2=?, city=?, pincode=?
            WHERE id=?
        """, (
            request.form.get("name"),
            request.form.get("address1"),
            request.form.get("address2"),
            request.form.get("city"),
            request.form.get("pincode"),
            user_id
        ))

        conn.commit()
        flash("Updated ✅", "success")
        return redirect(url_for("user.profile"))

    conn.close()

    return render_template("user/profile.html", user=user, orders=orders)


# ======================
# ALL PRODUCTS
# ======================
@user_bp.route("/all-products")
def all_products():

    if "user_id" not in session:
        return redirect("/login")

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT * FROM products ORDER BY id DESC")
    products = cur.fetchall()

    cur.execute("SELECT * FROM feedback ORDER BY id DESC")
    feedback = cur.fetchall()

    conn.close()

    return render_template(
        "user/all_products.html",
        products=products,
        feedback=feedback
    )