from flask import Flask, render_template, request, redirect, session, flash
from config import db, cursor
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)
app.secret_key = "secret123"

UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@app.route('/')
def home():
    search = request.args.get('search')

    if search and search.strip() != "":
        query = "%" + search + "%"
        cursor.execute("""
            SELECT * FROM products
            WHERE LOWER(name) LIKE LOWER(%s)
            OR LOWER(description) LIKE LOWER(%s)
        """, (query, query))
    else:
        cursor.execute("SELECT * FROM products")

    products = cursor.fetchall()

    cart_count = 0
    if 'user_id' in session:
        cursor.execute(
            "SELECT SUM(quantity) as total FROM cart WHERE user_id=%s",
            (session['user_id'],)
        )
        result = cursor.fetchone()
        cart_count = result['total'] if result['total'] else 0

    return render_template('home.html', products=products, cart_count=cart_count)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])

        cursor.execute("""
            INSERT INTO users (name, email, password)
            VALUES (%s, %s, %s)
        """, (name, email, password))

        db.commit()
        return redirect('/login')

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    next_page = request.args.get('next')

    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
        user = cursor.fetchone()
        
        print("LOGIN USER:", user)
        if user and check_password_hash(user['password'], password):

            session['user_id'] = user['id']
            session['role'] = user['role']
            session['name'] = user['name']

            # ✅ If redirected from another page (like cart), go there
            if next_page:
                return redirect(next_page)

            # ✅ Merchant → merchant dashboard
            if user['role'] == 'merchant':
                return redirect('/')

            # ✅ User → HOME PAGE (FIXED)
            return redirect('/')

        return "Invalid credentials"

    return render_template('login.html')

@app.route('/add-product', methods=['GET', 'POST'])
def add_product():
    if 'user_id' not in session or session.get('role') != 'merchant':
        return "Unauthorized"

    if request.method == 'POST':
        name = request.form['name']
        price = request.form['price']
        description = request.form['description']

        image = request.files['image']

        if image.filename == "":
            return "No image selected"

        filename = secure_filename(image.filename)
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        image.save(image_path)

        cursor.execute("""
            INSERT INTO products (name, price, description, image, merchant_id)
            VALUES (%s, %s, %s, %s, %s)
        """, (name, price, description, filename, session['user_id']))

        db.commit()
        return redirect('/')

    return render_template('add_product.html')


@app.route('/add-to-cart/<int:product_id>')
def add_to_cart(product_id):
    if 'user_id' not in session:
        return redirect('/login')

    user_id = session['user_id']

    cursor.execute("SELECT * FROM cart WHERE user_id=%s AND product_id=%s",
                   (user_id, product_id))
    item = cursor.fetchone()

    if item:
        cursor.execute(
            "UPDATE cart SET quantity = quantity + 1 WHERE id=%s",
            (item['id'],)
        )
    else:
        cursor.execute(
            "INSERT INTO cart (user_id, product_id, quantity) VALUES (%s,%s,1)",
            (user_id, product_id)
        )

    db.commit()
    return redirect('/')


@app.route('/product/<int:product_id>')
def product_detail(product_id):

    cursor.execute("SELECT * FROM products WHERE id=%s", (product_id,))
    product = cursor.fetchone()

    if not product:
        return "Product not found"

    return render_template('product_detail.html', product=product)


@app.route('/cart')
def cart():
    if 'user_id' not in session:
        return redirect('/login')

    user_id = session['user_id']

    cursor.execute("""
        SELECT p.name, p.price, p.image, p.description, c.quantity, c.id
        FROM cart c
        JOIN products p ON c.product_id = p.id
        WHERE c.user_id = %s
    """, (user_id,))

    cart_items = cursor.fetchall()

    total_price = sum(item['price'] * item['quantity'] for item in cart_items)

    return render_template('cart.html', cart_items=cart_items, total_price=total_price)

@app.route('/increase/<int:id>')
def increase(id):
    cursor.execute("UPDATE cart SET quantity = quantity + 1 WHERE id=%s", (id,))
    db.commit()
    return redirect('/cart')


@app.route('/decrease/<int:id>')
def decrease(id):
    cursor.execute("SELECT quantity FROM cart WHERE id=%s", (id,))
    item = cursor.fetchone()

    if item and item['quantity'] > 1:
        cursor.execute("UPDATE cart SET quantity = quantity - 1 WHERE id=%s", (id,))
    else:
        cursor.execute("DELETE FROM cart WHERE id=%s", (id,))

    db.commit()
    return redirect('/cart')


