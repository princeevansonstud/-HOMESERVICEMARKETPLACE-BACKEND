from flask import Blueprint, request, jsonify
from app.models import Listing

listings_bp = Blueprint("listings", __name__)

@listings_bp.get("/listings/search")
def search_listings():

    keyword = request.args.get("q", "")

    results = Listing.query.filter(
        Listing.title.ilike(f"%{keyword}%") |
        Listing.description.ilike(f"%{keyword}%")
    ).all()

    return jsonify([listing.to_dict() for listing in results]), 200

@listings_bp.get("/listings/category/<string:category>")
def category_filter(category):

    listings = Listing.query.filter_by(category=category).all()

    return jsonify([listing.to_dict() for listing in listings]), 200

@listings_bp.get("/listings/location/<string:location>")
def location_filter(location):

    listings = Listing.query.filter(
        Listing.location.ilike(f"%{location}%")
    ).all()

    return jsonify([listing.to_dict() for listing in listings]), 200

@listings_bp.get("/listings/price")
def filter_price():

    min_price = request.args.get("min", type=float)
    max_price = request.args.get("max", type=float)

    query = Listing.query

    if min_price is not None:
        query = query.filter(Listing.price >= min_price)

    if max_price is not None:
        query = query.filter(Listing.price <= max_price)

    return jsonify([listing.to_dict() for listing in query.all()])

@listings_bp.get("/listings/sort")
def sort_listings():

    order = request.args.get("order", "asc")

    if order == "desc":
        listings = Listing.query.order_by(Listing.price.desc()).all()
    else:
        listings = Listing.query.order_by(Listing.price.asc()).all()

    return jsonify([listing.to_dict() for listing in listings])

@listings_bp.get("/listings")
def all_listings():

    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 10, type=int)

    pagination = Listing.query.paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )

    return jsonify({
        "page": pagination.page,
        "pages": pagination.pages,
        "total": pagination.total,
        "results": [listing.to_dict() for listing in pagination.items]
    })