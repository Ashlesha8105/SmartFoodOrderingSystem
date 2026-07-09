from flask import Flask, render_template, request, redirect, session
import sqlite3

app = Flask(__name__)
app.secret_key = "foodorder123"

# ---------------- Home ----------------

@app.route("/")
def home():
    return render_template("home.html")


# ---------------- CUSTOMER LOGIN ----------------

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form.get("email")
        password = request.form.get("password")

        conn = sqlite3.connect("foodorder.db")
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM customers WHERE email=? AND password=?",
            (email, password)
        )

        user = cursor.fetchone()
        conn.close()

        if user:
            session["customer_id"] = user[0]
            session["customer_name"] = user[1]
            return redirect("/menu")
        else:
            return "❌ Invalid Email or Password"

    
    return render_template("login.html")


# ---------------- REGISTER ----------------

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        phone = request.form["phone"]
        address = request.form["address"]
        password = request.form["password"]

        conn = sqlite3.connect("foodorder.db")
        cursor = conn.cursor()

        cursor.execute("""
        INSERT INTO customers(name,email,phone,address,password)
        VALUES(?,?,?,?,?)
        """, (name, email, phone, address, password))

        conn.commit()
        conn.close()

        return redirect("/login")

    return render_template("register.html")


# ---------------- MENU ----------------

