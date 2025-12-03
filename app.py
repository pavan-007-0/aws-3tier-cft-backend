from flask import Flask
from flask_cors import CORS

# Import blueprints
from auth import auth
from cart import cart
from products import products

from create_tables import create_tables

app = Flask(__name__)
CORS(app)

# Register blueprints
app.register_blueprint(auth, url_prefix="/api")
app.register_blueprint(cart, url_prefix="/api/cart")
app.register_blueprint(products, url_prefix="/api/products")  # <-- ADD THIS

@app.route("/")
def home():
    return {"message": "Flask backend is running!"}

if __name__ == "__main__":
    create_tables()
    app.run(debug=True)
