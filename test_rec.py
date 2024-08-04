from datetime import datetime, timezone, timedelta
import pytest
import unittest

from app.app import create_app
from app.models import db
from app.models import User
from app.models import Reservation
from app.models import Restaurant
from app.models import Table
from app.models import Restriction
from config import Config


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite://"
    ELASTICSEARCH_URL = None


class TestUser(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        users = [
            ["Michael", True],
            ["George", True],
            ["Lucile", False],
            ["Gob", False],
            ["Tobias", False],
            ["Maeby", False],
        ]
        restaurants = [
            "Lardo",
            "Panadería Rosetta",
            "Tetetlán",
            "Falling Piano Brewing Co",
            "u.to.pi.a",
        ]

        for restaurant in restaurants:
            r = Restaurant(name=restaurant)
            r.tables.append(Table(capacity=2))
            db.session.add(r)
        db.session.commit()

        start = datetime(2020, 1, 1, 2)
        end = datetime(2020, 1, 1, 3)

        for i, [user, has_res] in enumerate(users):
            u = User(name=user)
            db.session.add(u)
            if has_res:
                r = Reservation(start=start, end=end, table_id=i)
                r.users.append(u)
                db.session.add(r)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test__has_reservations(self):
        tests = [
            [
                "no users",
                [],
                datetime(2020, 1, 1, 1),
                datetime(2020, 1, 1, 3),
                False,
            ],
            [
                "one user without res",
                [3],
                datetime(2020, 1, 1, 1),
                datetime(2020, 1, 1, 3),
                False,
            ],
            [
                "one user with res",
                [1],
                datetime(2020, 1, 1, 1),
                datetime(2020, 1, 1, 3),
                True,
            ],
            [
                "multiple users without res",
                [3, 4],
                datetime(2020, 1, 1, 1),
                datetime(2020, 1, 1, 3),
                False,
            ],
            [
                "multiple users with res",
                [1, 2],
                datetime(2020, 1, 1, 1),
                datetime(2020, 1, 1, 3),
                True,
            ],
            [
                "mix of users with & without res",
                [2, 3],
                datetime(2020, 1, 1, 1),
                datetime(2020, 1, 1, 3),
                True,
            ],
            [
                "user has res for different time",
                [1],
                datetime(2020, 1, 3, 1),
                datetime(2020, 1, 3, 3),
                False,
            ],
        ]

        for [name, userids, start, end, expected] in tests:
            try:
                self.assertEqual(User.has_reservation(userids, start, end), expected)
            except Exception as e:
                print(f"Failed test {name}: {e}")
                raise e


class TestRestaurant(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

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
                for _ in range(count):
                    r.tables.append(Table(capacity=capacity))
            db.session.add(r)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test__search_has_table__users_with_restrictions__only_restaurants_supporting(
        self,
    ):
        paleos = [4]
        veggies = [1]
        none = [5]

        tests = [
            ["no restrictions", none, 5],
            ["paleo", paleos, 1],
            ["veggies", veggies, 2],
            ["paleo & veggies & none", none + paleos + veggies, 0],
        ]

        for [name, userids, expected] in tests:

            # start & end shouldn't matter
            start = datetime(2020, 1, 1, 2)
            end = datetime(2020, 1, 1, 3)

            try:
                query = Restaurant.search_has_table(userids, start, end)
                out = db.session.scalars(query).all()
                self.assertEqual(len(out), expected)
            except Exception as e:
                print(f"Failed test {name}: {e}")
                raise e

    def test__search_has_table__reserved_table_timeslot__no_reserved_tables(self):

        users = [User.query.get(1)]

        # First reserve all tables for a few restaurants
        rids = [1, 2]
        for rid in rids:
            rest = Restaurant.query.get(rid)
            for table in rest.tables:
                r = Reservation(
                    start=datetime(2020, 1, 1, 1),
                    end=datetime(2020, 1, 1, 3),
                    table_id=table.id,
                )
                db.session.add(r)
                for user in users:
                    r.users.append(user)

        db.session.commit()

        # Those two restaurants should be excluded from the search, leaving 3
        start = datetime(2020, 1, 1, 2)
        end = datetime(2020, 1, 1, 3)
        query = Restaurant.search_has_table([5], start, end)
        out = db.session.scalars(query).all()
        self.assertEqual(len(out), 3)

    def test__search_has_table__nonreserved_table_timeslot__includes_reserved_tables(
        self,
    ):

        users = [User.query.get(1)]

        # First reserve all tables for a few restaurants at a certain time
        rids = [1, 2]
        for rid in rids:
            rest = Restaurant.query.get(rid)
            for table in rest.tables:
                r = Reservation(
                    start=datetime(2020, 1, 1, 1),
                    end=datetime(2020, 1, 1, 3),
                    table_id=table.id,
                )
                db.session.add(r)
                for user in users:
                    r.users.append(user)

        db.session.commit()

        # Those reservations should be ignored at this datetime
        start = datetime(2020, 1, 1, 12)
        end = datetime(2020, 1, 1, 13)
        query = Restaurant.search_has_table([5], start, end)
        out = db.session.scalars(query).all()
        self.assertEqual(len(out), 5)

    def test__book_table__no_reservations__books_smallest_available_table_and_creates_object(
        self,
    ):
        user_ids = [1]
        start = datetime(2020, 1, 1, 1)
        end = datetime(2020, 1, 1, 3)
        restaurants = Restaurant.query.all()
        count = len(restaurants)

        # setup: create reservations
        for restaurant in restaurants:
            restaurant.book_table(user_ids, start, end)

        reservations = Reservation.query.all()

        # Make sure one res for each restaurant
        self.assertEqual(len(set([r.table.restaurant_id for r in reservations])), count)

        # Make sure each is smallest table
        for r in reservations:
            self.assertEqual(r.table.capacity, 2)

        # Make sure user is attached to each res
        for r in reservations:
            self.assertEqual([u.id for u in r.users], user_ids)
