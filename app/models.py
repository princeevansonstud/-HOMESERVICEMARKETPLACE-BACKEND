"""
Models
======
All database models live in this single file.
This is a team convention — everyone adds their models here.
"""

from app import db


# ===================================================================
# STUB MODELS (owned by other team members)
# ===================================================================
# These are minimal placeholders so your Inquiry model can reference
# them via ForeignKey. When your teammates finish their models,
# just replace these stubs with their full implementations.
# DO NOT DELETE these stubs until the real models are merged.

class User(db.Model):
    """
    STUB: Owned by the Auth team.
    Replace this with the real User model when ready.
    """
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="customer")
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    def __repr__(self):
        return f"<User {self.name}>"


class Listing(db.Model):
    """
    STUB: Owned by the Listings team.
    Replace this with the real Listing model when ready.
    """
    __tablename__ = "listings"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(50))
    location = db.Column(db.String(100))
    price_range = db.Column(db.String(50))
    provider_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    def __repr__(self):
        return f"<Listing {self.title}>"


# ===================================================================
# YOUR MODEL: Inquiry / Contact Flow
# ===================================================================

class Inquiry(db.Model):
    """
    Represents a customer inquiry about a home service listing.

    A customer sends an inquiry to a provider about a specific listing.
    The provider can view it in their inbox and update the status.
    """

    __tablename__ = "inquiries"

    id = db.Column(db.Integer, primary_key=True)

    # The customer who sent the inquiry
    customer_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="SET NULL"),
        nullable=False,
        index=True
    )

    # The service listing being inquired about
    listing_id = db.Column(
        db.Integer,
        db.ForeignKey("listings.id", ondelete="SET NULL"),
        nullable=False,
        index=True
    )

    # The inquiry message
    message = db.Column(db.Text, nullable=False)

    # Status: pending, replied, closed
    status = db.Column(
        db.String(20),
        nullable=False,
        default="pending",
        server_default="pending"
    )

    # Timestamps
    created_at = db.Column(
        db.DateTime,
        nullable=False,
        server_default=db.func.now()
    )

    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        server_default=db.func.now(),
        onupdate=db.func.now()
    )

    # Relationships
    customer = db.relationship(
        "User",
        backref=db.backref("inquiries", lazy="dynamic"),
        lazy="joined"
    )

    listing = db.relationship(
        "Listing",
        backref=db.backref("inquiries", lazy="dynamic"),
        lazy="joined"
    )

    def __repr__(self):
        return (
            f"<Inquiry id={self.id} "
            f"customer_id={self.customer_id} "
            f"listing_id={self.listing_id} "
            f"status={self.status}>"
        )