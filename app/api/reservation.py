from app.api import api
from flask import request
from app.models import db, Reservation
import sqlalchemy as sa


@api.route("/reservations", methods=["GET"])
def reservations():
    """Get all reservations"""
    page = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 5, type=int), 100)
    return Reservation.to_collection_dict(
        sa.select(Reservation), page, per_page, "api.reservations"
    )


@api.route("/reservation/<int:id>", methods=["DELETE"])
def delete_reservation(id):
    """Delete reservation"""
    reservation = db.get_or_404(Reservation, id)
    db.session.delete(reservation)
    db.session.commit()
    return "", 204
