"""
Inquiry Service
===============
Business logic for the Inquiries / Contact Flow module.

This file knows NOTHING about HTTP. It only works with:
- Database queries (SQLAlchemy)
- Data validation (Marshmallow schemas)
- Business rules (who can do what)

Routes will call these functions and convert exceptions to HTTP responses.
"""

from marshmallow import ValidationError

from app import db
from app.models import Inquiry, Listing
from app.schemas.inquiry_schema import (
    InquirySchema,
    InquiryCreateSchema,
    InquiryUpdateStatusSchema,
)


# Pre-instantiated schemas for reuse
inquiry_schema = InquirySchema()
inquiries_schema = InquirySchema(many=True)
create_schema = InquiryCreateSchema()
update_status_schema = InquiryUpdateStatusSchema()


# ------------------------------------------------------------------
# Custom Exceptions
# ------------------------------------------------------------------
# We use custom exceptions so routes can distinguish between
# "expected" errors (return 404/403) and "unexpected" bugs (return 500).

class InquiryError(Exception):
    """Base exception for inquiry-related errors."""
    pass


class InquiryNotFoundError(InquiryError):
    """Raised when an inquiry ID doesn't exist."""
    pass


class PermissionDeniedError(InquiryError):
    """Raised when a user tries to access something they don't own."""
    pass


class ListingNotFoundError(InquiryError):
    """Raised when a customer inquires about a non-existent listing."""
    pass


# ------------------------------------------------------------------
# Create Inquiry
# ------------------------------------------------------------------

def create_inquiry(data, customer_id):
    """
    Creates a new inquiry from a customer about a service listing.

    Business rules:
        1. The listing must exist.
        2. The customer cannot inquire about their own listing.
        3. Message is validated by Marshmallow.

    Args:
        data (dict): Raw JSON from client. Must have 'listing_id' and 'message'.
        customer_id (int): Logged-in customer's ID (from JWT).

    Returns:
        dict: Serialized inquiry data.

    Raises:
        ValidationError: If input data fails schema validation.
        ListingNotFoundError: If the listing doesn't exist.
        InquiryError: If customer tries to self-inquire.
    """
    # Step 1: Validate incoming data
    validated = create_schema.load(data)
    listing_id = validated["listing_id"]
    message = validated["message"]

    # Step 2: Verify the listing exists
    listing = Listing.query.get(listing_id)
    if not listing:
        raise ListingNotFoundError(
            f"Listing with ID {listing_id} does not exist."
        )

    # Step 3: Prevent self-inquiry
    if listing.provider_id == customer_id:
        raise InquiryError(
            "You cannot send an inquiry about your own listing."
        )

    # Step 4: Create the inquiry
    inquiry = Inquiry(
        customer_id=customer_id,
        listing_id=listing_id,
        message=message,
        status="pending"
    )

    # Step 5: Save to database
    try:
        db.session.add(inquiry)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        raise InquiryError(f"Failed to save inquiry: {str(e)}")

    return inquiry_schema.dump(inquiry)


# ------------------------------------------------------------------
# Get Customer's Inquiries
# ------------------------------------------------------------------

def get_customer_inquiries(customer_id, status_filter=None):
    """
    Fetches all inquiries sent by a specific customer.

    Args:
        customer_id (int): The logged-in customer's ID.
        status_filter (str, optional): 'pending', 'replied', or 'closed'.

    Returns:
        list: Serialized inquiry dictionaries.
    """
    query = Inquiry.query.filter_by(customer_id=customer_id)

    if status_filter:
        query = query.filter_by(status=status_filter)

    # Newest first
    query = query.order_by(Inquiry.created_at.desc())

    return inquiries_schema.dump(query.all())


# ------------------------------------------------------------------
# Get Provider's Inquiries
# ------------------------------------------------------------------

def get_provider_inquiries(provider_id, status_filter=None):
    """
    Fetches all inquiries for listings owned by a specific provider.

    Uses a SQL JOIN for efficiency instead of multiple queries.

    Args:
        provider_id (int): The logged-in provider's ID.
        status_filter (str, optional): Filter by status.

    Returns:
        list: Serialized inquiry dictionaries.
    """
    query = (
        Inquiry.query
        .join(Listing, Inquiry.listing_id == Listing.id)
        .filter(Listing.provider_id == provider_id)
    )

    if status_filter:
        query = query.filter(Inquiry.status == status_filter)

    query = query.order_by(Inquiry.created_at.desc())

    return inquiries_schema.dump(query.all())


# ------------------------------------------------------------------
# Get Single Inquiry
# ------------------------------------------------------------------

def get_inquiry_by_id(inquiry_id, user_id, user_role):
    """
    Fetches a single inquiry if the user is authorized.

    Authorization:
        - Customer: only their own inquiries.
        - Provider: only inquiries for their listings.
        - Admin: all inquiries.

    Args:
        inquiry_id (int): Inquiry ID from URL.
        user_id (int): Logged-in user's ID.
        user_role (str): 'customer', 'provider', or 'admin'.

    Returns:
        dict: Serialized inquiry data.

    Raises:
        InquiryNotFoundError: If inquiry doesn't exist.
        PermissionDeniedError: If user isn't authorized.
    """
    inquiry = Inquiry.query.get(inquiry_id)

    if not inquiry:
        raise InquiryNotFoundError(
            f"Inquiry with ID {inquiry_id} not found."
        )

    if user_role == "admin":
        pass  # Admins can see everything

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


# ------------------------------------------------------------------
# Update Inquiry Status
# ------------------------------------------------------------------

def update_inquiry_status(inquiry_id, data, provider_id):
    """
    Updates the status of an inquiry (provider only).

    Valid transitions:
        pending -> replied
        pending -> closed
        replied -> closed

    Args:
        inquiry_id (int): Inquiry to update.
        data (dict): Must contain 'status'.
        provider_id (int): Logged-in provider's ID.

    Returns:
        dict: Updated inquiry data.

    Raises:
        InquiryNotFoundError: If inquiry doesn't exist.
        PermissionDeniedError: If provider doesn't own the listing.
        InquiryError: If status transition is invalid.
    """
    validated = update_status_schema.load(data)
    new_status = validated["status"]

    inquiry = Inquiry.query.get(inquiry_id)
    if not inquiry:
        raise InquiryNotFoundError(
            f"Inquiry with ID {inquiry_id} not found."
        )

    # Verify provider owns the listing
    listing = Listing.query.get(inquiry.listing_id)
    if not listing or listing.provider_id != provider_id:
        raise PermissionDeniedError(
            "You can only update inquiries for your own listings."
        )

    # Validate status transition
    valid_transitions = {
        "pending": ["replied", "closed"],
        "replied": ["closed"],
        "closed": []
    }

    current_status = inquiry.status
    allowed = valid_transitions.get(current_status, [])

    if new_status not in allowed:
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


# ------------------------------------------------------------------
# Delete Inquiry
# ------------------------------------------------------------------

def delete_inquiry(inquiry_id, user_id, user_role):
    """
    Deletes an inquiry.

    Authorization:
        - Customer: can delete their own inquiries.
        - Admin: can delete any inquiry.
        - Provider: cannot delete (only close via status update).

    Args:
        inquiry_id (int): Inquiry to delete.
        user_id (int): Logged-in user's ID.
        user_role (str): 'customer', 'provider', or 'admin'.

    Returns:
        bool: True if deleted.

    Raises:
        InquiryNotFoundError: If inquiry doesn't exist.
        PermissionDeniedError: If user cannot delete.
    """
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