from flask import Blueprint, request, jsonify
from db import get_connection

cart = Blueprint("cart", __name__)

# ---------------------------
# ADD TO CART
# ---------------------------
@cart.route("/add", methods=["POST"])
def add_to_cart():
    data = request.json
    user_id = data["user_id"]
    product_id = data["product_id"]

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO cart (user_id, product_id, quantity) VALUES (%s, %s, 1)",
        (user_id, product_id)
    )
    conn.commit()

    return jsonify({"success": True, "message": "Added to cart"})


# ---------------------------
# GET USER CART
# ---------------------------
@cart.route("/", methods=["GET"])
def get_cart():
    user_id = request.args.get("user_id")

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT c.id, c.quantity, p.name, p.price, p.image
        FROM cart c
        JOIN products p ON c.product_id = p.id
        WHERE c.user_id = %s
    """, (user_id,))

    items = cursor.fetchall()

    return jsonify({"success": True, "cart": items})
