from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from extensions import mysql
import cloudinary
import cloudinary.uploader

# ✅ CLOUDINARY CONFIG
cloudinary.config(
    cloud_name="dkz4irhst",
    api_key="253841239949845",
    api_secret="PuIlQcJzemhgOzd5TBJUIiE3qNk",
    secure=True
)

merchant_bp = Blueprint("merchant", __name__)


# =========================
# 🧑‍💼 DASHBOARD
# =========================
@merchant_bp.route("/merchant-dashboard")
def merchant_dashboard():

    if "user_id" not in session or session.get("role") != "merchant":
        return redirect("/login")

    merchant_id = session["user_id"]
    cur = mysql.connection.cursor()

    cur.execute("SELECT COUNT(*) FROM products WHERE merchant_id=%s", (merchant_id,))
    total_products = cur.fetchone()[0]

    cur.execute("""
        SELECT COUNT(*) 
        FROM orders o
        JOIN products p ON o.product_id = p.id
        WHERE p.merchant_id=%s
    """, (merchant_id,))
    total_orders = cur.fetchone()[0]

    cur.execute("""
        SELECT COUNT(*)
        FROM orders o
        JOIN products p ON o.product_id = p.id
        WHERE p.merchant_id=%s AND o.status='pending'
    """, (merchant_id,))
    pending_orders = cur.fetchone()[0]

    cur.execute("""
        SELECT IFNULL(SUM(o.total_price),0)
        FROM orders o
        JOIN products p ON o.product_id = p.id
        WHERE p.merchant_id=%s
    """, (merchant_id,))
    revenue = cur.fetchone()[0]

    cur.close()

    return render_template(
        "merchant/dashboard.html",
        total_products=total_products,
        total_orders=total_orders,
        pending_orders=pending_orders,
        revenue=revenue
    )


# =========================
# ➕ ADD PRODUCT (WITH CATEGORY)
# =========================
@merchant_bp.route("/add-product", methods=["GET", "POST"])
def add_product():

    if "user_id" not in session or session.get("role") != "merchant":
        return redirect("/login")

    merchant_id = session["user_id"]
    cur = mysql.connection.cursor()

    # ✅ GET EXISTING CATEGORIES
    cur.execute("SELECT DISTINCT category FROM products WHERE category IS NOT NULL")
    categories = [c[0] for c in cur.fetchall()]

    print("CATEGORIES:", categories)  # debug

    if request.method == "POST":

        name = request.form.get("name")
        price = request.form.get("price")
        description = request.form.get("description")
        category = request.form.get("category")
        new_category = request.form.get("new_category")

        # ✅ USE NEW CATEGORY IF ENTERED
        if new_category:
            category = new_category

        image = request.files.get("image")

        if not image:
            flash("Image not selected ❌", "error")
            return redirect(request.url)

        upload_result = cloudinary.uploader.upload(
            image.read(),
            folder="products"
        )

        image_url = upload_result.get("secure_url")

        # ✅ INSERT WITH CATEGORY
        cur.execute("""
            INSERT INTO products (name, price, description, image_url, merchant_id, category)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (name, price, description, image_url, merchant_id, category))

        mysql.connection.commit()
        cur.close()

        flash("Product added successfully ✅", "success")
        return redirect(url_for("merchant.products"))

    return render_template("merchant/add-product.html", categories=categories)


# =========================
# 📦 PRODUCTS
# =========================
@merchant_bp.route("/products")
def products():

    if "user_id" not in session or session.get("role") != "merchant":
        return redirect("/login")

    merchant_id = session["user_id"]

    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT id, name, price, description, image_url, category
        FROM products 
        WHERE merchant_id=%s
    """, (merchant_id,))

    data = cur.fetchall()
    cur.close()

    return render_template("merchant/products.html", products=data)


