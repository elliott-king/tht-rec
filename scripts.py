from datetime import datetime, timedelta
import flask_migrate as fm

from app.app import create_app
from app.models import User, Restaurant, Table, Restriction, db, Reservation


def reinit_tables():
    """Set up db as the suggestion given

    https://docs.google.com/spreadsheets/d/1qES1ch7ZbnunZE0GEESNuL73jzqDadHBk2LEDy027-w/edit?usp=sharing
    """

    app = create_app()
    app.app_context().push()

    # Use flask-migrate to create tables, to make sure they have the correct metadata
    fm.downgrade(revision="base")
    fm.upgrade()

    endorsements = [
        "vegetarian",
        "vegan",
        "gluten free",
        "paleo",
    ]
    users = [
        ["Michael", ["Vegetarian"]],
        ["George Michael", ["Vegetarian", "Gluten Free"]],
        ["Lucile", ["Gluten Free"]],
        ["Gob", ["Paleo"]],
        ["Tobias", []],
        ["Maeby", ["Vegan"]],
    ]
    restaurants = [
        ["Lardo", ["Gluten Free"], {2: 4, 4: 2, 6: 1}],
        ["Panadería Rosetta", ["Vegetarian", "Gluten Free"], {2: 3, 4: 2, 6: 0}],
        ["Tetetlán", ["Paleo", "Gluten Free"], {2: 4, 4: 2, 6: 1}],
        ["Falling Piano Brewing Co", [], {2: 5, 4: 5, 6: 5}],
        ["u.to.pi.a", ["Vegan", "Vegetarian"], {2: 2, 4: 0, 6: 0}],
    ]

    reservations = [
        [datetime(2020, 1, 1, 1), 5, [1, 2, 3, 4]],
        [datetime(2020, 1, 1, 1), 1, [5, 6]],
    ]

    # Create basic endorsements
    for endorsement in endorsements:
        db.session.add(Restriction(name=endorsement.lower()))
    db.session.commit()

    for [user, endorsements] in users:
        u = User(name=user)
        for endorsement in endorsements:
            # See note in models.py about restriction format
            u.restrictions.append(
                Restriction.query.filter_by(name=endorsement.lower()).first()
            )
        db.session.add(u)
    db.session.commit()

    for [restaurant, endorsements, tables] in restaurants:
        r = Restaurant(name=restaurant)
        for endorsement in endorsements:
            r.endorsements.append(
                Restriction.query.filter_by(name=endorsement.lower()).first()
            )
        for [capacity, count] in tables.items():
            for i in range(count):
                r.tables.append(Table(capacity=capacity))
        db.session.add(r)
    db.session.commit()

    for [start, tableid, userids] in reservations:
        end = start + timedelta(hours=2)
        r = Reservation(
            start=start,
            end=end,
            table_id=tableid,
        )
        db.session.add(r)
        for userid in userids:
            r.users.append(User.query.get(userid))
    db.session.commit()


if __name__ == "__main__":
    reinit_tables()
    print("Tables reinitialized")
