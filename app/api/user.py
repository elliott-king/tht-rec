from app.api import api
from flask import request
from app.models import User, db, Reservation
import sqlalchemy as sa


@api.route("/users", methods=["GET"])
def users():
    """Get all users"""
    page = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 5, type=int), 100)
    return User.to_collection_dict(sa.select(User), page, per_page, "api.users")


@api.route("/user/<int:id>", methods=["GET"])
def user(id):
    return db.get_or_404(User, id).to_dict()


@api.route("/user/<int:id>/reservations", methods=["GET"])
def user_reservations(id):
    """Get reservations for a user"""
    db.get_or_404(User, id)
    page = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 5, type=int), 100)
    return Reservation.to_collection_dict(
        sa.select(Reservation).where(Reservation.users.any(User.id == id)),
        page,
        per_page,
        "api.users",
    )
