from flask import Blueprint, request, jsonify
from db import get_connection
from security import token_required, admin_required, rate_limit_api, validate_json_input
from error_handlers import APIException
import uuid
from datetime import datetime
import logging

orders = Blueprint("orders", __name__)
logger = logging.getLogger(__name__)

@orders.route("/", methods=["POST"])
@token_required
@rate_limit_api
@validate_json_input(
    required_fields=['shipping_address'],
    optional_fields=['payment_method', 'notes']
)
def create_order():
    """Create a new order from cart items"""
    try:
        data = request.validated_json
        user_id = request.current_user_id
        shipping_address = data.get("shipping_address")
        payment_method = data.get("payment_method", "card")
        notes = data.get("notes", "")
        
        # Validate shipping address
        required_address_fields = ['street', 'city', 'state', 'zip_code', 'country']
        for field in required_address_fields:
            if field not in shipping_address:
                raise APIException(f"Missing required address field: {field}", 400)
        
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Get cart items with stock validation
        cursor.execute("""
            SELECT c.product_id, c.quantity, p.name, p.price, p.sku, p.quantity as stock
            FROM cart c
            JOIN products p ON c.product_id = p.id
            WHERE c.user_id = %s AND p.is_active = TRUE
        """, (user_id,))
        
        cart_items = cursor.fetchall()
        if not cart_items:
            cursor.close()
            conn.close()
            raise APIException("Cart is empty", 400)
        
        # Validate stock availability
        for item in cart_items:
            if item['stock'] < item['quantity']:
                cursor.close()
                conn.close()
                raise APIException(f"Insufficient stock for {item['name']}. Only {item['stock']} available.", 400)
        
        # Calculate totals
        subtotal = sum(float(item['price']) * item['quantity'] for item in cart_items)
        tax_rate = 0.08  # 8% tax
        tax_amount = subtotal * tax_rate
        shipping_amount = 10.00 if subtotal < 100 else 0  # Free shipping over $100
        total_amount = subtotal + tax_amount + shipping_amount
        
        # Generate order number
        order_number = f"ORD-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
        
        # Create order
        cursor.execute("""
            INSERT INTO orders (user_id, order_number, subtotal, tax_amount, shipping_amount, 
                              total_amount, payment_method, status, notes)
            VALUES (%s, %s, %s, %s, %s, %s, %s, 'pending', %s)
        """, (user_id, order_number, subtotal, tax_amount, shipping_amount, 
              total_amount, payment_method, notes))
        
        order_id = cursor.lastrowid
        
        # Create shipping address record
        cursor.execute("""
            INSERT INTO shipping_addresses (order_id, street, city, state, zip_code, country, 
                                          full_name, phone, user_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (order_id, shipping_address['street'], shipping_address['city'],
              shipping_address['state'], shipping_address['zip_code'], 
              shipping_address['country'], shipping_address.get('full_name', ''),
              shipping_address.get('phone', ''), user_id))
        
        # Create order items and update product stock
        for item in cart_items:
            cursor.execute("""
                INSERT INTO order_items (order_id, product_id, product_name, product_sku, 
                                       quantity, unit_price, total_price)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (order_id, item['product_id'], item['name'], item['sku'], 
                  item['quantity'], float(item['price']), float(item['price']) * item['quantity']))
            
            # Update product stock
            cursor.execute("""
                UPDATE products SET quantity = quantity - %s
                WHERE id = %s
            """, (item['quantity'], item['product_id']))
        
        # Clear user's cart
        cursor.execute("DELETE FROM cart WHERE user_id = %s", (user_id,))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({
            "success": True,
            "message": "Order created successfully",
            "order": {
                "id": order_id,
                "order_number": order_number,
                "total_amount": round(total_amount, 2),
                "status": "pending"
            }
        }), 201
        
    except APIException:
        raise
    except Exception as e:
        logger.error(f"Error creating order: {str(e)}")
        raise APIException("Failed to create order", 500)

@orders.route("/", methods=["GET"])
@token_required
@rate_limit_api
def get_user_orders():
    """Get user's order history"""
    try:
        user_id = request.current_user_id
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 10))
        status = request.args.get('status')
        
        if page < 1 or limit < 1 or limit > 50:
            raise APIException("Invalid pagination parameters", 400)
        
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Build query
        base_query = """
            SELECT o.id, o.order_number, o.subtotal, o.tax_amount, o.shipping_amount,
                   o.total_amount, o.payment_method, o.status, o.created_at, o.updated_at,
                   COUNT(oi.id) as item_count
            FROM orders o
            LEFT JOIN order_items oi ON o.id = oi.order_id
            WHERE o.user_id = %s
        """
        
        params = [user_id]
        
        if status:
            base_query += " AND o.status = %s"
            params.append(status)
        
        base_query += " GROUP BY o.id ORDER BY o.created_at DESC"
        
        # Add pagination
        offset = (page - 1) * limit
        base_query += " LIMIT %s OFFSET %s"
        params.extend([limit, offset])
        
        cursor.execute(base_query, params)
        orders_data = cursor.fetchall()
        
        # Get total count
        count_query = "SELECT COUNT(*) as total FROM orders WHERE user_id = %s"
        count_params = [user_id]
        
        if status:
            count_query += " AND status = %s"
            count_params.append(status)
        
        cursor.execute(count_query, count_params)
        total_count = cursor.fetchone()['total']
        
        cursor.close()
        conn.close()
        
        # Calculate pagination info
        total_pages = (total_count + limit - 1) // limit
        
        return jsonify({
            "success": True,
            "orders": orders_data,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total_count,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_prev": page > 1
            }
        })
        
    except APIException:
        raise
    except Exception as e:
        logger.error(f"Error fetching orders: {str(e)}")
        raise APIException("Failed to fetch orders", 500)

