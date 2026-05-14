
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from dotenv import load_dotenv
from db import get_connection
import os
import cloudinary
import cloudinary.uploader

load_dotenv()

# =========================
# CLOUDINARY CONFIG
# =========================
cloudinary.config(
    cloud_name=os.environ.get("CLOUD_NAME"),
    api_key=os.environ.get("API_KEY"),
    api_secret=os.environ.get("API_SECRET"),
    secure=True
)

merchant_bp = Blueprint("merchant", __name__)


# =========================
# DASHBOARD
# =========================
@merchant_bp.route("/merchant-dashboard")
def merchant_dashboard():

    if "user_id" not in session or session.get("role") != "merchant":
        return redirect("/login")

    merchant_id = session["user_id"]

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT COUNT(*)
        FROM products
        WHERE merchant_id = %s
    """, (merchant_id,))

    total_products = cur.fetchone()[0]

    cur.execute("""
        SELECT COUNT(*)
        FROM orders o
        JOIN products p ON o.product_id = p.id
        WHERE p.merchant_id = %s
    """, (merchant_id,))

    total_orders = cur.fetchone()[0]

    cur.execute("""
        SELECT COUNT(*)
        FROM orders o
        JOIN products p ON o.product_id = p.id
        WHERE p.merchant_id = %s
        AND o.status = 'Pending'
    """, (merchant_id,))

    pending_orders = cur.fetchone()[0]

    cur.execute("""
        SELECT COALESCE(SUM(o.total_price), 0)
        FROM orders o
        JOIN products p ON o.product_id = p.id
        WHERE p.merchant_id = %s
    """, (merchant_id,))

    revenue = cur.fetchone()[0]

    cur.close()
    conn.close()

    return render_template(
        "merchant/dashboard.html",
        total_products=total_products,
        total_orders=total_orders,
        pending_orders=pending_orders,
        revenue=revenue
    )


# =========================
# ADD / EDIT PRODUCT
# =========================
@merchant_bp.route("/add-product", methods=["GET", "POST"])
@merchant_bp.route("/edit-product/<int:id>", methods=["GET", "POST"])
def add_product(id=None):

    if "user_id" not in session or session.get("role") != "merchant":
        return redirect("/login")

    merchant_id = session["user_id"]

    conn = get_connection()
    cur = conn.cursor()

    # GET CATEGORIES
    cur.execute("""
        SELECT DISTINCT category
        FROM products
        WHERE category IS NOT NULL
    """)

    categories = [c[0] for c in cur.fetchall()]

    product = None

    # =========================
    # EDIT MODE
    # =========================
    if id:

        cur.execute("""
            SELECT *
            FROM products
            WHERE id = %s
            AND merchant_id = %s
        """, (id, merchant_id))

        product = cur.fetchone()

        if not product:

            cur.close()
            conn.close()

            flash("Product not found ❌", "error")

            return redirect(url_for("merchant.products"))

    # =========================
    # FORM SUBMIT
    # =========================
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

            # =========================
            # EDIT PRODUCT
            # =========================
            if product:

                # IMAGE UPDATED
                if image and image.filename != "":

                    upload_result = cloudinary.uploader.upload(
                        image.read(),
                        folder="products"
                    )

                    image_url = upload_result["secure_url"]

                    cur.execute("""
                        UPDATE products
                        SET
                            name = %s,
                            price = %s,
                            description = %s,
                            category = %s,
                            image_url = %s
                        WHERE id = %s
                        AND merchant_id = %s
                    """, (
                        name,
                        float(price),
                        description,
                        category,
                        image_url,
                        id,
                        merchant_id
                    ))

                # WITHOUT IMAGE
                else:

                    cur.execute("""
                        UPDATE products
                        SET
                            name = %s,
                            price = %s,
                            description = %s,
                            category = %s
                        WHERE id = %s
                        AND merchant_id = %s
                    """, (
                        name,
                        float(price),
                        description,
                        category,
                        id,
                        merchant_id
                    ))

                conn.commit()

                cur.close()
                conn.close()

                flash("Product updated successfully ✅", "success")

                return redirect(url_for("merchant.products"))

            # =========================
            # ADD PRODUCT
            # =========================
            else:

                if not all([name, price, description, category, image]):

                    flash("All fields required ❌", "error")

                    return redirect(request.url)

                upload_result = cloudinary.uploader.upload(
                    image.read(),
                    folder="products"
                )

                image_url = upload_result["secure_url"]

                cur.execute("""
                    INSERT INTO products
                    (
                        name,
                        price,
                        description,
                        image_url,
                        merchant_id,
                        category
                    )
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (
                    name,
                    float(price),
                    description,
                    image_url,
                    merchant_id,
                    category
                ))

                conn.commit()

                cur.close()
                conn.close()

                flash("Product added successfully ✅", "success")

                return redirect(url_for("merchant.products"))

        except Exception as e:

            print("PRODUCT ERROR:", e)

            conn.rollback()

            cur.close()
            conn.close()

            flash("Something went wrong ❌", "error")

            return redirect(request.url)

    cur.close()
    conn.close()

    return render_template(
        "merchant/add-product.html",
        categories=categories,
        product=product
    )


