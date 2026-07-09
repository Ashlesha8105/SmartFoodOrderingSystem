import sqlite3

conn = sqlite3.connect("foodorder.db")

cursor = conn.cursor()

# ---------------- Admin ----------------

cursor.execute("""
CREATE TABLE IF NOT EXISTS admin(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    password TEXT NOT NULL
)
""")

# ---------------- Customers ----------------

cursor.execute("""
CREATE TABLE IF NOT EXISTS customers(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE,
    phone TEXT,
    address TEXT,
    password TEXT
)
""")

# ---------------- Food ----------------

cursor.execute("""
CREATE TABLE IF NOT EXISTS food(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    food_name TEXT,
    category TEXT,
    price INTEGER,
    image TEXT
)
""")

# ---------------- Orders ----------------

cursor.execute("""
CREATE TABLE IF NOT EXISTS orders(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER,
    customer_name TEXT,
    phone TEXT,
    address TEXT,
    food_name TEXT,
    quantity INTEGER,
    total INTEGER,
    status TEXT DEFAULT 'Pending',
    order_date TEXT
)
""")

# ---------------- Default Admin ----------------

cursor.execute("""
INSERT INTO admin(username,password)
SELECT 'admin','admin123'
WHERE NOT EXISTS(
SELECT * FROM admin WHERE username='admin'
)
""") 

conn.commit()

conn.close()

print("Database Created Successfully")