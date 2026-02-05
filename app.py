from flask import Flask
from flask_cors import CORS
import os
from dotenv import load_dotenv

if os.getenv("FLASK_ENV") != "production":
    load_dotenv()

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

app = Flask(__name__)

app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "fallback-secret-key")
app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY", "fallback-jwt-secret")
app.config["ENV"] = os.getenv("FLASK_ENV", "development")

CORS(app, origins=["*"])
limiter.init_app(app)

setup_logging(app)
register_error_handlers(app)
register_api_exception_handler(app)
log_request_info(app)

@app.after_request
def after_request(response):
    return SecurityHeaders.add_security_headers(response)

app.register_blueprint(auth, url_prefix="/api")
app.register_blueprint(cart, url_prefix="/api/cart")
app.register_blueprint(products, url_prefix="/api/products")
app.register_blueprint(orders, url_prefix="/api/orders")
app.register_blueprint(admin, url_prefix
