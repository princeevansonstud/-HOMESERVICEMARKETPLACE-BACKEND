"""Application factory and shared Flask extensions."""

import os

from dotenv import load_dotenv
from flask import Flask
from flask_bcrypt import Bcrypt
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy


load_dotenv()

# Extensions are created without an application so models, routes, and tests
# can import them without creating circular imports.
db = SQLAlchemy()
bcrypt = Bcrypt()
jwt = JWTManager()
migrate = Migrate()


def create_app(test_config=None):
    """Create and configure the Home Service Marketplace Flask application.

    ``test_config`` lets tests replace environment-based settings without
    changing the normal application configuration.
    """
    app = Flask(__name__)
    app.config.from_mapping(
        SECRET_KEY=os.getenv("SECRET_KEY", "dev-secret-key-change-me"),
        JWT_SECRET_KEY=os.getenv("JWT_SECRET_KEY", "jwt-dev-secret-change-me"),
        SQLALCHEMY_DATABASE_URI=os.getenv(
            "DATABASE_URL", "sqlite:///homeservice.db"
        ),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )

    if test_config is not None:
        app.config.update(test_config)

    db.init_app(app)
    bcrypt.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)
    CORS(app)

    # Import models after db is defined so SQLAlchemy sees every model before
    # create_all() is called, including the Inquiry model.
    from app import models  # noqa: F401

    from app.routes.admin import admin_bp
    from app.routes.auth import auth_bp
    from app.routes.inquiries import inquiries_bp
    from app.routes.listings import listings_bp
    from app.routes.users import users_bp

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(users_bp, url_prefix="/api/users")
    app.register_blueprint(listings_bp, url_prefix="/api/listings")
    app.register_blueprint(inquiries_bp, url_prefix="/api/inquiries")
    app.register_blueprint(admin_bp, url_prefix="/api/admin")

    # Keep the existing development behavior: the inquiry and listing tables
    # are available even before their Alembic migrations are generated.
    with app.app_context():
        db.create_all()

    return app