@app.route("/menu")
def menu():

    search = request.args.get("search", "")

    conn = sqlite3.connect("foodorder.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    if search:
        cursor.execute("""
            SELECT * FROM food
            WHERE food_name LIKE ?
        """, ('%' + search + '%',))
    else:
        cursor.execute("SELECT * FROM food")

    foods = cursor.fetchall()
    conn.close()

    return render_template("menu.html", foods=foods)


# ---------------- CART ----------------

@app.route("/cart")
def cart():

    cart_items = session.get("cart", [])

    total = 0

    for item in cart_items:
        total += item["price"] * item["quantity"]

    return render_template(
        "cart.html",
        cart=cart_items,
        total=total
    )
# ---------------- ADD TO CART ----------------

@app.route("/add_to_cart", methods=["POST"])
def add_to_cart():

    food_name = request.form.get("food_name")
    price = int(request.form.get("price"))

    cart = session.get("cart", [])

    found = False

    for item in cart:

        if "quantity" not in item:
            item["quantity"] = 1

        if item["food_name"] == food_name:
            item["quantity"] += 1
            found = True
            break

    if not found:
        cart.append({
            "food_name": food_name,
            "price": price,
            "quantity": 1
        })

    session["cart"] = cart

    return redirect("/cart")

@app.route("/clear-cart")
def clear_cart():
    session.pop("cart", None)
    return redirect("/menu")

@app.route("/increase/<int:index>")
def increase(index):

    cart = session.get("cart", [])

    if index < len(cart):
        cart[index]["quantity"] += 1

    session["cart"] = cart

    return redirect("/cart")

@app.route("/decrease/<int:index>")
def decrease(index):

    cart = session.get("cart", [])

    if index < len(cart):

        if cart[index]["quantity"] > 1:
            cart[index]["quantity"] -= 1

    session["cart"] = cart

    return redirect("/cart")

@app.route("/remove/<int:index>")
def remove(index):

    cart = session.get("cart", [])

    if index < len(cart):
        cart.pop(index)

    session["cart"] = cart

    return redirect("/cart")

# ---------------- CHECKOUT ----------------

@app.route("/checkout")
def checkout():

    cart = session.get("cart", [])

    total = 0

    for item in cart:
        total += item["price"] * item["quantity"]

    return render_template(
        "checkout.html",
        total=total
    )


# ---------------- PLACE ORDER (NEW ADDED CODE) ----------------

@app.route("/place_order", methods=["POST"])
def place_order():

    name = request.form.get("name")
    phone = request.form.get("phone")
    address = request.form.get("address")

    cart = session.get("cart", [])
    customer_id = session["customer_id"]

    if len(cart) == 0:
        return "Cart is Empty"

    conn = sqlite3.connect("foodorder.db")
    cursor = conn.cursor()

    from datetime import datetime

    date = datetime.now().strftime("%d-%m-%Y")

    for item in cart:

        total = item["price"] * item["quantity"]

        cursor.execute("""
       INSERT INTO orders
(customer_id, customer_name, phone, address, food_name, quantity, total, status, order_date)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
    customer_id,
    name,
    phone,
    address,
    item["food_name"],
    item["quantity"],
    total,
    "Pending",
    date
))

    conn.commit()
    conn.close()

    session["cart"] = []

    return redirect("/orders")


# ---------------- ORDERS ----------------

@app.route("/orders")
def orders():

    if "customer_name" not in session:
        return redirect("/login")

    customer_id = session["customer_id"]

    conn = sqlite3.connect("foodorder.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
    SELECT * FROM orders
    WHERE customer_id = ?
    ORDER BY id DESC
""", (customer_id,))

    orders = cursor.fetchall()

    conn.close()

    return render_template("orders.html", orders=orders)

# ---------------- ADMIN LOGIN ----------------

@app.route("/admin", methods=["GET", "POST"])
def admin():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        conn = sqlite3.connect("foodorder.db")
        cursor = conn.cursor()

        cursor.execute("""
        SELECT * FROM admin WHERE username=? AND password=?
        """, (username, password))

        admin = cursor.fetchone()
        conn.close()

        if admin:
            return redirect("/dashboard")
        else:
            return "❌ Invalid Admin Login"

    return render_template("admin_login.html")


# ---------------- ADMIN PAGES ----------------

@app.route("/dashboard")
def dashboard():

    conn = sqlite3.connect("foodorder.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Foods
    cursor.execute("SELECT COUNT(*) FROM food")
    total_foods = cursor.fetchone()[0]

    # Customers
    cursor.execute("SELECT COUNT(*) FROM customers")
    total_customers = cursor.fetchone()[0]

    # Orders
    cursor.execute("SELECT COUNT(*) FROM orders")
    total_orders = cursor.fetchone()[0]

    # Revenue
    cursor.execute("SELECT SUM(total) FROM orders")
    revenue = cursor.fetchone()[0]

    if revenue is None:
        revenue = 0

    # Pending
    cursor.execute("SELECT COUNT(*) FROM orders WHERE status='Pending'")
    pending = cursor.fetchone()[0]

    # Approved
    cursor.execute("SELECT COUNT(*) FROM orders WHERE status='Approved'")
    approved = cursor.fetchone()[0]

    # Delivered
    cursor.execute("SELECT COUNT(*) FROM orders WHERE status='Delivered'")
    delivered = cursor.fetchone()[0]

    # Cancelled
    cursor.execute("SELECT COUNT(*) FROM orders WHERE status='Cancelled'")
    cancelled = cursor.fetchone()[0]

    conn.close()

    return render_template(
        "dashboard.html",
        total_foods=total_foods,
        total_customers=total_customers,
        total_orders=total_orders,
        revenue=revenue,
        pending=pending,
        approved=approved,
        delivered=delivered,
        cancelled=cancelled
    )


@app.route("/add-food", methods=["GET", "POST"])
def add_food():

    if request.method == "POST":

        food_name = request.form.get("food_name")
        category = request.form.get("category")
        price = request.form.get("price")
        image = request.form.get("image")

        conn = sqlite3.connect("foodorder.db")
        cursor = conn.cursor()

        cursor.execute("""
        INSERT INTO food
        (food_name, category, price, image)
        VALUES (?, ?, ?, ?)
        """, (
            food_name,
            category,
            price,
            image
        ))

        conn.commit()
        conn.close()

        return redirect("/food-list")

    return render_template("add_food.html")


@app.route("/food-list")
def food_list():

    conn = sqlite3.connect("foodorder.db")
    conn.row_factory = sqlite3.Row

    cursor = conn.cursor()

    cursor.execute("""
    SELECT *
    FROM food
    ORDER BY id DESC
    """)

    foods = cursor.fetchall()

    conn.close()

    return render_template(
        "food_list.html",
        foods=foods
    )


@app.route("/customers")
def customers():

    conn = sqlite3.connect("foodorder.db")
    conn.row_factory = sqlite3.Row

    cursor = conn.cursor()

    cursor.execute("SELECT * FROM customers")

    customers = cursor.fetchall()

    conn.close()

    return render_template(
        "customers.html",
        customers=customers
    )


@app.route("/admin-orders")
def admin_orders():

    conn = sqlite3.connect("foodorder.db")
    conn.row_factory = sqlite3.Row

    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM orders
        ORDER BY id DESC
    """)

    orders = cursor.fetchall()

    conn.close()

    return render_template("admin_orders.html", orders=orders)

@app.route("/delete-food/<int:id>")
def delete_food(id):

    conn = sqlite3.connect("foodorder.db")
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM food WHERE id=?",
        (id,)
    )

    conn.commit()
    conn.close()

    return redirect("/food-list")


@app.route("/edit-food/<int:id>", methods=["GET", "POST"])
def edit_food(id):

    conn = sqlite3.connect("foodorder.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    if request.method == "POST":

        food_name = request.form.get("food_name")
        category = request.form.get("category")
        price = request.form.get("price")
        image = request.form.get("image")

        cursor.execute("""
        UPDATE food
        SET food_name=?,
            category=?,
            price=?,
            image=?
        WHERE id=?
        """, (
            food_name,
            category,
            price,
            image,
            id
        ))

        conn.commit()
        conn.close()

        return redirect("/food-list")

    cursor.execute(
        "SELECT * FROM food WHERE id=?",
        (id,)
    )

    food = cursor.fetchone()

    conn.close()

    return render_template(
        "edit_food.html",
        food=food
    )

# ---------------- APPROVE ORDER ----------------

@app.route("/approve-order/<int:id>")
def approve_order(id):

    conn = sqlite3.connect("foodorder.db")
    cursor = conn.cursor()

    cursor.execute("""
    UPDATE orders
    SET status='Approved'
    WHERE id=?
    """, (id,))

    conn.commit()
    conn.close()

    return redirect("/admin-orders")


# ---------------- CANCEL ORDER ----------------

@app.route("/cancel-order/<int:id>")
def cancel_order(id):

    conn = sqlite3.connect("foodorder.db")
    cursor = conn.cursor()

    cursor.execute("""
    UPDATE orders
    SET status='Cancelled'
    WHERE id=?
    """, (id,))

    conn.commit()
    conn.close()

    return redirect("/admin-orders")

# ---------------- RUN ----------------

if __name__ == "__main__":
    app.run(debug=True)