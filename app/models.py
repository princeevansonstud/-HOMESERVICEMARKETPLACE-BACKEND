"""
Models

All database models live in this single file.
This is a team convention —everyone adds their models here.
"""

from app import db


# ===================================================================
# USER MODEL (Auth Team)
# ===================================================================

class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="customer")
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "role": self.role,
        }

    def __repr__(self):
        return f"<User {self.name}>"


# ===================================================================
# LISTING MODEL (Temporary Stub)
# ===================================================================

class Listing(db.Model):
    """
    Temporary stub model for Listings.
    Replace with the Listings team's full model when merged.
    """

    __tablename__ = "listings"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(50))
    location = db.Column(db.String(100))
    price_range = db.Column(db.String(50))
    provider_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False,
    )
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    def __repr__(self):
        return f"<Listing {self.title}>"


# ===================================================================
# INQUIRY MODEL (Your Feature)
# ===================================================================

class Inquiry(db.Model):
    """
    Represents a customer inquiry about a home service listing.
    """

    __tablename__ = "inquiries"

    id = db.Column(db.Integer, primary_key=True)

    customer_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="SET NULL"),
        nullable=False,
        index=True,
    )

    listing_id = db.Column(
        db.Integer,
        db.ForeignKey("listings.id", ondelete="SET NULL"),
        nullable=False,
        index=True,
    )

    message = db.Column(db.Text, nullable=False)

    status = db.Column(
        db.String(20),
        nullable=False,
        default="pending",
        server_default="pending",
    )

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        server_default=db.func.now(),
    )

    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        server_default=db.func.now(),
        onupdate=db.func.now(),
    )

    customer = db.relationship(
        "User",
        backref=db.backref("inquiries", lazy="dynamic"),
        lazy="joined",
    )

    listing = db.relationship(
        "Listing",
        backref=db.backref("inquiries", lazy="dynamic"),
        lazy="joined",
    )

    def __repr__(self):
        return (
            f"<Inquiry id={self.id} "
            f"customer_id={self.customer_id} "
            f"listing_id={self.listing_id} "
            f"status={self.status}>"
        )