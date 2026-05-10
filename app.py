from flask import Flask, render_template, request, redirect, flash
from dotenv import load_dotenv
import os

# -------------------------
# LOAD ENV FIRST
# -------------------------
load_dotenv()

app = Flask(__name__)

# safe secret key
app.secret_key = os.getenv("SECRET_KEY", "dev-secret-key")


# -------------------------
# FIX: IMPORT DB INIT SAFELY
# -------------------------
from init_db import init_db
with app.app_context():
    init_db()


# -------------------------
# DB FUNCTION
# -------------------------
from db import execute


# -------------------------
# BLUEPRINTS
# -------------------------
from routes.auth import auth_bp
from routes.user import user_bp
from routes.merchant import merchant_bp

app.register_blueprint(auth_bp)
app.register_blueprint(user_bp)
app.register_blueprint(merchant_bp)


# -------------------------
# HOME PAGE
# -------------------------
@app.route("/")
def landing():
    return render_template("landing.html")


# -------------------------
# FEEDBACK ROUTE (SAFE + RENDER READY)
# -------------------------
@app.route("/add_feedback", methods=["POST"])
def add_feedback():

    try:
        product_id = request.form.get("product_id")
        user_name = request.form.get("user_name")
        rating = request.form.get("rating")
        comment = request.form.get("comment")

        if not all([product_id, user_name, rating, comment]):
            flash("Missing feedback fields!", "error")
            return redirect(request.referrer or "/all-products")

        execute(
            "INSERT INTO feedback (product_id, user_name, rating, comment) VALUES (?, ?, ?, ?)",
            (product_id, user_name, rating, comment),
            commit=True
        )

        flash("Feedback Submitted Successfully ⭐", "success")

    except Exception as e:
        print("FEEDBACK ERROR:", e)
        flash("Something went wrong!", "error")

    return redirect(request.referrer or "/all-products")


# -------------------------
# PRODUCT DETAIL PAGE (SAFE)
# -------------------------
@app.route("/product/<int:product_id>")
def product_detail(product_id):

    try:
        product = execute(
            "SELECT id, name, price, description, image_url FROM products WHERE id = ?",
            (product_id,),
            fetchone=True
        )

        if not product:
            return "Product not found", 404

        return render_template("product_detail.html", product=product)

    except Exception as e:
        print("PRODUCT ERROR:", e)
        return "Server Error", 500


# -------------------------
# RUN APP (RENDER SAFE)
# -------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)