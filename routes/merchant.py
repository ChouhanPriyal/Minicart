from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from dotenv import load_dotenv
import os
import sqlite3
import cloudinary
import cloudinary.uploader

load_dotenv()

# =========================
# CLOUDINARY CONFIG
# =========================
cloudinary.config(
    cloud_name=os.getenv("CLOUD_NAME"),
    api_key=os.getenv("API_KEY"),
    api_secret=os.getenv("API_SECRET"),
    secure=True
)

merchant_bp = Blueprint("merchant", __name__)

# =========================
# FIXED DB PATH (IMPORTANT FOR RENDER)
# =========================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "../database.db")


def get_db_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


# =========================
# DASHBOARD
# =========================
@merchant_bp.route("/merchant-dashboard")
def merchant_dashboard():

    if "user_id" not in session or session.get("role") != "merchant":
        return redirect("/login")

    merchant_id = session["user_id"]

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM products WHERE merchant_id = ?", (merchant_id,))
    total_products = cur.fetchone()[0]

    cur.execute("""
        SELECT COUNT(*)
        FROM orders o
        JOIN products p ON o.product_id = p.id
        WHERE p.merchant_id = ?
    """, (merchant_id,))
    total_orders = cur.fetchone()[0]

    cur.execute("""
        SELECT COUNT(*)
        FROM orders o
        JOIN products p ON o.product_id = p.id
        WHERE p.merchant_id = ? AND o.status = 'Pending'
    """, (merchant_id,))
    pending_orders = cur.fetchone()[0]

    cur.execute("""
        SELECT IFNULL(SUM(o.total_price), 0)
        FROM orders o
        JOIN products p ON o.product_id = p.id
        WHERE p.merchant_id = ?
    """, (merchant_id,))
    revenue = cur.fetchone()[0]

    conn.close()

    return render_template(
        "merchant/dashboard.html",
        total_products=total_products,
        total_orders=total_orders,
        pending_orders=pending_orders,
        revenue=revenue
    )


# =========================
# ADD PRODUCT (FIXED)
# =========================
@merchant_bp.route("/add-product", methods=["GET", "POST"])
def add_product():

    if "user_id" not in session or session.get("role") != "merchant":
        return redirect("/login")

    merchant_id = session["user_id"]

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT DISTINCT category FROM products WHERE category IS NOT NULL")
    categories = [c[0] for c in cur.fetchall()]

    if request.method == "POST":

        try:
            name = request.form.get("name")
            price = request.form.get("price")
            description = request.form.get("description")
            category = request.form.get("category")
            new_category = request.form.get("new_category")

            if new_category:
                category = new_category

            image = request.files.get("image")

            if not all([name, price, description, category, image]):
                flash("All fields required ❌", "error")
                return redirect(request.url)

            # FIXED CLOUDINARY UPLOAD
            upload_result = cloudinary.uploader.upload(
                image.read(),
                folder="products"
            )

            image_url = upload_result["secure_url"]

            cur.execute("""
                INSERT INTO products
                (name, price, description, image_url, merchant_id, category)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                name,
                float(price),
                description,
                image_url,
                merchant_id,
                category
            ))

            conn.commit()
            conn.close()

            flash("Product added successfully ✅", "success")
            return redirect(url_for("merchant.products"))

        except Exception as e:
            print("ADD PRODUCT ERROR:", e)
            conn.rollback()
            flash("Server error ❌ check logs", "error")
            return redirect(request.url)

    conn.close()
    return render_template("merchant/add-product.html", categories=categories)


# =========================
# PRODUCTS
# =========================
@merchant_bp.route("/products")
def products():

    if "user_id" not in session or session.get("role") != "merchant":
        return redirect("/login")

    merchant_id = session["user_id"]

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, name, price, description, image_url, category
        FROM products
        WHERE merchant_id = ?
    """, (merchant_id,))

    data = cur.fetchall()
    conn.close()

    return render_template("merchant/products.html", products=data)


# =========================
# DELETE PRODUCT
# =========================
@merchant_bp.route("/delete-product/<int:id>")
def delete_product(id):

    if "user_id" not in session or session.get("role") != "merchant":
        return redirect("/login")

    merchant_id = session["user_id"]

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        DELETE FROM products
        WHERE id = ? AND merchant_id = ?
    """, (id, merchant_id))

    conn.commit()
    conn.close()

    flash("Product deleted ❌", "error")
    return redirect(url_for("merchant.products"))


# =========================
# ORDERS
# =========================
@merchant_bp.route("/orders")
def orders():

    if "user_id" not in session or session.get("role") != "merchant":
        return redirect("/login")

    merchant_id = session["user_id"]

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT 
            o.id,
            p.name,
            p.image_url,
            p.price,
            o.quantity,
            o.total_price,
            o.status,
            u.name
        FROM orders o
        JOIN products p ON o.product_id = p.id
        JOIN users u ON o.user_id = u.id
        WHERE p.merchant_id = ?
    """, (merchant_id,))

    orders = cur.fetchall()
    conn.close()

    return render_template("merchant/orders.html", orders=orders)


# =========================
# UPDATE ORDER
# =========================
@merchant_bp.route("/update-order/<int:order_id>/<status>")
def update_order(order_id, status):

    if "user_id" not in session or session.get("role") != "merchant":
        return redirect("/login")

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE orders
        SET status = ?
        WHERE id = ?
    """, (status, order_id))

    conn.commit()
    conn.close()

    flash("Order updated ✅", "success")
    return redirect(url_for("merchant.orders"))


# =========================
# PROFILE
# =========================
@merchant_bp.route("/merchant/profile", methods=["GET", "POST"])
def merchant_profile():

    if "user_id" not in session or session.get("role") != "merchant":
        return redirect("/login")

    merchant_id = session["user_id"]

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT name, email, address1, address2, city, pincode
        FROM users
        WHERE id = ?
    """, (merchant_id,))

    merchant = cur.fetchone()

    if request.method == "POST":

        name = request.form.get("name")
        address1 = request.form.get("address1")
        address2 = request.form.get("address2")
        city = request.form.get("city")
        pincode = request.form.get("pincode")

        cur.execute("""
            UPDATE users
            SET name = ?, address1 = ?, address2 = ?, city = ?, pincode = ?
            WHERE id = ?
        """, (name, address1, address2, city, pincode, merchant_id))

        conn.commit()
        conn.close()

        flash("Profile Updated ✅", "success")
        return redirect(url_for("merchant.merchant_profile"))

    conn.close()
    return render_template("merchant/profile.html", merchant=merchant)


# =========================
# FEEDBACK
# =========================
@merchant_bp.route("/merchant-feedback")
def merchant_feedback():

    if "user_id" not in session or session.get("role") != "merchant":
        return redirect("/login")

    merchant_id = session["user_id"]

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT f.id, p.name, p.image_url, f.user_name, f.rating, f.comment
        FROM feedback f
        JOIN products p ON f.product_id = p.id
        WHERE p.merchant_id = ?
        ORDER BY f.id DESC
    """, (merchant_id,))

    feedbacks = cur.fetchall()
    conn.close()

    return render_template("merchant/merchant_feedback.html", feedbacks=feedbacks)


# =========================
# REJECT ORDER
# =========================
@merchant_bp.route("/reject-order/<int:order_id>")
def reject_order(order_id):

    if "user_id" not in session or session.get("role") != "merchant":
        return redirect("/login")

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE orders
        SET status = 'Rejected'
        WHERE id = ?
    """, (order_id,))

    conn.commit()
    conn.close()

    flash("Order Rejected ❌", "success")
    return redirect(url_for("merchant.orders"))