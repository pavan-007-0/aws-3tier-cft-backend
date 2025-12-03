from flask import Blueprint, jsonify
from db import get_connection

products = Blueprint("products", __name__)

@products.route("/", methods=["GET"])
def get_all_products():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id, name, description, price, image FROM products")
    data = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify({"success": True, "products": data})

@products.route("/<int:id>", methods=["GET"])
def get_single_product(id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT id, name, description, price, image FROM products WHERE id=%s",
        (id,)
    )
    data = cursor.fetchone()
    cursor.close()
    conn.close()

    if not data:
        return jsonify({"success": False, "message": "Product not found"}), 404

    return jsonify({"success": True, "product": data})
