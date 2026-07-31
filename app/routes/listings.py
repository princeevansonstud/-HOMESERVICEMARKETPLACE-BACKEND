"""Persisted service-listing API used by browsing and inquiry flows."""

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt, get_jwt_identity, jwt_required

from app import db
from app.models import Listing


listings_bp = Blueprint("listings", __name__)


def serialize_listing(listing):
    """Return the shape consumed by the React listing pages."""
    return {
        "id": listing.id,
        "title": listing.title,
        "description": listing.description,
        "category": listing.category,
        "location": listing.location,
        "price_range": listing.price_range,
        "provider_id": listing.provider_id,
        "status": "active",
        "created_at": listing.created_at.isoformat() if listing.created_at else None,
    }


def current_user():
    return get_jwt_identity(), get_jwt().get("role")


def can_manage(listing, user_id, role):
    return role == "admin" or listing.provider_id == int(user_id)


@listings_bp.route("", methods=["GET"])
def list_listings():
    """List all service listings, optionally filtered by provider."""
    provider_id = request.args.get("provider_id", type=int)
    query = Listing.query
    if provider_id is not None:
        query = query.filter_by(provider_id=provider_id)
    return jsonify([serialize_listing(listing) for listing in query.all()]), 200


@listings_bp.route("/mine", methods=["GET"])
@jwt_required()
def my_listings():
    """List listings belonging to the authenticated provider."""
    user_id, role = current_user()
    if role not in {"provider", "admin"}:
        return jsonify({"error": "Provider account required"}), 403
    listings = Listing.query.filter_by(provider_id=int(user_id)).all()
    return jsonify([serialize_listing(listing) for listing in listings]), 200


@listings_bp.route("/<int:listing_id>", methods=["GET"])
def get_listing(listing_id):
    listing = db.session.get(Listing, listing_id)
    if not listing:
        return jsonify({"error": "Listing not found"}), 404
    return jsonify(serialize_listing(listing)), 200


@listings_bp.route("", methods=["POST"])
@jwt_required()
def create_listing():
    """Create a listing for the authenticated provider."""
    user_id, role = current_user()
    if role != "provider":
        return jsonify({"error": "Only providers can create listings"}), 403

    data = request.get_json(silent=True) or {}
    required_fields = ("title", "category", "price_range")
    missing_fields = [field for field in required_fields if not data.get(field)]
    if missing_fields:
        return jsonify({"error": f"Missing required fields: {', '.join(missing_fields)}"}), 400

    listing = Listing(
        title=data["title"],
        description=data.get("description"),
        category=data["category"],
        location=data.get("location"),
        price_range=data["price_range"],
        provider_id=int(user_id),
    )
    db.session.add(listing)
    db.session.commit()
    return jsonify(serialize_listing(listing)), 201


@listings_bp.route("/<int:listing_id>", methods=["PATCH"])
@jwt_required()
def update_listing(listing_id):
    listing = db.session.get(Listing, listing_id)
    if not listing:
        return jsonify({"error": "Listing not found"}), 404

    user_id, role = current_user()
    if not can_manage(listing, user_id, role):
        return jsonify({"error": "You cannot edit this listing"}), 403

    data = request.get_json(silent=True) or {}
    for field in ("title", "description", "category", "location", "price_range"):
        if field in data:
            setattr(listing, field, data[field])
    db.session.commit()
    return jsonify(serialize_listing(listing)), 200


@listings_bp.route("/<int:listing_id>", methods=["DELETE"])
@jwt_required()
def delete_listing(listing_id):
    listing = db.session.get(Listing, listing_id)
    if not listing:
        return jsonify({"error": "Listing not found"}), 404

    user_id, role = current_user()
    if not can_manage(listing, user_id, role):
        return jsonify({"error": "You cannot delete this listing"}), 403

    db.session.delete(listing)
    db.session.commit()
    return jsonify({"success": True}), 200
