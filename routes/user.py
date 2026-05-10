from flask import Blueprint, render_template, request, redirect, url_for, session, flash
import sqlite3
import uuid

user_bp = Blueprint("user", __name__)


# -------------------------
# DB CONNECTION
# -------------------------
def get_db_connection():
    conn = sqlite3.connect("database.db")
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

    cur.execute("""
        SELECT id, name, price, description, image_url
        FROM products
        ORDER BY id DESC
    """)

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
        SELECT *
        FROM cart
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
        SELECT
            p.id,
            p.name,
            p.price,
            p.description,
            p.image_url,
            c.quantity
        FROM cart c
        JOIN products p ON c.product_id = p.id
        WHERE c.user_id = ?
    """, (user_id,))

    cart_items = cur.fetchall()

    # SAFE TOTAL CALCULATION
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
# INCREASE QUANTITY
# ======================
@user_bp.route("/increase/<int:product_id>")
def increase(product_id):

    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE cart
        SET quantity = quantity + 1
        WHERE product_id = ? AND user_id = ?
    """, (product_id, user_id))

    conn.commit()
    conn.close()

    return redirect(url_for("user.cart"))


# ======================
# DECREASE QUANTITY
# ======================
@user_bp.route("/decrease/<int:product_id>")
def decrease(product_id):

    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE cart
        SET quantity = quantity - 1
        WHERE product_id = ? AND user_id = ? AND quantity > 1
    """, (product_id, user_id))

    conn.commit()
    conn.close()

    return redirect(url_for("user.cart"))


# ======================
# CHECKOUT (FIXED)
# ======================
@user_bp.route("/checkout")
def checkout():

    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]

    conn = get_db_connection()
    cur = conn.cursor()

    order_group = str(uuid.uuid4())

    cur.execute("""
        SELECT
            c.product_id,
            c.quantity,
            p.price,
            p.merchant_id
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

        total_price = float(item["price"]) * int(item["quantity"])

        cur.execute("""
            INSERT INTO orders (
                product_id,
                quantity,
                total_price,
                user_id,
                merchant_id,
                order_group
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            item["product_id"],
            item["quantity"],
            total_price,
            user_id,
            item["merchant_id"],
            order_group
        ))

    cur.execute("""
        DELETE FROM cart
        WHERE user_id = ?
    """, (user_id,))

    conn.commit()
    conn.close()

    flash("Order Placed Successfully 🎉", "success")
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

    cur.execute("""
        SELECT name, email, address1, address2, city, pincode
        FROM users
        WHERE id = ?
    """, (user_id,))

    user = cur.fetchone()

    if not user:
        conn.close()
        return redirect("/login")

    cur.execute("""
        SELECT
            o.id,
            p.name,
            p.image_url,
            p.price,
            o.quantity,
            o.total_price,
            o.status
        FROM orders o
        JOIN products p ON o.product_id = p.id
        WHERE o.user_id = ?
        ORDER BY o.id DESC
    """, (user_id,))

    orders = cur.fetchall()

    if request.method == "POST":

        cur.execute("""
            UPDATE users
            SET name = ?, address1 = ?, address2 = ?, city = ?, pincode = ?
            WHERE id = ?
        """, (
            request.form.get("name"),
            request.form.get("address1"),
            request.form.get("address2"),
            request.form.get("city"),
            request.form.get("pincode"),
            user_id
        ))

        conn.commit()

        flash("Profile Updated ✅", "success")
        conn.close()

        return redirect(url_for("user.profile"))

    conn.close()

    return render_template("user/profile.html", user=user, orders=orders)


# ======================
# ORDER SUCCESS
# ======================
@user_bp.route("/order-success")
def order_success():

    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT name, address1, address2, city, pincode
        FROM users
        WHERE id = ?
    """, (user_id,))

    user = cur.fetchone()

    cur.execute("""
        SELECT order_group
        FROM orders
        WHERE user_id = ?
        ORDER BY id DESC
        LIMIT 1
    """, (user_id,))

    latest = cur.fetchone()

    if not latest:
        return redirect("/cart")

    order_group = latest["order_group"]

    cur.execute("""
        SELECT
            o.id,
            p.name,
            p.price,
            p.image_url,
            o.quantity
        FROM orders o
        JOIN products p ON o.product_id = p.id
        WHERE o.order_group = ?
    """, (order_group,))

    items = cur.fetchall()

    conn.close()

    return render_template(
        "user/order_success.html",
        user=user,
        order_id=order_group,
        items=items
    )


# ======================
# ALL PRODUCTS
# ======================
@user_bp.route("/all-products")
def all_products():

    if "user_id" not in session:
        return redirect("/login")

    search = request.args.get("search", "")
    selected_category = request.args.get("category", "")

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT DISTINCT category
        FROM products
        WHERE category IS NOT NULL
    """)

    categories = cur.fetchall()

    query = """
        SELECT id, name, price, description, image_url
        FROM products
        WHERE 1=1
    """

    params = []

    if search:
        query += " AND name LIKE ?"
        params.append(f"%{search}%")

    if selected_category:
        query += " AND category = ?"
        params.append(selected_category)

    cur.execute(query, params)
    products = cur.fetchall()

    cur.execute("""
        SELECT product_id, user_name, rating, comment
        FROM feedback
    """)

    feedback = cur.fetchall()

    conn.close()

    return render_template(
        "user/all_products.html",
        products=products,
        categories=categories,
        selected_category=selected_category,
        search=search,
        feedback=feedback
    )