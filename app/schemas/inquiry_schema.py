from marshmallow import Schema, fields, validate


class CustomerInfoSchema(Schema):
    id = fields.Integer(dump_only=True)
    name = fields.String()
    email = fields.Email()


class ListingInfoSchema(Schema):
    id = fields.Integer(dump_only=True)
    title = fields.String()
    provider_id = fields.Integer()


class InquiryMessageSchema(Schema):
    id = fields.Integer(dump_only=True)
    inquiry_id = fields.Integer(dump_only=True)
    message = fields.String()
    created_at = fields.DateTime(dump_only=True, format="iso")
    sender = fields.Nested(CustomerInfoSchema, dump_only=True)


class InquiryMessageCreateSchema(Schema):
    message = fields.String(
        required=True,
        validate=validate.Length(
            min=1,
            max=5000,
            error="Message must be between 1 and 5000 characters."
        ),
        error_messages={"required": "Message is required."}
    )


class InquirySchema(Schema):
    id = fields.Integer(dump_only=True)
    customer_id = fields.Integer(load_only=True)
    listing_id = fields.Integer(load_only=True)
    message = fields.String()
    status = fields.String(dump_only=True)
    created_at = fields.DateTime(dump_only=True, format="iso")
    updated_at = fields.DateTime(dump_only=True, format="iso")

    customer = fields.Nested(CustomerInfoSchema, dump_only=True)
    listing = fields.Nested(ListingInfoSchema, dump_only=True)
    messages = fields.List(fields.Nested(InquiryMessageSchema), dump_only=True)


class InquiryCreateSchema(Schema):
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


class InquiryUpdateStatusSchema(Schema):
    status = fields.String(
        required=True,
        validate=validate.OneOf(
            ["pending", "replied", "closed"],
            error="Status must be one of: pending, replied, closed."
        ),
        error_messages={"required": "Status is required."}
    )


def api_response(success=True, message="", data=None, errors=None):
    response = {
        "success": success,
        "message": message
    }
    if data is not None:
        response["data"] = data
    if errors is not None:
        response["errors"] = errors
    return response
