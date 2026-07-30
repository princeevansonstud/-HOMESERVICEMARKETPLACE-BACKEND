import re
from flask import Blueprint, request, jsonify
from app import db, bcrypt
from app.models import User
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, get_jwt

auth_bp = Blueprint("auth", __name__)

EMAIL_REGEX = r"^[^\s@]+@[^\s@]+\.[^\s@]+$"


@auth_bp.route("/signup", methods=["POST"])
def signup():
    data = request.get_json()

    name = data.get("name")
    email = data.get("email")
    password = data.get("password")
    role = data.get("role")

    if not all([name, email, password, role]):
        return jsonify({"error": "name, email, password, and role are required"}), 400

    if role not in ["provider", "customer", "admin"]:
        return jsonify({"error": "role must be 'provider', 'customer', or 'admin'"}), 400

    if not re.match(EMAIL_REGEX, email):
        return jsonify({"error": "Invalid email format"}), 400

    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters"}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({"error": "Email already registered"}), 409

    password_hash = bcrypt.generate_password_hash(password).decode("utf-8")

    user = User(name=name, email=email, password_hash=password_hash, role=role)
    db.session.add(user)
    db.session.commit()

    return jsonify(user.to_dict()), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    # Hardcoded admin check
    if email == "admin@gmail.com" and password == "adminme":
        user = User.query.filter_by(email=email).first()
        if not user:
            password_hash = bcrypt.generate_password_hash(
                password).decode("utf-8")
            user = User(name="Super Admin", email=email,
                        password_hash=password_hash, role="admin")
            db.session.add(user)
            db.session.commit()

        access_token = create_access_token(
            identity=str(user.id),
            additional_claims={"role": "admin"}
        )
        return jsonify({"access_token": access_token, "user": user.to_dict()}), 200

    user = User.query.filter_by(email=email).first()

    if not user or not bcrypt.check_password_hash(user.password_hash, password):
        return jsonify({"error": "Invalid email or password"}), 401

    access_token = create_access_token(
        identity=str(user.id),
        additional_claims={"role": user.role}
    )

    return jsonify({"access_token": access_token, "user": user.to_dict()}), 200


@auth_bp.route("/logout", methods=["POST"])
@jwt_required()
def logout():
    return jsonify({"message": "Successfully logged out"}), 200


@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def me():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    if not user:
        return jsonify({"error": "User not found"}), 404

    return jsonify(user.to_dict()), 200
