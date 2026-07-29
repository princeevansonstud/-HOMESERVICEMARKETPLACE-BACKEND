"""
Auth Routes
===========
Owned by the Auth team.
Handles signup, login, JWT token generation.
"""

from flask import Blueprint

auth_bp = Blueprint("auth", __name__)