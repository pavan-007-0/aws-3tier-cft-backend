from flask import Blueprint, request, jsonify
import mysql.connector
from db import get_connection
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import datetime

auth = Blueprint("auth", __name__)

SECRET_KEY = "MY_SUPER_SECRET_KEY"  # Change later


# ==============================
# REGISTER USER
# ==============================
@auth.route("/register", methods=["POST"])
def register():
    data = request.json
    name = data["name"]
    email = data["email"]
    password = data["password"]

    conn = get_connection()
    cursor = conn.cursor()

    # Check existing email
    cursor.execute("SELECT id FROM users WHERE email=%s", (email,))
    if cursor.fetchone():
        return jsonify({"success": False, "message": "Email already exists"})

    hashed = generate_password_hash(password)

    cursor.execute(
        "INSERT INTO users (name, email, password) VALUES (%s, %s, %s)",
        (name, email, hashed)
    )
    conn.commit()

    return jsonify({"success": True, "message": "Registration successful"})


# ==============================
# LOGIN USER
# ==============================
@auth.route("/login", methods=["POST"])
def login():
    data = request.json
    email = data["email"]
    password = data["password"]

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
    user = cursor.fetchone()

    if not user or not check_password_hash(user["password"], password):
        return jsonify({"success": False, "message": "Invalid credentials"})

    token = jwt.encode(
        {
            "id": user["id"],
            "email": user["email"],
            "exp": datetime.datetime.utcnow() + datetime.timedelta(days=1)
        },
        SECRET_KEY,
        algorithm="HS256"
    )

    return jsonify({"success": True, "token": token})


# ==============================
# GET ALL PRODUCTS
# ==============================
@auth.route("/products", methods=["GET"])
def get_products():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT id, name, description, price, image FROM products")
    products = cursor.fetchall()

    return jsonify({"success": True, "products": products})


# ==============================
# GET SINGLE PRODUCT BY ID
# ==============================
@auth.route("/products/<int:id>", methods=["GET"])
def get_product(id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        "SELECT id, name, description, price, image FROM products WHERE id=%s",
        (id,)
    )
    product = cursor.fetchone()

    if not product:
        return jsonify({"success": False, "message": "Product not found"}), 404

    return jsonify({"success": True, "product": product})
