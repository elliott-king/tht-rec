from datetime import datetime, timedelta
from flask import request
import sqlalchemy as sa

from app.api import api
from app.api.error import error_response
from app.models import Restaurant, db, User


@api.route("/restaurants", methods=["GET"])
def restaurants():
    """Get all restaurants"""
    page = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 10, type=int), 100)
    return Restaurant.to_collection_dict(
        sa.select(Restaurant), page, per_page, "api.restaurants"
    )


@api.route("/restaurant/<int:id>", methods=["GET"])
def restaurant(id):
    return db.get_or_404(Restaurant, id).to_dict()


@api.route("/restaurant/search", methods=["GET"])
def restaurant_search():
    """Restaraunts that are available within a given time block

    Example:
    http://localhost:5000/restaurant/search?user_ids=1&user_ids=2&datetime=2024-08-04T18%3A15%3A06.844854%2B00%3A00
    """
    page = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 10, type=int), 100)
    user_ids = request.args.getlist("user_ids")
    dt = request.args.get("datetime", type=str)
    print("uids", user_ids)

    if len(user_ids) == 0:
        return error_response(400, "No user ids provided")

    try:
        dt = datetime.fromisoformat(dt)
    except Exception:
        return error_response(400, f"Invalid datetime {dt}")

    for id_ in user_ids:
        # Could be more efficiently handled, but this makes the helper method simpler
        db.get_or_404(User, id_)

    end = dt + timedelta(hours=2)
    # If Person A makes a group reservation for Persons A/B/C, Persons A/B/C cannot
    # make or be included in time-overlapping reservations.
    if User.has_reservation(user_ids, dt, end):
        return error_response(400, "User has reservation at this time")

    query = Restaurant.search_has_table(user_ids, dt, end)
    return Restaurant.to_collection_dict(query, page, per_page, "api.restaurant_search")


@api.route("/restaurant/<int:id>/reservation", methods=["POST"])
def create_reservation(id):
    """Create reservation for given restaurant"""
    db.get_or_404(Restaurant, id).to_dict()
    user_ids = request.args.getlist("user_ids")
    dt = request.args.get("datetime", type=str)

    try:
        dt = datetime.fromisoformat(dt)
    except Exception:
        return error_response(400, f"Invalid datetime {dt}")

    for id_ in user_ids:
        # Could be more efficiently handled, but this makes the helper method simpler
        db.get_or_404(User, id_)

    end = dt + timedelta(hours=2)
    if User.has_reservation(user_ids, dt, end):
        return error_response(400, "User has reservation at this time")

    restaurant_query = Restaurant.search_has_table(user_ids, dt, end)
    restaurant_query.where(Restaurant.id == id).limit(1)
    restaurant = db.session.scalars(restaurant_query).first()
    if not restaurant:
        return error_response(400, "Restaurant not available at this time")

    res = restaurant.book_table(user_ids, dt, end)
    return res.to_dict()
