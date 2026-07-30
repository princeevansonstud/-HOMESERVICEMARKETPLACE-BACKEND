from datetime import datetime
from app import db


class Listing(db.Model):
    __tablename__ = "listings"

    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(db.String(150), nullable=False)

    description = db.Column(db.Text, nullable=False)

    category = db.Column(db.String(100), nullable=False)

    location = db.Column(db.String(100), nullable=False)

    price = db.Column(db.Float, nullable=False)

    image_url = db.Column(db.String(255))

    is_available = db.Column(db.Boolean, default=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    provider_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    provider = db.relationship(
        "User",
        back_populates="listings"
    )

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "category": self.category,
            "location": self.location,
            "price": self.price,
            "image_url": self.image_url,
            "is_available": self.is_available,
            "provider_id": self.provider_id,
            "created_at": self.created_at.isoformat()
        }