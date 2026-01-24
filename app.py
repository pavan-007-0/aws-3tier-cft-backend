from flask import Flask
from flask_cors import CORS
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import blueprints
from auth import auth
from cart import cart
from products import products
from orders import orders
from admin import admin
from chatbot import chatbot

from create_tables import create_tables
from error_handlers import (
    register_error_handlers,
    setup_logging,
    log_request_info,
    register_api_exception_handler
)
from security import limiter, SecurityHeaders

# Initialize Flask app
app = Flask(__name__)

# -------------------------
# Configuration
# -------------------------
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'fallback-secret-key')
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'fallback-jwt-secret')
app.config['ENV'] = os.getenv('FLASK_ENV', 'development')

# -------------------------
# Extensions
# -------------------------
CORS(
    app,
    origins=[
        'http://localhost:4200',
        'https://yourdomain.com'  # replace later with frontend ALB DNS
    ]
)

limiter.init_app(app)

# -------------------------
# Logging & Error Handling
# -------------------------
setup_logging(app)
register_error_handlers(app)
register_api_exception_handler(app)
log_request_info(app)

# -------------------------
# Security Headers
# -------------------------
@app.after_request
def after_request(response):
    return SecurityHeaders.add_security_headers(response)

# -------------------------
# Register Blueprints
# -------------------------
app.register_blueprint(auth, url_prefix="/api")
app.register_blueprint(cart, url_prefix="/api/cart")
app.register_blueprint(products, url_prefix="/api/products")
app.register_blueprint(orders, url_prefix="/api/orders")
app.register_blueprint(admin, url_prefix="/api/admin")
app.register_blueprint(chatbot, url_prefix="/api/chatbot")

# -------------------------
# Health & Root Endpoints
# -------------------------
@app.route("/", methods=["GET"])
def home():
    return {
        "message": "Flask backend is running!",
        "status": "healthy"
    }, 200


@app.route("/health", methods=["GET"])
def health_check():
    return {
        "status": "healthy",
        "service": "backend-api",
        "version": "1.0.0"
    }, 200

# -------------------------
# Application Entry Point
# -------------------------
if __name__ == "__main__":
    create_tables()
    app.run(
        host="0.0.0.0",
        port=int(os.getenv("PORT", 5000)),
        debug=os.getenv("FLASK_DEBUG", "false").lower() == "true"
    )
0# -------------------------
if __name__ == "__main__":
    create_tables()
    app.run(
        host="0.0.0.0",
        port=int(os.getenv("PORT", 5000)),
        debug=os.getenv("FLASK_DEBUG", "false").lower() == "true"
    )
