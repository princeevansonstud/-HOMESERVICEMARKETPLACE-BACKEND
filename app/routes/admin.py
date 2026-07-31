from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import User, Listing

admin_bp = Blueprint("admin", __name__)


@admin_bp.route("/users", methods=["GET"])
@jwt_required()
def get_all_users():
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    if not current_user or current_user.role != "admin":
        return jsonify({"error": "Unauthorized access"}), 403

    users = User.query.all()
    return jsonify([user.to_dict() for user in users]), 200


@admin_bp.route("/users/<int:user_id>", methods=["DELETE"])
@jwt_required()
def delete_user(user_id):
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    if not current_user or current_user.role != "admin":
        return jsonify({"error": "Unauthorized access"}), 403

    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    return jsonify({"message": "User deleted successfully"}), 200


@admin_bp.route("/listings", methods=["GET"])
@jwt_required()
def get_all_admin_listings():
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    if not current_user or current_user.role != "admin":
        return jsonify({"error": "Unauthorized access"}), 403

    listings = Listing.query.all()
    return jsonify([{
        "id": l.id,
        "title": l.title,
        "description": l.description,
        "category": l.category,
        "location": l.location,
        "price_range": l.price_range,
        "provider_id": l.provider_id
    } for l in listings]), 200


@admin_bp.route("/listings/<int:listing_id>", methods=["DELETE"])
@jwt_required()
def delete_admin_listing(listing_id):
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    if not current_user or current_user.role != "admin":
        return jsonify({"error": "Unauthorized access"}), 403

    listing = Listing.query.get_or_404(listing_id)
    db.session.delete(listing)
    db.session.commit()
    return jsonify({"message": "Listing deleted successfully"}), 200