@app.route('/remove/<int:id>')
def remove(id):
    cursor.execute("DELETE FROM cart WHERE id=%s", (id,))
    db.commit()
    return redirect('/cart')


@app.route('/checkout')
def checkout():
    if 'user_id' not in session:
        return redirect('/login')

    cursor.execute("""
        SELECT name, address1, address2, city, pincode 
        FROM users 
        WHERE id=%s
    """, (session['user_id'],))

    user = cursor.fetchone()

    # 🔴 pick only ONE address
    address = user['address1'] if user['address1'] else user['address2']

    return render_template('checkout.html', 
                            user=user, 
                            address=address)
    
    
@app.route('/place-order', methods=['POST'])
def place_order():
    if 'user_id' not in session:
        return redirect('/login')

    user_id = session['user_id']

    # ✅ SAFE FORM DATA
    address = request.form.get('address')
    city = request.form.get('city')
    pincode = request.form.get('pincode')

    # ❌ If no address → stop
    if not address or not city or not pincode:
        flash("Please fill all address details")
        return redirect('/checkout')

    # ✅ GET CART ITEMS
    cursor.execute("""
        SELECT products.name, products.image, products.price, cart.quantity
        FROM cart
        JOIN products ON cart.product_id = products.id
        WHERE cart.user_id=%s
    """, (user_id,))

    items = cursor.fetchall()

    # ❌ If cart empty → stop
    if not items:
        flash("Your cart is empty!")
        return redirect('/cart')

    # ✅ CALCULATE TOTAL
    total_price = sum(item['price'] * item['quantity'] for item in items)

    # ✅ INSERT ORDER
    cursor.execute("""
        INSERT INTO orders 
        (user_id, total_price, address, city, pincode, payment_method, status)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (user_id, total_price, address, city, pincode, "COD", "Placed"))

    db.commit()
    order_id = cursor.lastrowid

    # ✅ INSERT ORDER ITEMS
    for item in items:
        cursor.execute("""
            INSERT INTO order_items 
            (order_id, product_name, image, price, quantity)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            order_id,
            item['name'],
            item['image'],
            item['price'],
            item['quantity']
        ))

    db.commit()

    # ✅ CLEAR CART
    cursor.execute("DELETE FROM cart WHERE user_id=%s", (user_id,))
    db.commit()

    # ✅ GET USER NAME (FIXED TABLE ✅)
    cursor.execute("SELECT name FROM users WHERE id=%s", (user_id,))
    user = cursor.fetchone()

    name = user['name'] if user else "User"

    return render_template(
        'success.html',
        order_id=order_id,
        name=name,
        address=address,
        city=city,
        pincode=pincode,
        total_price=total_price
    )
    
    
@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'user_id' not in session:
        return redirect('/login')

    user_id = session['user_id']

    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        address1 = request.form.get('address1')
        address2 = request.form.get('address2')
        city = request.form.get('city')
        pincode = request.form.get('pincode')

        cursor.execute("""
            UPDATE users 
            SET name=%s, email=%s, address1=%s, address2=%s, city=%s, pincode=%s
            WHERE id=%s
        """, (name, email, address1, address2, city, pincode, user_id))

        db.commit()
        return redirect('/profile')

    cursor.execute("SELECT * FROM users WHERE id=%s", (user_id,))
    user = cursor.fetchone()

    print("USER DATA:", user)

    return render_template('profile.html', user=user)

@app.route('/orders')
def orders():
    if 'user_id' not in session:
        return redirect('/login')

    role = session.get('role')

    if role == 'merchant':
        return redirect('/merchant-orders')
    else:
        return redirect('/user-orders')

