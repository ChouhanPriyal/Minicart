from flask import Flask, render_template, request, redirect, flash
from dotenv import load_dotenv
from init_db import init_db
import os

# -------------------------
# APP SETUP
# -------------------------
app = Flask(__name__)
load_dotenv()
init_db()

app.secret_key = os.getenv("SECRET_KEY", "dev-secret-key")


# -------------------------
# IMPORT DB FUNCTION
# -------------------------
from db import execute


# -------------------------
# REGISTER BLUEPRINTS
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
# FEEDBACK ROUTE (SAFE VERSION)
# -------------------------
@app.route("/add_feedback", methods=["POST"])
def add_feedback():

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
    return redirect(request.referrer or "/all-products")


# -------------------------
# PRODUCT DETAIL PAGE (SAFE)
# -------------------------
@app.route("/product/<int:product_id>")
def product_detail(product_id):

    product = execute(
        "SELECT id, name, price, description, image_url FROM products WHERE id = ?",
        (product_id,),
        fetchone=True
    )

    if not product:
        return "Product not found", 404

    return render_template("product_detail.html", product=product)


# -------------------------
# RUN APP
# -------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
    