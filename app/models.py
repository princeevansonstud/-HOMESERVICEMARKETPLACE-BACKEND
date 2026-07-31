from app import db


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


class Listing(db.Model):
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


class Service(db.Model):
    __tablename__ = "services"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)
    provider_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=False
    )
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    provider = db.relationship(
        "User", backref=db.backref("services", lazy="dynamic")
    )

    def __repr__(self):
        return f"<Service {self.title}>"


class InquiryMessage(db.Model):
    __tablename__ = "inquiry_messages"

    id = db.Column(db.Integer, primary_key=True)
    inquiry_id = db.Column(db.Integer, db.ForeignKey(
        "inquiries.id", ondelete="CASCADE"), nullable=False, index=True)
    sender_id = db.Column(db.Integer, db.ForeignKey(
        "users.id", ondelete="CASCADE"), nullable=False)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    sender = db.relationship("User", lazy="joined")

    def to_dict(self):
        return {
            "id": self.id,
            "inquiry_id": self.inquiry_id,
            "sender_id": self.sender_id,
            "message": self.message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "sender": {
                "id": self.sender.id,
                "name": self.sender.name,
                "role": self.sender.role
            } if self.sender else None
        }

    def __repr__(self):
        return f"<InquiryMessage id={self.id} inquiry_id={self.inquiry_id}>"


class Inquiry(db.Model):
    __tablename__ = "inquiries"

    id = db.Column(db.Integer, primary_key=True)

    customer_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    listing_id = db.Column(
        db.Integer,
        db.ForeignKey("listings.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    message = db.Column(db.Text, nullable=False)

    provider_response = db.Column(db.Text, nullable=True)

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

    messages = db.relationship(
        "InquiryMessage",
        backref="inquiry",
        cascade="all, delete-orphan",
        lazy="joined"
    )

    def to_dict(self):
        return {
            "id": self.id,
            "customer_id": self.customer_id,
            "listing_id": self.listing_id,
            "message": self.message,
            "provider_response": self.provider_response,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "messages": [msg.to_dict() for msg in self.messages],
            "listing": {
                "id": self.listing.id,
                "title": self.listing.title,
                "category": self.listing.category,
                "location": self.listing.location,
            } if self.listing else None,
            "customer": {
                "id": self.customer.id,
                "name": self.customer.name,
                "email": self.customer.email,
            } if self.customer else None,
        }

    def __repr__(self):
        return (
            f"<Inquiry id={self.id} "
            f"customer_id={self.customer_id} "
            f"listing_id={self.listing_id} "
            f"status={self.status}>"
        )