@orders.route("/<int:order_id>", methods=["GET"])
@token_required
@rate_limit_api
def get_order_details(order_id):
    """Get detailed order information"""
    try:
        user_id = request.current_user_id
        
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Get order details
        cursor.execute("""
            SELECT o.*, sa.street, sa.city, sa.state, sa.zip_code, sa.country,
                   sa.full_name as shipping_name, sa.phone as shipping_phone
            FROM orders o
            LEFT JOIN shipping_addresses sa ON o.id = sa.order_id
            WHERE o.id = %s AND o.user_id = %s
        """, (order_id, user_id))
        
        order = cursor.fetchone()
        if not order:
            cursor.close()
            conn.close()
            raise APIException("Order not found", 404)
        
        # Get order items
        cursor.execute("""
            SELECT oi.*, p.name, p.image, p.brand
            FROM order_items oi
            JOIN products p ON oi.product_id = p.id
            WHERE oi.order_id = %s
        """, (order_id,))
        
        items = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        # Prepare response
        order_data = dict(order)
        order_data['items'] = items
        order_data['shipping_address'] = {
            'street': order.get('street'),
            'city': order.get('city'),
            'state': order.get('state'),
            'zip_code': order.get('zip_code'),
            'country': order.get('country'),
            'full_name': order.get('shipping_name'),
            'phone': order.get('shipping_phone')
        }
        
        return jsonify({
            "success": True,
            "order": order_data
        })
        
    except APIException:
        raise
    except Exception as e:
        logger.error(f"Error fetching order details: {str(e)}")
        raise APIException("Failed to fetch order details", 500)

@orders.route("/<int:order_id>/cancel", methods=["POST"])
@token_required
@rate_limit_api
def cancel_order(order_id):
    """Cancel an order (only if pending)"""
    try:
        user_id = request.current_user_id
        
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Check if order exists and belongs to user
        cursor.execute("""
            SELECT id, status, order_number
            FROM orders
            WHERE id = %s AND user_id = %s
        """, (order_id, user_id))
        
        order = cursor.fetchone()
        if not order:
            cursor.close()
            conn.close()
            raise APIException("Order not found", 404)
        
        if order['status'] != 'pending':
            cursor.close()
            conn.close()
            raise APIException("Only pending orders can be cancelled", 400)
        
        # Get order items to restore stock
        cursor.execute("""
            SELECT product_id, quantity
            FROM order_items
            WHERE order_id = %s
        """, (order_id,))
        
        order_items = cursor.fetchall()
        
        # Restore product stock
        for item in order_items:
            cursor.execute("""
                UPDATE products SET quantity = quantity + %s
                WHERE id = %s
            """, (item['quantity'], item['product_id']))
        
        # Update order status
        cursor.execute("""
            UPDATE orders SET status = 'cancelled', updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """, (order_id,))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({
            "success": True,
            "message": f"Order {order['order_number']} has been cancelled"
        })
        
    except APIException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling order: {str(e)}")
        raise APIException("Failed to cancel order", 500)

# Admin endpoints
@orders.route("/admin/all", methods=["GET"])
@admin_required
@rate_limit_api
def get_all_orders():
    """Get all orders (admin only)"""
    try:
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 20))
        status = request.args.get('status')
        
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Build query
        base_query = """
            SELECT o.id, o.order_number, o.total_amount, o.status, o.created_at,
                   u.name as customer_name, u.email as customer_email,
                   COUNT(oi.id) as item_count
            FROM orders o
            JOIN users u ON o.user_id = u.id
            LEFT JOIN order_items oi ON o.id = oi.order_id
        """
        
        params = []
        
        if status:
            base_query += " WHERE o.status = %s"
            params.append(status)
        
        base_query += " GROUP BY o.id ORDER BY o.created_at DESC"
        
        # Add pagination
        offset = (page - 1) * limit
        base_query += " LIMIT %s OFFSET %s"
        params.extend([limit, offset])
        
        cursor.execute(base_query, params)
        orders_data = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return jsonify({
            "success": True,
            "orders": orders_data
        })
        
    except Exception as e:
        logger.error(f"Error fetching all orders: {str(e)}")
        raise APIException("Failed to fetch orders", 500)

@orders.route("/admin/<int:order_id>/status", methods=["PUT"])
@admin_required
@rate_limit_api
@validate_json_input(required_fields=['status'])
def update_order_status(order_id):
    """Update order status (admin only)"""
    try:
        data = request.validated_json
        new_status = data.get('status')
        
        valid_statuses = ['pending', 'confirmed', 'processing', 'shipped', 'delivered', 'cancelled']
        if new_status not in valid_statuses:
            raise APIException(f"Invalid status. Must be one of: {', '.join(valid_statuses)}", 400)
        
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Check if order exists
        cursor.execute("SELECT id, status, order_number FROM orders WHERE id = %s", (order_id,))
        order = cursor.fetchone()
        
        if not order:
            cursor.close()
            conn.close()
            raise APIException("Order not found", 404)
        
        # Update status
        cursor.execute("""
            UPDATE orders SET status = %s, updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """, (new_status, order_id))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({
            "success": True,
            "message": f"Order {order['order_number']} status updated to {new_status}"
        })
        
    except APIException:
        raise
    except Exception as e:
        logger.error(f"Error updating order status: {str(e)}")
        raise APIException("Failed to update order status", 500)
