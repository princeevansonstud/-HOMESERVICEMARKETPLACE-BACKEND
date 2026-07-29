"""
Inquiry Routes
==============
REST API endpoints for the Inquiries / Contact Flow module.

Base URL: /api/inquiries

Endpoints:
    POST   /api/inquiries              → Create inquiry (customer)
    GET    /api/inquiries              → List inquiries (customer sees theirs, provider sees inbox)
    GET    /api/inquiries/<id>         → Get single inquiry (auth check)
    PATCH  /api/inquiries/<id>/status  → Update status (provider only)
    DELETE /api/inquiries/<id>         → Delete inquiry (customer or admin)

JWT Integration:
    All routes are protected with @jwt_required().
    The JWT payload contains: { "sub": user_id, "role": "customer|provider|admin" }
"""

from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from flask import Blueprint
inquiries_bp = Blueprint("inquiries", __name__)
from app.services.inquiry_service import (
    create_inquiry,
    get_customer_inquiries,
    get_provider_inquiries,
    get_inquiry_by_id,
    update_inquiry_status,
    delete_inquiry,
    InquiryNotFoundError,
    PermissionDeniedError,
    ListingNotFoundError,
    InquiryError,
)
from app.schemas.inquiry_schema import api_response


# ------------------------------------------------------------------
# Helper: Extract user info from JWT
# ------------------------------------------------------------------
# The Auth team's JWT contains: { "sub": user_id, "role": "customer" }
# We wrap this in a helper so routes stay clean.

def get_current_user():
    """
    Extracts user_id and role from the JWT token.
    
    Returns:
        tuple: (user_id, user_role)
    """
    identity = get_jwt_identity()
    # identity could be a dict or just the user_id depending on Auth team's setup
    # Based on your answers, it contains user_id and role.
    if isinstance(identity, dict):
        return identity.get("sub"), identity.get("role", "customer")
    return identity, "customer"  # Fallback if identity is just the ID


# ------------------------------------------------------------------
# POST /api/inquiries
# Create a new inquiry (Customer only)
# ------------------------------------------------------------------

@inquiries_bp.route("", methods=["POST"])
@jwt_required()
def create_inquiry_route():
    """
    Customer sends an inquiry about a service listing.
    
    Request Body:
        {
            "listing_id": 1,
            "message": "Hi, are you available this weekend?"
        }
    
    Returns:
        201 Created: { success: true, message: "...", data: {...} }
        400 Bad Request: Validation failed
        404 Not Found: Listing doesn't exist
    """
    user_id, user_role = get_current_user()

    # Only customers can send inquiries
    if user_role != "customer":
        return jsonify(api_response(
            success=False,
            message="Only customers can send inquiries."
        )), 403

    data = request.get_json(silent=True) or {}

    try:
        result = create_inquiry(data, user_id)
        return jsonify(api_response(
            success=True,
            message="Inquiry sent successfully.",
            data=result
        )), 201

    except ListingNotFoundError as e:
        return jsonify(api_response(
            success=False,
            message=str(e)
        )), 404

    except InquiryError as e:
        return jsonify(api_response(
            success=False,
            message=str(e)
        )), 400

    except Exception as e:
        return jsonify(api_response(
            success=False,
            message="An unexpected error occurred.",
            errors={"detail": str(e)}
        )), 500


# ------------------------------------------------------------------
# GET /api/inquiries
# List inquiries (role-based filtering)
# ------------------------------------------------------------------

@inquiries_bp.route("", methods=["GET"])
@jwt_required()
def list_inquiries_route():
    """
    Returns inquiries based on the user's role:
        - Customer: All inquiries they sent (with optional ?status= filter)
        - Provider: All inquiries for their listings (with optional ?status= filter)
        - Admin: All inquiries (future expansion)
    
    Query Params:
        ?status=pending|replied|closed (optional)
    
    Returns:
        200 OK: { success: true, data: [...] }
    """
    user_id, user_role = get_current_user()
    status_filter = request.args.get("status")

    try:
        if user_role == "customer":
            result = get_customer_inquiries(user_id, status_filter)

        elif user_role == "provider":
            result = get_provider_inquiries(user_id, status_filter)

        else:
            # Admin or other roles — return empty for now
            result = []

        return jsonify(api_response(
            success=True,
            data=result
        )), 200

    except Exception as e:
        return jsonify(api_response(
            success=False,
            message="Failed to fetch inquiries.",
            errors={"detail": str(e)}
        )), 500


