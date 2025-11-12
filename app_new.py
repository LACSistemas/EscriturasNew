"""Flask application - Refactored modular version"""
import os
import sys
import logging
from flask import Flask
from dotenv import load_dotenv

# Import configuration and initialization
from config import config, MAX_CONTENT_LENGTH
from database import init_database

# Import blueprints
from routes.health_routes import health_bp
from routes.auth_routes import auth_bp
from routes.cartorio_routes import cartorio_bp
from routes.process_routes import process_bp, set_clients

# Force unbuffered output
sys.stdout = sys.__stdout__
sys.stderr = sys.__stderr__

load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH
app.secret_key = os.getenv("FLASK_SECRET_KEY", "your-secret-key-here")

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
app.logger.setLevel(logging.DEBUG)

# Initialize database
try:
    init_database()
    app.logger.info("Database initialized successfully")
except Exception as e:
    app.logger.error(f"Database initialization failed: {e}")

# Initialize external clients
config.initialize_vision_client()
config.initialize_gemini_client()

# Set clients for process routes
set_clients(config.get_vision_client(), config.get_gemini_model())

# Register blueprints
app.register_blueprint(health_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(cartorio_bp)
app.register_blueprint(process_bp)

# Error handlers
@app.errorhandler(404)
def not_found(error):
    from flask import jsonify
    return jsonify({"error": "Resource not found"}), 404


@app.errorhandler(500)
def internal_error(error):
    from flask import jsonify
    return jsonify({"error": "Internal server error"}), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
