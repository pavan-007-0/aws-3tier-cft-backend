from flask import Blueprint, jsonify, request
from db import get_connection
from security import rate_limit_api, validate_json_input
from error_handlers import APIException
import logging

products = Blueprint("products", __name__)
logger = logging.getLogger(__name__)

# ---------------- GET ALL PRODUCTS ----------------
@products.route("/", methods=["GET"])
@rate_limit_api
def get_all_products():
    try:
        # Query params
        page = int(request.args.get("page", 1))
        limit = int(request.args.get("limit", 20))
        category = request.args.get("category")
        search = request.args.get("search")
        sort_by = request.args.get("sort_by", "name")
        sort_order = request.args.get("sort_order", "ASC").upper()

        if page < 1 or limit < 1 or limit > 100:
            raise APIException("Invalid pagination parameters", 400)

        # Allowed sorting fields
        if sort_by not in ["name", "price", "created_at", "avg_rating"]:
            sort_by = "name"

        if sort_order not in ["ASC", "DESC"]:
            sort_order = "ASC"

        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        query = """
            SELECT
                p.id,
                p.name,
                p.description,
                p.price,
                p.compare_price,
                p.image,
                p.brand,
                p.quantity,
                p.is_active,
                p.created_at,
                c.name AS category_name,
                COALESCE(AVG(r.rating), 0) AS avg_rating,
                COUNT(r.id) AS review_count
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.id
            LEFT JOIN reviews r ON p.id = r.product_id
            WHERE p.is_active = TRUE
        """

        params = []

        if category:
            query += " AND c.name = %s"
            params.append(category)

        if search:
            query += " AND (p.name LIKE %s OR p.description LIKE %s OR p.brand LIKE %s)"
            search_term = f"%{search}%"
            params.extend([search_term, search_term, search_term])

        query += " GROUP BY p.id"
        query += f" ORDER BY {sort_by} {sort_order}"
        query += " LIMIT %s OFFSET %s"

        offset = (page - 1) * limit
        params.extend([limit, offset])

        cursor.execute(query, params)
        data = cursor.fetchall()

        # Count query
        count_query = """
            SELECT COUNT(DISTINCT p.id) AS total
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.id
            WHERE p.is_active = TRUE
        """
        count_params = []

        if category:
            count_query += " AND c.name = %s"
            count_params.append(category)

        if search:
            count_query += " AND (p.name LIKE %s OR p.description LIKE %s OR p.brand LIKE %s)"
            count_params.extend([search_term, search_term, search_term])

        cursor.execute(count_query, count_params)
        total = cursor.fetchone()["total"]

        cursor.close()
        conn.close()

        return jsonify({
            "success": True,
            "products": data,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "total_pages": (total + limit - 1) // limit
            }
        })

    except APIException:
        raise
    except Exception as e:
        logger.error(f"Error fetching products: {e}")
        raise APIException("Failed to fetch products", 500)

# ---------------- SINGLE PRODUCT ----------------
@products.route("/<int:product_id>", methods=["GET"])
@rate_limit_api
def get_product(product_id):
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT
                p.*,
                c.name AS category_name,
                COALESCE(AVG(r.rating), 0) AS avg_rating,
                COUNT(r.id) AS review_count
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.id
            LEFT JOIN reviews r ON p.id = r.product_id
            WHERE p.id = %s AND p.is_active = TRUE
            GROUP BY p.id
        """, (product_id,))

        product = cursor.fetchone()
        if not product:
            raise APIException("Product not found", 404)

        cursor.execute("""
            SELECT image_url, alt_text, is_primary
            FROM product_images
            WHERE product_id = %s
            ORDER BY is_primary DESC
        """, (product_id,))

        product["images"] = cursor.fetchall()

        cursor.close()
        conn.close()

        return jsonify({
            "success": True,
            "product": product
        })

    except APIException:
        raise
    except Exception as e:
        logger.error(f"Error fetching product {product_id}: {e}")
        raise APIException("Failed to fetch product", 500)

# ---------------- CATEGORIES ----------------
@products.route("/categories", methods=["GET"])
@rate_limit_api
def get_categories():
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT c.id, c.name, COUNT(p.id) AS product_count
            FROM categories c
            LEFT JOIN products p ON c.id = p.category_id AND p.is_active = TRUE
            WHERE c.is_active = TRUE
            GROUP BY c.id
            ORDER BY c.name
        """)

        categories = cursor.fetchall()
        cursor.close()
        conn.close()

        return jsonify({
            "success": True,
            "categories": categories
        })

    except Exception as e:
        logger.error(f"Error fetching categories: {e}")
        raise APIException("Failed to fetch categories", 500)
