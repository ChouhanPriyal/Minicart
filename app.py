from flask import Flask, render_template, request, redirect, session, flash
from dotenv import load_dotenv
import os

app = Flask(__name__)
load_dotenv()
app.secret_key = os.getenv("SECRET_KEY")


# -------------------------
# IMPORT DB FUNCTION
# -------------------------
from db import execute


# -------------------------
# IMPORT BLUEPRINTS
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
# FEEDBACK INSERT
# -------------------------
@app.route("/add_feedback", methods=["POST"])
def add_feedback():

    execute(
        "INSERT INTO feedback (product_id, user_name, rating, comment) VALUES (?, ?, ?, ?)",
        (
            request.form["product_id"],
            request.form["user_name"],
            request.form["rating"],
            request.form["comment"]
        ),
        commit=True
    )

    flash("Feedback Submitted Successfully ⭐", "success")

    return redirect(request.referrer or "/all-products")


# -------------------------
# PRODUCT DETAIL PAGE
# -------------------------
@app.route("/product/<int:product_id>")
def product_detail(product_id):

    product = execute(
        "SELECT id, name, price, description, image_url FROM products WHERE id = ?",
        (product_id,),
        fetchone=True
    )

    return render_template("product_detail.html", product=product)


# -------------------------
# DEBUG ROUTES
# -------------------------
print("\n🔥 ROUTES LOADED:")
print(app.url_map)


# -------------------------
# RUN APP
# -------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)