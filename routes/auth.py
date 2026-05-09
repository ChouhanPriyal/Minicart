from flask import Blueprint, render_template, request, redirect, session, flash
import sqlite3

auth_bp = Blueprint("auth", __name__)


# ----------------------
# DB CONNECTION
# ----------------------
def get_db_connection():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row  # IMPORTANT
    return conn


# ======================
# REGISTER
# ======================
@auth_bp.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")
        role = request.form.get("role")

        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO users (name, email, password, role)
            VALUES (?, ?, ?, ?)
        """, (name, email, password, role))

        conn.commit()
        conn.close()

        flash("Registration Successful 🎉", "success")
        return redirect("/login")

    return render_template("auth/register.html")


# ======================
# LOGIN
# ======================
@auth_bp.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form.get("email")
        password = request.form.get("password")

        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("SELECT * FROM users WHERE email = ?", (email,))
        user = cur.fetchone()

        conn.close()

        if user:

            # ✅ SAFE ACCESS USING INDEX (ONLY if table is correct order)
            if user[3] == password:

                session["user_id"] = user[0]
                session["name"] = user[1]
                session["role"] = user[4]

                flash("Login Successful ✅", "success")

                if user[4] == "merchant":
                    return redirect("/merchant-dashboard")
                else:
                    return redirect("/user-home")

            else:
                flash("Wrong Password ❌", "error")
                return redirect("/login")

        else:
            flash("User Not Found ❌", "error")
            return redirect("/login")

    return render_template("auth/login.html")


# ======================
# LOGOUT
# ======================
@auth_bp.route("/logout")
def logout():

    session.clear()
    flash("Logged Out Successfully 👋", "success")

    return redirect("/login")