from flask import Blueprint, jsonify, request
from db import get_connection
from security import rate_limit_api, validate_json_input
from error_handlers import APIException
import logging

products = Blueprint("products", __name__)
logger = logging.getLogger(__name__)

@products.route("/", methods=["GET"])
@rate_limit_api
def get_all_products():
    """Get all products with filtering, sorting, and pagination"""
    try:
        # Get query parameters
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 20))
        category = request.args.get('category')
        search = request.args.get('search')
        sort_by = request.args.get('sort_by', 'name')
        sort_order = request.args.get('sort_order', 'ASC')
        min_price = request.args.get('min_price')
        max_price = request.args.get('max_price')
        
        # Validate parameters
        if page < 1 or limit < 1 or limit > 100:
            raise APIException("Invalid pagination parameters", 400)
        
        if sort_by not in ['name', 'price', 'created_at', 'rating']:
            sort_by = 'name'
        
        if sort_order.upper() not in ['ASC', 'DESC']:
            sort_order = 'ASC'
        
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Build query with filters
        base_query = """
            SELECT p.id, p.name, p.description, p.price, p.compare_price, 
                   p.image, p.brand, p.sku, p.quantity, p.is_active,
                   c.name as category_name, p.created_at,
                   COALESCE(AVG(r.rating), 0) as avg_rating,
                   COUNT(r.id) as review_count
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.id
            LEFT JOIN reviews r ON p.id = r.product_id
            WHERE p.is_active = TRUE
        """
        
        params = []
        
        # Add filters
        if category:
            base_query += " AND c.name = %s"
            params.append(category)
        
        if search:
            base_query += " AND (p.name LIKE %s OR p.description LIKE %s OR p.brand LIKE %s)"
            search_term = f"%{search}%"
            params.extend([search_term, search_term, search_term])
        
        if min_price:
            base_query += " AND p.price >= %s"
            params.append(float(min_price))
        
        if max_price:
            base_query += " AND p.price <= %s"
            params.append(float(max_price))
        
        # Group by for aggregation
        base_query += " GROUP BY p.id"
        
        # Add sorting
        base_query += f" ORDER BY {sort_by} {sort_order}"
        
        # Add pagination
        offset = (page - 1) * limit
        base_query += " LIMIT %s OFFSET %s"
        params.extend([limit, offset])
        
        cursor.execute(base_query, params)
        products_data = cursor.fetchall()
        
        # Get total count for pagination
        count_query = """
            SELECT COUNT(DISTINCT p.id) as total
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
        
        if min_price:
            count_query += " AND p.price >= %s"
            count_params.append(float(min_price))
        
        if max_price:
            count_query += " AND p.price <= %s"
            count_params.append(float(max_price))
        
        cursor.execute(count_query, count_params)
        total_count = cursor.fetchone()['total']
        
        cursor.close()
        conn.close()
        
        # Calculate pagination info
        total_pages = (total_count + limit - 1) // limit
        has_next = page < total_pages
        has_prev = page > 1
        
        return jsonify({
            "success": True,
            "products": products_data,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total_count,
                "total_pages": total_pages,
                "has_next": has_next,
                "has_prev": has_prev
            },
            "filters": {
                "category": category,
                "search": search,
                "min_price": min_price,
                "max_price": max_price,
                "sort_by": sort_by,
                "sort_order": sort_order
            }
        })
        
    except APIException:
        raise
    except Exception as e:
        logger.error(f"Error fetching products: {str(e)}")
        raise APIException("Failed to fetch products", 500)

@products.route("/<int:product_id>", methods=["GET"])
@rate_limit_api
def get_single_product(product_id):
    """Get single product with detailed information"""
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Get product details with category and reviews
        cursor.execute("""
            SELECT p.*, c.name as category_name,
                   COALESCE(AVG(r.rating), 0) as avg_rating,
                   COUNT(r.id) as review_count
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.id
            LEFT JOIN reviews r ON p.id = r.product_id
            WHERE p.id = %s AND p.is_active = TRUE
            GROUP BY p.id
        """, (product_id,))
        
        product = cursor.fetchone()
        
        if not product:
            cursor.close()
            conn.close()
            raise APIException("Product not found", 404)
        
        # Get product images
        cursor.execute("""
            SELECT image_url, alt_text, is_primary
            FROM product_images
            WHERE product_id = %s
            ORDER BY is_primary DESC, id ASC
        """, (product_id,))
        
        images = cursor.fetchall()
        
        # Get recent reviews
        cursor.execute("""
            SELECT r.*, u.name as user_name
            FROM reviews r
            JOIN users u ON r.user_id = u.id
            WHERE r.product_id = %s
            ORDER BY r.created_at DESC
            LIMIT 5
        """, (product_id,))
        
        reviews = cursor.fetchall()
        
        # Get related products (same category)
        cursor.execute("""
            SELECT id, name, price, image, avg_rating
            FROM (
                SELECT p.id, p.name, p.price, p.image,
                       COALESCE(AVG(r.rating), 0) as avg_rating
                FROM products p
                LEFT JOIN reviews r ON p.id = r.product_id
                WHERE p.category_id = %s AND p.id != %s AND p.is_active = TRUE
                GROUP BY p.id
                ORDER BY avg_rating DESC, p.created_at DESC
                LIMIT 4
            ) as related
        """, (product.get('category_id'), product_id))
        
        related_products = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        # Prepare response
        product_data = dict(product)
        product_data['images'] = images
        product_data['reviews'] = reviews
        product_data['related_products'] = related_products
        
        return jsonify({
            "success": True,
            "product": product_data
        })
        
    except APIException:
        raise
    except Exception as e:
        logger.error(f"Error fetching product {product_id}: {str(e)}")
        raise APIException("Failed to fetch product", 500)

@products.route("/categories", methods=["GET"])
@rate_limit_api
def get_categories():
    """Get all product categories"""
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT c.*, COUNT(p.id) as product_count
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
        logger.error(f"Error fetching categories: {str(e)}")
        raise APIException("Failed to fetch categories", 500)

@products.route("/search", methods=["GET"])
@rate_limit_api
def search_products():
    """Advanced product search with suggestions"""
    try:
        query = request.args.get('q', '').strip()
        
        if not query or len(query) < 2:
            raise APIException("Search query must be at least 2 characters", 400)
        
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Search products
        search_term = f"%{query}%"
        cursor.execute("""
            SELECT p.id, p.name, p.description, p.price, p.image, p.brand,
                   c.name as category_name,
                   COALESCE(AVG(r.rating), 0) as avg_rating,
                   COUNT(r.id) as review_count,
                   MATCH(p.name, p.description) AGAINST(%s IN NATURAL LANGUAGE MODE) as relevance
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.id
            LEFT JOIN reviews r ON p.id = r.product_id
            WHERE p.is_active = TRUE AND (
                p.name LIKE %s OR 
                p.description LIKE %s OR 
                p.brand LIKE %s OR
                MATCH(p.name, p.description) AGAINST(%s IN NATURAL LANGUAGE MODE)
            )
            GROUP BY p.id
            ORDER BY relevance DESC, avg_rating DESC
            LIMIT 20
        """, (query, search_term, search_term, search_term, query))
        
        products_data = cursor.fetchall()
        
        # Get search suggestions
        cursor.execute("""
            SELECT DISTINCT p.name
            FROM products p
            WHERE p.is_active = TRUE AND p.name LIKE %s
            ORDER BY p.name
            LIMIT 5
        """, (search_term,))
        
        suggestions = [row['name'] for row in cursor.fetchall()]
        
        cursor.close()
        conn.close()
        
        return jsonify({
            "success": True,
            "query": query,
            "products": products_data,
            "suggestions": suggestions,
            "total": len(products_data)
        })
        
    except APIException:
        raise
    except Exception as e:
        logger.error(f"Error searching products: {str(e)}")
        raise APIException("Search failed", 500)

@products.route("/<int:product_id>/reviews", methods=["POST"])
@rate_limit_api
@validate_json_input(required_fields=['rating', 'comment'])
def add_product_review(product_id):
    """Add a review for a product"""
    try:
        data = request.validated_json
        rating = int(data.get('rating'))
        comment = data.get('comment')
        user_id = getattr(request, 'current_user_id', 1)  # Default for demo
        
        # Validate rating
        if rating < 1 or rating > 5:
            raise APIException("Rating must be between 1 and 5", 400)
        
        conn = get_connection()
        cursor = conn.cursor()
        
        # Check if product exists
        cursor.execute("SELECT id FROM products WHERE id = %s AND is_active = TRUE", (product_id,))
        if not cursor.fetchone():
            cursor.close()
            conn.close()
            raise APIException("Product not found", 404)
        
        # Check if user already reviewed this product
        cursor.execute("SELECT id FROM reviews WHERE product_id = %s AND user_id = %s", (product_id, user_id))
        if cursor.fetchone():
            cursor.close()
            conn.close()
            raise APIException("You have already reviewed this product", 409)
        
        # Add review
        cursor.execute("""
            INSERT INTO reviews (product_id, user_id, rating, comment)
            VALUES (%s, %s, %s, %s)
        """, (product_id, user_id, rating, comment))
        
        review_id = cursor.lastrowid
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({
            "success": True,
            "message": "Review added successfully",
            "review_id": review_id
        }), 201
        
    except APIException:
        raise
    except Exception as e:
        logger.error(f"Error adding review: {str(e)}")
        raise APIException("Failed to add review", 500)
