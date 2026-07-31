from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from app.schemas.inquiry_schema import api_response
from app.services.inquiry_service import (
    create_inquiry,
    get_customer_inquiries,
    get_provider_inquiries,
    get_inquiry_by_id,
    update_inquiry_status,
    delete_inquiry,
    add_inquiry_message,
    InquiryNotFoundError,
    PermissionDeniedError,
    ListingNotFoundError,
    InquiryError,
)

inquiries_bp = Blueprint("inquiries", __name__)


def get_current_user():
    identity = get_jwt_identity()
    if identity is None:
        return None, None
    try:
        user_id = int(identity)
    except (TypeError, ValueError):
        user_id = identity

    claims = get_jwt() or {}
    role = claims.get("role", "customer")
    return user_id, role


@inquiries_bp.route("", methods=["POST"])
@jwt_required()
def create_inquiry_route():
    user_id, user_role = get_current_user()
    if not user_id:
        return jsonify(api_response(success=False, message="Invalid token.")), 401

    if user_role != "customer":
        return jsonify(api_response(success=False, message="Only customers can send inquiries.")), 403

    data = request.get_json(silent=True) or {}

    try:
        result = create_inquiry(data, user_id)
        return jsonify(api_response(success=True, message="Inquiry sent successfully.", data=result)), 201
    except ListingNotFoundError as e:
        return jsonify(api_response(success=False, message=str(e))), 404
    except InquiryError as e:
        return jsonify(api_response(success=False, message=str(e))), 400
    except Exception as e:
        return jsonify(api_response(success=False, message="An unexpected error occurred.", errors={"detail": str(e)})), 500


@inquiries_bp.route("", methods=["GET"])
@jwt_required()
def list_inquiries_route():
    user_id, user_role = get_current_user()
    if not user_id:
        return jsonify(api_response(success=False, message="Invalid token.")), 401

    status_filter = request.args.get("status")

    try:
        if user_role == "customer":
            result = get_customer_inquiries(user_id, status_filter)
        elif user_role == "provider":
            result = get_provider_inquiries(user_id, status_filter)
        else:
            result = []

        return jsonify(api_response(success=True, data=result)), 200
    except Exception as e:
        return jsonify(api_response(success=False, message="Failed to fetch inquiries.", errors={"detail": str(e)})), 500


@inquiries_bp.route("/<int:inquiry_id>", methods=["GET"])
@jwt_required()
def get_inquiry_route(inquiry_id):
    user_id, user_role = get_current_user()
    if not user_id:
        return jsonify(api_response(success=False, message="Invalid token.")), 401

    try:
        result = get_inquiry_by_id(inquiry_id, user_id, user_role)
        return jsonify(api_response(success=True, data=result)), 200
    except InquiryNotFoundError as e:
        return jsonify(api_response(success=False, message=str(e))), 404
    except PermissionDeniedError as e:
        return jsonify(api_response(success=False, message=str(e))), 403
    except Exception as e:
        return jsonify(api_response(success=False, message="An unexpected error occurred.", errors={"detail": str(e)})), 500


@inquiries_bp.route("/<int:inquiry_id>/status", methods=["PATCH"])
@jwt_required()
def update_status_route(inquiry_id):
    user_id, user_role = get_current_user()
    if not user_id:
        return jsonify(api_response(success=False, message="Invalid token.")), 401

    if user_role != "provider":
        return jsonify(api_response(success=False, message="Only providers can update inquiry status.")), 403

    data = request.get_json(silent=True) or {}

    try:
        result = update_inquiry_status(inquiry_id, data, user_id)
        return jsonify(api_response(success=True, message="Status updated successfully.", data=result)), 200
    except InquiryNotFoundError as e:
        return jsonify(api_response(success=False, message=str(e))), 404
    except PermissionDeniedError as e:
        return jsonify(api_response(success=False, message=str(e))), 403
    except InquiryError as e:
        return jsonify(api_response(success=False, message=str(e))), 400
    except Exception as e:
        return jsonify(api_response(success=False, message="An unexpected error occurred.", errors={"detail": str(e)})), 500


@inquiries_bp.route("/<int:inquiry_id>/messages", methods=["POST"])
@jwt_required()
def post_inquiry_message_route(inquiry_id):
    user_id, user_role = get_current_user()
    if not user_id:
        return jsonify(api_response(success=False, message="Invalid token.")), 401

    data = request.get_json(silent=True) or {}

    try:
        result = add_inquiry_message(inquiry_id, data, user_id, user_role)
        return jsonify(api_response(success=True, message="Message sent successfully.", data=result)), 201
    except InquiryNotFoundError as e:
        return jsonify(api_response(success=False, message=str(e))), 404
    except PermissionDeniedError as e:
        return jsonify(api_response(success=False, message=str(e))), 403
    except InquiryError as e:
        return jsonify(api_response(success=False, message=str(e))), 400
    except Exception as e:
        return jsonify(api_response(success=False, message="An unexpected error occurred.", errors={"detail": str(e)})), 500


@inquiries_bp.route("/<int:inquiry_id>", methods=["DELETE"])
@jwt_required()
def delete_inquiry_route(inquiry_id):
    user_id, user_role = get_current_user()
    if not user_id:
        return jsonify(api_response(success=False, message="Invalid token.")), 401

    try:
        delete_inquiry(inquiry_id, user_id, user_role)
        return jsonify(api_response(success=True, message="Inquiry deleted successfully.")), 200
    except InquiryNotFoundError as e:
        return jsonify(api_response(success=False, message=str(e))), 404
    except PermissionDeniedError as e:
        return jsonify(api_response(success=False, message=str(e))), 403
    except Exception as e:
        return jsonify(api_response(success=False, message="An unexpected error occurred.", errors={"detail": str(e)})), 500
