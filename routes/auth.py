from flask import Blueprint, render_template, request, redirect, session, flash
from extensions import mysql

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

        cur = mysql.connection.cursor()

        cur.execute(
            "INSERT INTO users (name, email, password, role) VALUES (%s, %s, %s, %s)",
            (name, email, password, role)
        )

        mysql.connection.commit()
        cur.close()

        # ⭐ POPUP
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

        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE email=%s", (email,))
        user = cur.fetchone()
        cur.close()

        if user:

            # 0=id, 1=name, 2=email, 3=password, 4=role
            if user[3] == password:

                session["user_id"] = user[0]
                session["name"] = user[1]
                session["role"] = user[4]

                flash("Login Successful ✅", "success")   # ⭐ POPUP

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

    flash("Logged Out Successfully 👋", "success")   # ⭐ POPUP

    return redirect("/login")