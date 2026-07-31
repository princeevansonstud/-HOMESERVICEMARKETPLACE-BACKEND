from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required
from app.models import db, User, Service

admin_bp = Blueprint('admin', __name__)


@admin_bp.route('/users', methods=['GET'])
@jwt_required(optional=True)
def get_users():
    users = User.query.all()
    return jsonify([user.to_dict() for user in users])


@admin_bp.route('/users/<int:user_id>', methods=['DELETE'])
@jwt_required(optional=True)
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    return jsonify({"message": "User deleted successfully"})


@admin_bp.route('/listings', methods=['GET'])
@jwt_required(optional=True)
def get_listings():
    services = Service.query.all()
    return jsonify([service.to_dict() for service in services])
