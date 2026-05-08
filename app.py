from flask import Flask, render_template, redirect, request, session, flash
from extensions import mysql

app = Flask(__name__)

#  secret key
app.secret_key = "mysecret123"

#  DB config
app.config.from_pyfile('config.py')

# init mysql
mysql.init_app(app)

# import blueprints
from routes.auth import auth_bp
from routes.user import user_bp
from routes.merchant import merchant_bp

# register blueprints
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

    product_id = request.form["product_id"]
    user_name = request.form["user_name"]
    rating = request.form["rating"]
    comment = request.form["comment"]

    cursor = mysql.connection.cursor()
    cursor.execute("""
        INSERT INTO feedback (product_id, user_name, rating, comment)
        VALUES (%s, %s, %s, %s)
    """, (product_id, user_name, rating, comment))

    mysql.connection.commit()
    cursor.close()

    # ⭐ POPUP
    flash("Feedback Submitted Successfully ⭐", "success")

    return redirect(request.referrer or "/all-products")


# -------------------------
# FETCH FEEDBACK
# -------------------------
def get_feedback():
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM feedback")
    data = cursor.fetchall()
    cursor.close()
    return data


# -------------------------
# FETCH PRODUCTS
# -------------------------
def get_all_products():
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM products")
    data = cursor.fetchall()
    cursor.close()
    return data


# -------------------------
# PRODUCT DETAIL PAGE
# -------------------------
@app.route("/product/<int:product_id>")
def product_detail(product_id):

    cursor = mysql.connection.cursor()

    cursor.execute("""
        SELECT id, name, price, description, image_url
        FROM products
        WHERE id = %s
    """, (product_id,))

    product = cursor.fetchone()
    cursor.close()

    return render_template("product_detail.html", product=product)


# -------------------------
# RUN APP
# -------------------------
if __name__ == "__main__":
    print("\n🔥 ROUTES:", app.url_map, "\n")
    app.run(host="0.0.0.0", port=5000, debug=True)