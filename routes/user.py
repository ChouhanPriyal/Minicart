
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from db import get_connection
import uuid

user_bp = Blueprint("user", __name__)


# ======================
# HOME PAGE
# ======================
@user_bp.route("/user-home")
def home():

    if "user_id" not in session or session.get("role") != "user":
        return redirect("/login")

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, name, price, description, image_url
        FROM products
        ORDER BY id DESC
    """)

    products = cur.fetchall()

    cur.close()
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

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT id FROM cart
        WHERE product_id = %s AND user_id = %s
    """, (product_id, user_id))

    existing = cur.fetchone()

    if existing:

        cur.execute("""
            UPDATE cart
            SET quantity = quantity + 1
            WHERE product_id = %s AND user_id = %s
        """, (product_id, user_id))

    else:

        cur.execute("""
            INSERT INTO cart (product_id, quantity, user_id)
            VALUES (%s, %s, %s)
        """, (product_id, 1, user_id))

    conn.commit()

    cur.close()
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

    conn = get_connection()
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
        WHERE c.user_id = %s
    """, (user_id,))

    cart_items = cur.fetchall()

    total = 0

    for item in cart_items:
        total += float(item[2]) * int(item[5])

    cur.close()
    conn.close()

    return render_template(
        "user/cart.html",
        cart_items=cart_items,
        total=total
    )


# ======================
# REMOVE FROM CART
# ======================
@user_bp.route("/remove_from_cart/<int:product_id>")
def remove_from_cart(product_id):

    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        DELETE FROM cart
        WHERE product_id = %s AND user_id = %s
    """, (product_id, user_id))

    conn.commit()

    cur.close()
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

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE cart
        SET quantity = quantity + 1
        WHERE product_id = %s AND user_id = %s
    """, (product_id, session["user_id"]))

    conn.commit()

    cur.close()
    conn.close()

    return redirect(url_for("user.cart"))


# ======================
# DECREASE
# ======================
@user_bp.route("/decrease/<int:product_id>")
def decrease(product_id):

    if "user_id" not in session:
        return redirect("/login")

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE cart
        SET quantity = quantity - 1
        WHERE product_id = %s
        AND user_id = %s
        AND quantity > 1
    """, (product_id, session["user_id"]))

    conn.commit()

    cur.close()
    conn.close()

    return redirect(url_for("user.cart"))


# ======================
# CHECKOUT
# ======================
@user_bp.route("/checkout")
def checkout():

    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]

    order_group = "ORD" + str(uuid.uuid4())[:8].upper()

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            c.product_id,
            c.quantity,
            p.price,
            p.merchant_id
        FROM cart c
        JOIN products p ON c.product_id = p.id
        WHERE c.user_id = %s
    """, (user_id,))

    cart_items = cur.fetchall()

    if not cart_items:

        flash("Cart is empty ❌", "error")

        cur.close()
        conn.close()

        return redirect("/cart")

    for item in cart_items:

        cur.execute("""
            INSERT INTO orders (
                product_id,
                quantity,
                total_price,
                user_id,
                merchant_id,
                order_group
            )
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            item[0],
            item[1],
            float(item[2]) * int(item[1]),
            user_id,
            item[3],
            order_group
        ))

    cur.execute("""
        DELETE FROM cart
        WHERE user_id = %s
    """, (user_id,))

    conn.commit()

    cur.close()
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

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT name, email, address1, address2, city, pincode
        FROM users
        WHERE id = %s
    """, (user_id,))

    user = cur.fetchone()

    cur.execute("""
        SELECT
            o.id,
            p.name,
            p.image_url,
            o.quantity,
            o.total_price,
            o.status
        FROM orders o
        JOIN products p ON o.product_id = p.id
        WHERE o.user_id = %s
        ORDER BY o.id DESC
    """, (user_id,))

    orders = cur.fetchall()

    if request.method == "POST":

        cur.execute("""
            UPDATE users
            SET
                name = %s,
                address1 = %s,
                address2 = %s,
                city = %s,
                pincode = %s
            WHERE id = %s
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

        cur.close()
        conn.close()

        return redirect(url_for("user.profile"))

    cur.close()
    conn.close()

    return render_template(
        "user/profile.html",
        user=user,
        orders=orders
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

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT DISTINCT category
        FROM products
        WHERE category IS NOT NULL
        AND category != ''
    """)

    categories = cur.fetchall()

    query = """
        SELECT
            id,
            name,
            price,
            description,
            image_url,
            category
        FROM products
        WHERE 1=1
    """

    params = []

    if search:
        query += " AND name ILIKE %s"
        params.append(f"%{search}%")

    if selected_category:
        query += " AND category = %s"
        params.append(selected_category)

    query += " ORDER BY id DESC"

    cur.execute(query, tuple(params))

    products = cur.fetchall()

    cur.execute("""
        SELECT *
        FROM feedback
        ORDER BY id DESC
    """)

    feedback = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "user/all_products.html",
        products=products,
        feedback=feedback,
        categories=categories,
        selected_category=selected_category,
        search=search
    )


# ======================
# ORDER SUCCESS
# ======================
@user_bp.route("/order-success")
def order_success():

    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            name,
            address1,
            address2,
            city,
            pincode
        FROM users
        WHERE id = %s
    """, (user_id,))

    user = cur.fetchone()

    cur.execute("""
        SELECT order_group
        FROM orders
        WHERE user_id = %s
        ORDER BY id DESC
        LIMIT 1
    """, (user_id,))

    latest = cur.fetchone()

    if not latest:

        cur.close()
        conn.close()

        flash("No recent order found ❌", "error")

        return redirect("/cart")

    order_group = latest[0]

    cur.execute("""
        SELECT
            o.id,
            p.name,
            p.price,
            p.image_url,
            o.quantity,
            o.total_price,
            o.status
        FROM orders o
        JOIN products p ON o.product_id = p.id
        WHERE o.order_group = %s
    """, (order_group,))

    items = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "user/order_success.html",
        user=user,
        order_id=order_group,
        items=items
    )

