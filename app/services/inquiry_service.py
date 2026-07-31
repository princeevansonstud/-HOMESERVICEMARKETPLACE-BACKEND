from datetime import datetime
from marshmallow import ValidationError

from app import db
from app.models import Inquiry, Listing, InquiryMessage
from app.schemas.inquiry_schema import (
    InquirySchema,
    InquiryCreateSchema,
    InquiryUpdateStatusSchema,
)


inquiry_schema = InquirySchema()
inquiries_schema = InquirySchema(many=True)
create_schema = InquiryCreateSchema()
update_status_schema = InquiryUpdateStatusSchema()


class InquiryError(Exception):
    pass


class InquiryNotFoundError(InquiryError):
    pass


class PermissionDeniedError(InquiryError):
    pass


class ListingNotFoundError(InquiryError):
    pass


def create_inquiry(data, customer_id):
    validated = create_schema.load(data)
    listing_id = validated["listing_id"]
    message = validated["message"]

    listing = Listing.query.get(listing_id)
    if not listing:
        raise ListingNotFoundError(
            f"Listing with ID {listing_id} does not exist."
        )

    if listing.provider_id == customer_id:
        raise InquiryError(
            "You cannot send an inquiry about your own listing."
        )

    inquiry = Inquiry(
        customer_id=customer_id,
        listing_id=listing_id,
        message=message,
        status="pending"
    )

    try:
        db.session.add(inquiry)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        raise InquiryError(f"Failed to save inquiry: {str(e)}")

    return inquiry_schema.dump(inquiry)


def get_customer_inquiries(customer_id, status_filter=None):
    query = Inquiry.query.options(db.joinedload(
        Inquiry.messages)).filter_by(customer_id=customer_id)

    if status_filter:
        query = query.filter_by(status=status_filter)

    query = query.order_by(Inquiry.created_at.desc())

    return inquiries_schema.dump(query.all())


def get_provider_inquiries(provider_id, status_filter=None):
    query = (
        Inquiry.query
        .options(db.joinedload(Inquiry.messages))
        .join(Listing, Inquiry.listing_id == Listing.id)
        .filter(Listing.provider_id == provider_id)
    )

    if status_filter:
        query = query.filter(Inquiry.status == status_filter)

    query = query.order_by(Inquiry.created_at.desc())

    return inquiries_schema.dump(query.all())


def get_inquiry_by_id(inquiry_id, user_id, user_role):
    inquiry = Inquiry.query.options(
        db.joinedload(Inquiry.messages)).get(inquiry_id)

    if not inquiry:
        raise InquiryNotFoundError(
            f"Inquiry with ID {inquiry_id} not found."
        )

    if user_role == "admin":
        pass

    elif user_role == "customer":
        if inquiry.customer_id != user_id:
            raise PermissionDeniedError(
                "You can only view inquiries you sent."
            )

    elif user_role == "provider":
        listing = Listing.query.get(inquiry.listing_id)
        if not listing or listing.provider_id != user_id:
            raise PermissionDeniedError(
                "You can only view inquiries for your own listings."
            )

    else:
        raise PermissionDeniedError("Invalid user role.")

    return inquiry_schema.dump(inquiry)


def update_inquiry_status(inquiry_id, data, provider_id):
    validated = update_status_schema.load(data)
    new_status = validated.get("status")
    provider_response = data.get("provider_response")

    inquiry = Inquiry.query.get(inquiry_id)
    if not inquiry:
        raise InquiryNotFoundError(
            f"Inquiry with ID {inquiry_id} not found."
        )

    listing = Listing.query.get(inquiry.listing_id)
    if not listing or listing.provider_id != provider_id:
        raise PermissionDeniedError(
            "You can only update inquiries for your own listings."
        )

    if provider_response is not None:
        inquiry.provider_response = provider_response
        if not new_status and inquiry.status == "pending":
            new_status = "replied"

    if new_status:
        valid_transitions = {
            "pending": ["replied", "closed"],
            "replied": ["closed"],
            "closed": []
        }

        current_status = inquiry.status
        allowed = valid_transitions.get(current_status, [])

        if new_status not in allowed and new_status != current_status:
            raise InquiryError(
                f"Cannot change status from '{current_status}' to '{new_status}'. "
                f"Allowed: {allowed}"
            )

        inquiry.status = new_status

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        raise InquiryError(f"Failed to update status: {str(e)}")

    return inquiry_schema.dump(inquiry)


def delete_inquiry(inquiry_id, user_id, user_role):
    inquiry = Inquiry.query.get(inquiry_id)

    if not inquiry:
        raise InquiryNotFoundError(
            f"Inquiry with ID {inquiry_id} not found."
        )

    can_delete = False

    if user_role == "admin":
        can_delete = True
    elif user_role == "customer" and inquiry.customer_id == user_id:
        can_delete = True

    if not can_delete:
        raise PermissionDeniedError(
            "You do not have permission to delete this inquiry."
        )

    try:
        db.session.delete(inquiry)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        raise InquiryError(f"Failed to delete inquiry: {str(e)}")

    return True


def add_inquiry_message(inquiry_id, data, user_id, user_role):
    inquiry = Inquiry.query.get(inquiry_id)
    if not inquiry:
        raise InquiryNotFoundError("Inquiry not found.")

    if user_role == "customer" and inquiry.customer_id != user_id:
        raise PermissionDeniedError("Unauthorized to reply to this inquiry.")

    if user_role == "provider":
        listing = Listing.query.get(inquiry.listing_id)
        if not listing or listing.provider_id != user_id:
            raise PermissionDeniedError(
                "Unauthorized to reply to this inquiry.")

    message_text = data.get("message")
    if not message_text:
        raise InquiryError("Message content is required.")

    new_msg = InquiryMessage(
        inquiry_id=inquiry.id,
        sender_id=user_id,
        message=message_text,
        created_at=datetime.utcnow()
    )
    db.session.add(new_msg)

    if user_role == "provider" and inquiry.status == "pending":
        inquiry.status = "replied"

    try:
        db.session.commit()
        db.session.refresh(new_msg)
    except Exception as e:
        db.session.rollback()
        raise InquiryError(f"Failed to save message: {str(e)}")

    return {
        "id": new_msg.id,
        "inquiry_id": new_msg.inquiry_id,
        "message": new_msg.message,
        "created_at": new_msg.created_at.isoformat(),
        "sender": {
            "id": new_msg.sender.id,
            "name": new_msg.sender.name,
            "role": user_role
        }
    }
