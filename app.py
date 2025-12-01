from flask import Flask
from flask_cors import CORS

# Import blueprints
from auth import auth
from cart import cart

app = Flask(__name__)
CORS(app)

# Register blueprints
app.register_blueprint(auth, url_prefix="/api")
app.register_blueprint(cart, url_prefix="/api/cart")

@app.route("/")
def home():
    return {"message": "Flask backend is running!"}

if __name__ == "__main__":
    app.run(debug=True)
