"""
App Factory
===========
Creates and configures the Flask application.
This pattern (the "app factory") is the standard way to set up Flask apps
because it avoids circular imports and makes testing easier.
"""

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Initialize extensions (but don't bind them to an app yet)
# This prevents circular imports between models and routes
db = SQLAlchemy()
jwt = JWTManager()
migrate = Migrate()


def create_app():
    """
    Creates and configures the Flask application instance.
    
    Returns:
        Flask: The configured Flask app.
    """
    app = Flask(__name__)

    # ------------------------------------------------------------------
    # Configuration
    # ------------------------------------------------------------------
    
    # Secret key for JWT signing and session cookies
    # In production, this should be a strong random string in your .env file
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-key-change-me")
    
    # JWT configuration
    app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY", "jwt-dev-secret-change-me")
    
    # Database configuration
    # For development, SQLite is easier. Switch to PostgreSQL for production.
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
        "DATABASE_URL", 
        "sqlite:///homeservice.db"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # ------------------------------------------------------------------
    # Initialize Extensions with the App
    # ------------------------------------------------------------------
    
    db.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)
    
    # Enable CORS so your React frontend can call this API
    CORS(app)
    from app import models

    # ------------------------------------------------------------------
    # Register Blueprints (Routes)
    # ------------------------------------------------------------------
    from app.routes.auth import auth_bp
    from app.routes.users import users_bp
    from app.routes.listings import listings_bp
    from app.routes.inquiries import inquiries_bp
    from app.routes.admin import admin_bp

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(users_bp, url_prefix="/api/users")
    app.register_blueprint(listings_bp, url_prefix="/api/listings")
    app.register_blueprint(inquiries_bp, url_prefix="/api/inquiries")
    app.register_blueprint(admin_bp, url_prefix="/api/admin")

    # ------------------------------------------------------------------
    # Create Database Tables
    # ------------------------------------------------------------------
    # db.create_all() looks at all imported models and creates their tables.
    # This only runs when the app starts.
    with app.app_context():
        db.create_all()

    return app