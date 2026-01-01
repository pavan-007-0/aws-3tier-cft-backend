from flask import Blueprint, request, jsonify
from db import get_connection
from security import token_required, rate_limit_api, validate_json_input
from error_handlers import APIException
import logging

cart = Blueprint("cart", __name__)
logger = logging.getLogger(__name__)

@cart.route("/add", methods=["POST"])
@token_required
@rate_limit_api
@validate_json_input(required_fields=['product_id'], optional_fields=['quantity'])
def add_to_cart():
    """Add item to user's cart"""
    try:
        data = request.validated_json
        user_id = request.current_user_id
        product_id = int(data.get('product_id'))
        quantity = int(data.get('quantity', 1))
        
        if quantity < 1 or quantity > 10:
            raise APIException("Quantity must be between 1 and 10", 400)
        
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Check if product exists and is active
        cursor.execute("""
            SELECT id, name, price, quantity as stock, is_active
            FROM products 
            WHERE id = %s AND is_active = TRUE
        """, (product_id,))
        
        product = cursor.fetchone()
        if not product:
            cursor.close()
            conn.close()
            raise APIException("Product not found or unavailable", 404)
        
        # Check stock availability
        if product['stock'] < quantity:
            cursor.close()
            conn.close()
            raise APIException(f"Only {product['stock']} items available in stock", 400)
        
        # Check if item already exists in cart
        cursor.execute("""
            SELECT id, quantity FROM cart 
            WHERE user_id = %s AND product_id = %s
        """, (user_id, product_id))
        
        existing_item = cursor.fetchone()
        
        if existing_item:
            # Update existing cart item
            new_quantity = existing_item['quantity'] + quantity
            if new_quantity > 10:
                cursor.close()
                conn.close()
                raise APIException("Maximum 10 items per product allowed", 400)
            
            if new_quantity > product['stock']:
                cursor.close()
                conn.close()
                raise APIException(f"Only {product['stock']} items available in stock", 400)
            
            cursor.execute("""
                UPDATE cart SET quantity = %s, updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (new_quantity, existing_item['id']))
            
            message = f"Updated {product['name']} quantity to {new_quantity}"
        else:
            # Add new cart item
            cursor.execute("""
                INSERT INTO cart (user_id, product_id, quantity)
                VALUES (%s, %s, %s)
            """, (user_id, product_id, quantity))
            
            message = f"Added {product['name']} to cart"
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({
            "success": True,
            "message": message
        }), 201
        
    except APIException:
        raise
    except Exception as e:
        logger.error(f"Error adding to cart: {str(e)}")
        raise APIException("Failed to add item to cart", 500)

@cart.route("/", methods=["GET"])
@token_required
@rate_limit_api
def get_cart():
    """Get user's cart items"""
    try:
        user_id = request.current_user_id
        
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT c.id as cart_id, c.quantity, c.created_at, c.updated_at,
                   p.id as product_id, p.name, p.price, p.compare_price, 
                   p.image, p.brand, p.quantity as stock,
                   (c.quantity * p.price) as subtotal
            FROM cart c
            JOIN products p ON c.product_id = p.id
            WHERE c.user_id = %s AND p.is_active = TRUE
            ORDER BY c.updated_at DESC
        """, (user_id,))
        
        items = cursor.fetchall()
        
        # Calculate totals
        total_items = sum(item['quantity'] for item in items)
        subtotal = sum(item['subtotal'] for item in items)
        
        # Calculate savings if compare_price exists
        total_savings = sum(
            (item['compare_price'] - item['price']) * item['quantity']
            for item in items 
            if item['compare_price'] and item['compare_price'] > item['price']
        )
        
        cursor.close()
        conn.close()
        
        return jsonify({
            "success": True,
            "cart": {
                "items": items,
                "summary": {
                    "total_items": total_items,
                    "subtotal": round(subtotal, 2),
                    "total_savings": round(total_savings, 2),
                    "estimated_total": round(subtotal, 2)  # Before tax/shipping
                }
            }
        })
        
    except Exception as e:
        logger.error(f"Error fetching cart: {str(e)}")
        raise APIException("Failed to fetch cart", 500)

@cart.route("/update/<int:cart_id>", methods=["PUT"])
@token_required
@rate_limit_api
@validate_json_input(required_fields=['quantity'])
def update_cart_item(cart_id):
    """Update cart item quantity"""
    try:
        data = request.validated_json
        user_id = request.current_user_id
        quantity = int(data.get('quantity'))
        
        if quantity < 1 or quantity > 10:
            raise APIException("Quantity must be between 1 and 10", 400)
        
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Check if cart item belongs to user and get product info
        cursor.execute("""
            SELECT c.id, c.product_id, p.name, p.quantity as stock
            FROM cart c
            JOIN products p ON c.product_id = p.id
            WHERE c.id = %s AND c.user_id = %s AND p.is_active = TRUE
        """, (cart_id, user_id))
        
        cart_item = cursor.fetchone()
        if not cart_item:
            cursor.close()
            conn.close()
            raise APIException("Cart item not found", 404)
        
        # Check stock availability
        if cart_item['stock'] < quantity:
            cursor.close()
            conn.close()
            raise APIException(f"Only {cart_item['stock']} items available in stock", 400)
        
        # Update quantity
        cursor.execute("""
            UPDATE cart SET quantity = %s, updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """, (quantity, cart_id))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({
            "success": True,
            "message": f"Updated {cart_item['name']} quantity to {quantity}"
        })
        
    except APIException:
        raise
    except Exception as e:
        logger.error(f"Error updating cart item: {str(e)}")
        raise APIException("Failed to update cart item", 500)

@cart.route("/remove/<int:cart_id>", methods=["DELETE"])
@token_required
@rate_limit_api
def remove_cart_item(cart_id):
    """Remove item from cart"""
    try:
        user_id = request.current_user_id
        
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Check if cart item belongs to user
        cursor.execute("""
            SELECT c.id, p.name
            FROM cart c
            JOIN products p ON c.product_id = p.id
            WHERE c.id = %s AND c.user_id = %s
        """, (cart_id, user_id))
        
        cart_item = cursor.fetchone()
        if not cart_item:
            cursor.close()
            conn.close()
            raise APIException("Cart item not found", 404)
        
        # Remove item
        cursor.execute("DELETE FROM cart WHERE id = %s", (cart_id,))
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({
            "success": True,
            "message": f"Removed {cart_item['name']} from cart"
        })
        
    except APIException:
        raise
    except Exception as e:
        logger.error(f"Error removing cart item: {str(e)}")
        raise APIException("Failed to remove cart item", 500)

@cart.route("/clear", methods=["DELETE"])
@token_required
@rate_limit_api
def clear_cart():
    """Clear all items from user's cart"""
    try:
        user_id = request.current_user_id
        
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM cart WHERE user_id = %s", (user_id,))
        affected_rows = cursor.rowcount
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({
            "success": True,
            "message": f"Cleared {affected_rows} items from cart"
        })
        
    except Exception as e:
        logger.error(f"Error clearing cart: {str(e)}")
        raise APIException("Failed to clear cart", 500)
