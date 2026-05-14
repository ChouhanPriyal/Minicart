import bcrypt
from flask import Blueprint, render_template, request, redirect, session, flash
from db import get_connection

auth_bp = Blueprint("auth", __name__)


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

        conn = get_connection()
        cur = conn.cursor()

        try:
            # check if user exists
            cur.execute("SELECT id FROM users WHERE email = %s", (email,))
            existing_user = cur.fetchone()

            if existing_user:
                flash("Email already registered ❌", "error")
                return redirect("/register")

            # 🔥 FIXED: store bcrypt as STRING (NOT bytes)
            hashed_password = bcrypt.hashpw(
                password.encode('utf-8'),
                bcrypt.gensalt()
            ).decode('utf-8')

            cur.execute("""
                INSERT INTO users (name, email, password, role)
                VALUES (%s, %s, %s, %s)
            """, (name, email, hashed_password, role))

            conn.commit()

            flash("Registration Successful 🎉", "success")
            return redirect("/login")

        except Exception as e:
            conn.rollback()
            print("REGISTER ERROR:", e)
            flash("Something went wrong ❌", "error")

        finally:
            cur.close()
            conn.close()

    return render_template("auth/register.html")


# ======================
# LOGIN
# ======================
@auth_bp.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form.get("email")
        password = request.form.get("password")

        conn = get_connection()
        cur = conn.cursor()

        try:
            cur.execute("""
                SELECT id, name, email, password, role
                FROM users
                WHERE email = %s
            """, (email,))

            user = cur.fetchone()

            if not user:
                flash("User Not Found ❌", "error")
                return redirect("/login")

            stored_password = user[3]

            # 🔥 FIX: ensure correct type
            if isinstance(stored_password, memoryview):
                stored_password = stored_password.tobytes()

            if isinstance(stored_password, str):
                stored_password = stored_password.encode('utf-8')

            # verify password
            if not bcrypt.checkpw(
                password.encode('utf-8'),
                stored_password
            ):
                flash("Wrong Password ❌", "error")
                return redirect("/login")

            # session
            session["user_id"] = user[0]
            session["user_name"] = user[1]
            session["role"] = user[4]

            flash("Login Successful ✅", "success")

            if user[4] == "merchant":
                return redirect("/merchant-dashboard")
            else:
                return redirect("/user-home")

        except Exception as e:
            print("LOGIN ERROR:", e)
            flash("Server Error ❌", "error")

        finally:
            cur.close()
            conn.close()

    return render_template("auth/login.html")


# ======================
# LOGOUT
# ======================
@auth_bp.route("/logout")
def logout():

    session.clear()
    flash("Logged Out Successfully 👋", "success")
    return redirect("/login")