@app.route('/user-orders')
def user_orders():
    if 'user_id' not in session:
        return redirect('/login')

    # 🔁 Redirect merchant
    if session.get('role') == 'merchant':
        return redirect('/merchant-orders')

    user_id = session['user_id']

    # ✅ GET USER NAME (IMPORTANT FIX)
    cursor.execute("SELECT name FROM users WHERE id=%s", (user_id,))
    user = cursor.fetchone()

    if user:
        user_name = user['name']
    else:
        user_name = "User"

    # ✅ GET ORDERS
    cursor.execute("""
        SELECT * FROM orders
        WHERE user_id=%s
        ORDER BY created_at DESC
    """, (user_id,))

    orders = cursor.fetchall()

    # ✅ ADD ITEMS + NAME IN EACH ORDER
    for order in orders:

        # 🔹 Attach user name
        order['name'] = user_name

        # 🔹 Get items for this order
        cursor.execute(
            "SELECT * FROM order_items WHERE order_id=%s",
            (order['id'],)
        )
        items = cursor.fetchall()

        # 🔹 Safe fallback
        order['items'] = items if items else []

    return render_template('user_orders.html', orders=orders)

@app.route('/merchant-orders')
def merchant_orders():
    if 'user_id' not in session or session.get('role') != 'merchant':
        return redirect('/login')

    cursor.execute("SELECT * FROM orders ORDER BY created_at DESC")
    orders = cursor.fetchall()

    return render_template('merchant_orders.html', orders=orders) 


@app.route('/update-status/<int:order_id>', methods=['POST'])
def update_status(order_id):

    if 'user_id' not in session or session.get('role') != 'merchant':
        return "Unauthorized"

    flow = ["Placed", "Confirmed", "Shipped", "Out for Delivery", "Delivered"]

    cursor.execute("SELECT status FROM orders WHERE id=%s", (order_id,))
    order = cursor.fetchone()

    if not order:
        return "Order not found"

    current = order['status'] or "Placed"

    if current not in flow:
        current = "Placed"

    index = flow.index(current)

    if index < len(flow) - 1:
        new_status = flow[index + 1]

        cursor.execute("""
            UPDATE orders
            SET status=%s
            WHERE id=%s
        """, (new_status, order_id))

        db.commit()

    return redirect('/merchant-orders')

@app.route('/delete-product/<int:product_id>')
def delete_product(product_id):

    if 'user_id' not in session or session.get('role') != 'merchant':
        return "Unauthorized"

    cursor.execute("DELETE FROM products WHERE id=%s", (product_id,))
    db.commit()

    return redirect('/')

@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return redirect('/')

# WISHLIST
@app.route('/add-to-wishlist/<int:product_id>')
def add_to_wishlist(product_id):

    if 'user_id' not in session:
        return redirect('/login')

    user_id = session['user_id']

    cursor.execute("""
        SELECT * FROM wishlist 
        WHERE user_id=%s AND product_id=%s
    """, (user_id, product_id))

    item = cursor.fetchone()

    if not item:
        cursor.execute("""
            INSERT INTO wishlist (user_id, product_id)
            VALUES (%s, %s)
        """, (user_id, product_id))
        db.commit()

    return redirect('/')


@app.route('/wishlist')
def wishlist():

    if 'user_id' not in session:
        return redirect('/login')

    cursor.execute("""
        SELECT products.*
        FROM wishlist
        JOIN products ON wishlist.product_id = products.id
        WHERE wishlist.user_id=%s
    """, (session['user_id'],))

    items = cursor.fetchall()

    return render_template('wishlist.html', items=items)

@app.route('/remove-from-wishlist/<int:product_id>')
def remove_from_wishlist(product_id):

    if 'user_id' not in session:
        return redirect('/login')

    user_id = session['user_id']

    cursor.execute("""
        DELETE FROM wishlist 
        WHERE user_id=%s AND product_id=%s
    """, (user_id, product_id))

    db.commit()

    return redirect('/wishlist')



@app.route('/all-products')
def all_products():
    min_price = request.args.get('min_price')
    max_price = request.args.get('max_price')
    product_name = request.args.get('product_name')

    # 🔹 BASE QUERY
    query = "SELECT * FROM products WHERE 1=1"
    values = []

    if product_name:
        query += " AND name=%s"
        values.append(product_name)

    if min_price:
        query += " AND price >= %s"
        values.append(min_price)

    if max_price:
        query += " AND price <= %s"
        values.append(max_price)

    cursor.execute(query, tuple(values))
    products = cursor.fetchall()

    # 🔹 GET ALL PRODUCT NAMES (for filter list)
    cursor.execute("SELECT DISTINCT name FROM products")
    names = cursor.fetchall()

    # convert to simple list
    all_names = [n['name'] for n in names]

    return render_template(
        "all_products.html",
        products=products,
        all_names=all_names
    )
if __name__ == "__main__":
    app.run(debug=True)