# =========================
# PRODUCTS
# =========================
@merchant_bp.route("/products")
def products():

    if "user_id" not in session or session.get("role") != "merchant":
        return redirect("/login")

    merchant_id = session["user_id"]

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            id,
            name,
            price,
            description,
            image_url,
            category
        FROM products
        WHERE merchant_id = %s
    """, (merchant_id,))

    data = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "merchant/products.html",
        products=data
    )


# =========================
# DELETE PRODUCT
# =========================
@merchant_bp.route("/delete-product/<int:id>")
def delete_product(id):

    if "user_id" not in session or session.get("role") != "merchant":
        return redirect("/login")

    merchant_id = session["user_id"]

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        DELETE FROM products
        WHERE id = %s
        AND merchant_id = %s
    """, (id, merchant_id))

    conn.commit()

    cur.close()
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

    conn = get_connection()
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
        WHERE p.merchant_id = %s
    """, (merchant_id,))

    orders = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "merchant/orders.html",
        orders=orders
    )


# =========================
# UPDATE ORDER
# =========================
@merchant_bp.route("/update-order/<int:order_id>/<status>")
def update_order(order_id, status):

    if "user_id" not in session or session.get("role") != "merchant":
        return redirect("/login")

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE orders
        SET status = %s
        WHERE id = %s
    """, (status, order_id))

    conn.commit()

    cur.close()
    conn.close()

    flash("Order updated ✅", "success")

    return redirect(url_for("merchant.orders"))


# =========================
# PROFILE + CHANGE PASSWORD
# =========================
@merchant_bp.route("/merchant/profile", methods=["GET", "POST"])
def merchant_profile():

    if "user_id" not in session or session.get("role") != "merchant":
        return redirect("/login")

    merchant_id = session["user_id"]

    conn = get_connection()
    cur = conn.cursor()

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

    if request.method == "POST":

        # CHANGE PASSWORD
        if request.form.get("form_type") == "password":

            current_password = request.form.get("current_password")
            new_password = request.form.get("new_password")
            confirm_password = request.form.get("confirm_password")

            cur.execute("""
                SELECT password
                FROM users
                WHERE id = %s
            """, (merchant_id,))

            user = cur.fetchone()

            if not user or user[0] != current_password:

                cur.close()
                conn.close()

                flash("Current password incorrect ❌", "error")

                return redirect(url_for("merchant.merchant_profile"))

            if new_password != confirm_password:

                cur.close()
                conn.close()

                flash("Passwords do not match ❌", "error")

                return redirect(url_for("merchant.merchant_profile"))

            cur.execute("""
                UPDATE users
                SET password = %s
                WHERE id = %s
            """, (new_password, merchant_id))

            conn.commit()

            cur.close()
            conn.close()

            flash("Password updated successfully ✅", "success")

            return redirect(url_for("merchant.merchant_profile"))

        # PROFILE UPDATE
        else:

            name = request.form.get("name")
            address1 = request.form.get("address1")
            address2 = request.form.get("address2")
            city = request.form.get("city")
            pincode = request.form.get("pincode")

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
                name,
                address1,
                address2,
                city,
                pincode,
                merchant_id
            ))

            conn.commit()

            cur.close()
            conn.close()

            flash("Profile Updated ✅", "success")

            return redirect(url_for("merchant.merchant_profile"))

    cur.close()
    conn.close()

    return render_template(
        "merchant/profile.html",
        merchant=merchant
    )


# =========================
# FEEDBACK
# =========================
@merchant_bp.route("/merchant-feedback")
def merchant_feedback():

    if "user_id" not in session or session.get("role") != "merchant":
        return redirect("/login")

    merchant_id = session["user_id"]

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            f.id,
            p.name,
            p.image_url,
            f.user_name,
            f.rating,
            f.comment
        FROM feedback f
        JOIN products p ON f.product_id = p.id
        WHERE p.merchant_id = %s
        ORDER BY f.id DESC
    """, (merchant_id,))

    feedbacks = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "merchant/merchant_feedback.html",
        feedbacks=feedbacks
    )


# =========================
# REJECT ORDER
# =========================
@merchant_bp.route("/reject-order/<int:order_id>")
def reject_order(order_id):

    if "user_id" not in session or session.get("role") != "merchant":
        return redirect("/login")

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE orders
        SET status = 'Rejected'
        WHERE id = %s
    """, (order_id,))

    conn.commit()

    cur.close()
    conn.close()

    flash("Order Rejected ❌", "success")

    return redirect(url_for("merchant.orders"))

