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
from error_handlers import register_error_handlers, setup_logging, log_request_info, register_api_exception_handler
from security import limiter, SecurityHeaders

app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'fallback-secret-key')
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'fallback-jwt-secret')
app.config['ENV'] = os.getenv('FLASK_ENV', 'development')

# Initialize extensions
CORS(app, origins=['http://localhost:4200', 'https://yourdomain.com'])
limiter.init_app(app)

# Setup logging and error handling
setup_logging(app)
register_error_handlers(app)
register_api_exception_handler(app)
log_request_info(app)

# Add security headers to all responses
@app.after_request
def after_request(response):
    return SecurityHeaders.add_security_headers(response)

# Register blueprints
app.register_blueprint(auth, url_prefix="/api")
app.register_blueprint(cart, url_prefix="/api/cart")
app.register_blueprint(products, url_prefix="/api/products")
app.register_blueprint(orders, url_prefix="/api/orders")
app.register_blueprint(admin, url_prefix="/api/admin")
app.register_blueprint(chatbot, url_prefix="/api/chatbot")

@app.route("/")
def home():
    return {"message": "Flask backend is running!", "status": "healthy"}

@app.route("/health")
def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": "2024-01-01T00:00:00Z",
        "version": "1.0.0"
    }

if __name__ == "__main__":
    create_tables()
    app.run(
        debug=os.getenv('FLASK_DEBUG', 'True').lower() == 'true',
        host='0.0.0.0',
        port=int(os.getenv('PORT', 5000))
    )