# ------------------------------------------------------------------
# GET /api/inquiries/<id>
# Get a single inquiry by ID
# ------------------------------------------------------------------

@inquiries_bp.route("/<int:inquiry_id>", methods=["GET"])
@jwt_required()
def get_inquiry_route(inquiry_id):
    """
    Fetch a single inquiry if the user is authorized to view it.
    
    Returns:
        200 OK: { success: true, data: {...} }
        404 Not Found: Inquiry doesn't exist
        403 Forbidden: User can't view this inquiry
    """
    user_id, user_role = get_current_user()

    try:
        result = get_inquiry_by_id(inquiry_id, user_id, user_role)
        return jsonify(api_response(
            success=True,
            data=result
        )), 200

    except InquiryNotFoundError as e:
        return jsonify(api_response(
            success=False,
            message=str(e)
        )), 404

    except PermissionDeniedError as e:
        return jsonify(api_response(
            success=False,
            message=str(e)
        )), 403

    except Exception as e:
        return jsonify(api_response(
            success=False,
            message="An unexpected error occurred.",
            errors={"detail": str(e)}
        )), 500


# ------------------------------------------------------------------
# PATCH /api/inquiries/<id>/status
# Update inquiry status (Provider only)
# ------------------------------------------------------------------

@inquiries_bp.route("/<int:inquiry_id>/status", methods=["PATCH"])
@jwt_required()
def update_status_route(inquiry_id):
    """
    Provider updates the status of an inquiry.
    
    Request Body:
        { "status": "replied" }  or  { "status": "closed" }
    
    Returns:
        200 OK: Updated inquiry
        400 Bad Request: Invalid status or transition
        403 Forbidden: Not the listing owner
        404 Not Found: Inquiry doesn't exist
    """
    user_id, user_role = get_current_user()

    if user_role != "provider":
        return jsonify(api_response(
            success=False,
            message="Only providers can update inquiry status."
        )), 403

    data = request.get_json(silent=True) or {}

    try:
        result = update_inquiry_status(inquiry_id, data, user_id)
        return jsonify(api_response(
            success=True,
            message="Status updated successfully.",
            data=result
        )), 200

    except InquiryNotFoundError as e:
        return jsonify(api_response(
            success=False,
            message=str(e)
        )), 404

    except PermissionDeniedError as e:
        return jsonify(api_response(
            success=False,
            message=str(e)
        )), 403

    except InquiryError as e:
        return jsonify(api_response(
            success=False,
            message=str(e)
        )), 400

    except Exception as e:
        return jsonify(api_response(
            success=False,
            message="An unexpected error occurred.",
            errors={"detail": str(e)}
        )), 500


# ------------------------------------------------------------------
# DELETE /api/inquiries/<id>
# Delete an inquiry (Customer or Admin)
# ------------------------------------------------------------------

@inquiries_bp.route("/<int:inquiry_id>", methods=["DELETE"])
@jwt_required()
def delete_inquiry_route(inquiry_id):
    """
    Delete an inquiry.
    
    Authorization:
        - Customer: can delete their own inquiries
        - Admin: can delete any inquiry
        - Provider: cannot delete
    
    Returns:
        200 OK: Successfully deleted
        403 Forbidden: Not authorized
        404 Not Found: Inquiry doesn't exist
    """
    user_id, user_role = get_current_user()

    try:
        delete_inquiry(inquiry_id, user_id, user_role)
        return jsonify(api_response(
            success=True,
            message="Inquiry deleted successfully."
        )), 200

    except InquiryNotFoundError as e:
        return jsonify(api_response(
            success=False,
            message=str(e)
        )), 404

    except PermissionDeniedError as e:
        return jsonify(api_response(
            success=False,
            message=str(e)
        )), 403

    except Exception as e:
        return jsonify(api_response(
            success=False,
            message="An unexpected error occurred.",
            errors={"detail": str(e)}
        )), 500