"""
Inquiry Schemas
===============
Handles validation of incoming requests and serialization of outgoing responses.

Install: pip install marshmallow
"""

from marshmallow import Schema, fields, validate


# ------------------------------------------------------------------
# Nested Schemas (for embedding related data in API responses)
# ------------------------------------------------------------------

class CustomerInfoSchema(Schema):
    """
    Minimal customer data embedded in inquiry responses.
    """
    id = fields.Integer(dump_only=True)
    name = fields.String()
    email = fields.Email()


class ListingInfoSchema(Schema):
    """
    Minimal listing data embedded in inquiry responses.
    """
    id = fields.Integer(dump_only=True)
    title = fields.String()
    provider_id = fields.Integer()


# ------------------------------------------------------------------
# Main Inquiry Schema (for GET responses)
# ------------------------------------------------------------------

class InquirySchema(Schema):
    """
    Full inquiry schema for serialization.
    Used when returning inquiry data to the frontend.
    """
    id = fields.Integer(dump_only=True)
    customer_id = fields.Integer(load_only=True)
    listing_id = fields.Integer(load_only=True)
    message = fields.String(dump_only=True)
    status = fields.String(dump_only=True)
    created_at = fields.DateTime(dump_only=True, format="iso")
    updated_at = fields.DateTime(dump_only=True, format="iso")
    
    customer = fields.Nested(CustomerInfoSchema, dump_only=True)
    listing = fields.Nested(ListingInfoSchema, dump_only=True)


# ------------------------------------------------------------------
# Create Schema (for POST /api/inquiries)
# ------------------------------------------------------------------

class InquiryCreateSchema(Schema):
    """
    Validation schema for creating a new inquiry.
    Customers send: listing_id + message
    """
    listing_id = fields.Integer(
        required=True,
        error_messages={"required": "Listing ID is required."}
    )
    
    message = fields.String(
        required=True,
        validate=validate.Length(
            min=1,
            max=5000,
            error="Message must be between 1 and 5000 characters."
        ),
        error_messages={"required": "Message is required."}
    )


# ------------------------------------------------------------------
# Update Status Schema (for PATCH /api/inquiries/<id>/status)
# ------------------------------------------------------------------

class InquiryUpdateStatusSchema(Schema):
    """
    Validation schema for updating inquiry status.
    Only providers can update status.
    """
    status = fields.String(
        required=True,
        validate=validate.OneOf(
            ["pending", "replied", "closed"],
            error="Status must be one of: pending, replied, closed."
        ),
        error_messages={"required": "Status is required."}
    )


# ------------------------------------------------------------------
# API Response Helper
# ------------------------------------------------------------------

def api_response(success=True, message="", data=None, errors=None):
    """
    Builds a consistent JSON response envelope.
    
    Success: { "success": true, "message": "...", "data": {...} }
    Error:   { "success": false, "message": "...", "errors": {...} }
    """
    response = {
        "success": success,
        "message": message
    }
    if data is not None:
        response["data"] = data
    if errors is not None:
        response["errors"] = errors
    return response