# =========================
# ❌ DELETE PRODUCT
# =========================
@merchant_bp.route("/delete-product/<int:id>")
def delete_product(id):

    if "user_id" not in session or session.get("role") != "merchant":
        return redirect("/login")

    merchant_id = session["user_id"]

    cur = mysql.connection.cursor()
    cur.execute("""
        DELETE FROM products 
        WHERE id=%s AND merchant_id=%s
    """, (id, merchant_id))

    mysql.connection.commit()
    cur.close()

    flash("Product deleted ❌", "error")
    return redirect(url_for("merchant.products"))


# =========================
# 🧾 ORDERS
# =========================
@merchant_bp.route("/orders")
def orders():

    if "user_id" not in session or session.get("role") != "merchant":
        return redirect("/login")

    merchant_id = session["user_id"]

    cur = mysql.connection.cursor()

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
        WHERE p.merchant_id=%s
    """, (merchant_id,))

    orders = cur.fetchall()
    cur.close()

    return render_template("merchant/orders.html", orders=orders)


# =========================
# 🔄 UPDATE ORDER
# =========================
@merchant_bp.route("/update-order/<int:order_id>/<status>")
def update_order(order_id, status):

    if "user_id" not in session or session.get("role") != "merchant":
        return redirect("/login")

    merchant_id = session["user_id"]

    cur = mysql.connection.cursor()

    cur.execute("""
        UPDATE orders o
        JOIN products p ON o.product_id = p.id
        SET o.status=%s
        WHERE o.id=%s AND p.merchant_id=%s
    """, (status, order_id, merchant_id))

    mysql.connection.commit()
    cur.close()

    flash("Order updated ✅", "success")
    return redirect(url_for("merchant.orders"))

# 👤 MERCHANT PROFILE
@merchant_bp.route("/merchant/profile", methods=["GET", "POST"])
def merchant_profile():

    # 🔐 LOGIN CHECK
    if "user_id" not in session or session.get("role") != "merchant":
        return redirect("/login")

    merchant_id = session["user_id"]

    cur = mysql.connection.cursor()

    # ✅ GET MERCHANT DATA
    cur.execute("""
        SELECT 
            name,
            email,
            address1,
            address2,
            city,
            pincode
        FROM users
        WHERE id = %s
    """, (merchant_id,))

    merchant = cur.fetchone()

    # ✅ UPDATE PROFILE
    if request.method == "POST":

        name = request.form.get("name")
        address1 = request.form.get("address1")
        address2 = request.form.get("address2")
        city = request.form.get("city")
        pincode = request.form.get("pincode")

        cur.execute("""
            UPDATE users
            SET
                name=%s,
                address1=%s,
                address2=%s,
                city=%s,
                pincode=%s
            WHERE id=%s
        """, (
            name,
            address1,
            address2,
            city,
            pincode,
            merchant_id
        ))

        mysql.connection.commit()

        flash("Profile Updated Successfully ✅", "success")

        cur.close()

        return redirect(url_for("merchant.merchant/profile"))

    cur.close()

    return render_template(
        "merchant/profile.html",
        merchant=merchant
    )
    
# ⭐ MERCHANT FEEDBACK
@merchant_bp.route("/merchant-feedback")
def merchant_feedback():

    # 🔐 LOGIN CHECK
    if "user_id" not in session or session.get("role") != "merchant":
        return redirect("/login")

    merchant_id = session["user_id"]

    cur = mysql.connection.cursor()

    # ✅ GET FEEDBACK OF MERCHANT PRODUCTS
    cur.execute("""
        SELECT
            f.id,
            p.name,
            p.image_url,
            f.user_name,
            f.rating,
            f.comment,
            f.created_at
        FROM feedback f
        JOIN products p ON f.product_id = p.id
        WHERE p.merchant_id = %s
        ORDER BY f.id DESC
    """, (merchant_id,))

    feedbacks = cur.fetchall()

    cur.close()

    return render_template("merchant/merchant_feedback.html", feedbacks=feedbacks)