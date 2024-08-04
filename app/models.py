from datetime import datetime, timezone, timedelta
from flask import url_for
from flask_sqlalchemy import SQLAlchemy
import sqlalchemy as sa
import sqlalchemy.orm as so

db = SQLAlchemy()


class PaginatedAPIMixin(object):
    """Used to easily represent paginated queries.

    Plagiarized from: https://github.com/miguelgrinberg/microblog/blob/main/app/models.py#L63
    """

    @staticmethod
    def to_collection_dict(query, page, per_page, endpoint, **kwargs):
        resources = db.paginate(query, page=page, per_page=per_page, error_out=False)
        data = {
            "items": [item.to_dict() for item in resources.items],
            "_meta": {
                "page": page,
                "per_page": per_page,
                "total_pages": resources.pages,
                "total_items": resources.total,
            },
            "_links": {
                "self": url_for(
                    endpoint, page=page, per_page=per_page, _external=True, **kwargs
                ),
                "next": (
                    url_for(
                        endpoint,
                        page=page + 1,
                        per_page=per_page,
                        _external=True,
                        **kwargs,
                    )
                    if resources.has_next
                    else None
                ),
                "prev": (
                    url_for(
                        endpoint,
                        page=page - 1,
                        per_page=per_page,
                        _external=True,
                        **kwargs,
                    )
                    if resources.has_prev
                    else None
                ),
            },
        }
        return data


user_restriction = sa.Table(
    "user_restriction",
    db.Model.metadata,
    sa.Column("user_id", sa.ForeignKey("user.id")),
    sa.Column("restriction_id", sa.ForeignKey("restriction.id")),
)

restaurant_endorsement = sa.Table(
    "restaurant_endorsement",
    db.Model.metadata,
    sa.Column("restaurant_id", sa.ForeignKey("restaurant.id")),
    sa.Column("restriction_id", sa.ForeignKey("restriction.id")),
)

user_reservation = sa.Table(
    "user_reservation",
    db.Model.metadata,
    sa.Column("user_id", sa.ForeignKey("user.id")),
    sa.Column("reservation_id", sa.ForeignKey("reservation.id")),
)


class Restriction(db.Model):
    """Dietary restrictions

    For simplicity, these are strings. To create a user, we expect an exact (non case-sensitive) match.
    For a prod app, we'd want enums + a helper to convert to string + an ILIKE query for searching.
    """

    __tablename__ = "restriction"

    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    name: so.Mapped[str] = so.mapped_column(
        sa.String(64), index=True, unique=True, nullable=False
    )
    users: so.Mapped[list["User"]] = so.relationship(
        secondary=user_restriction, back_populates="restrictions"
    )

    def __repr__(self):
        return f"<Restriction {self.id}:{self.name}>"


class User(PaginatedAPIMixin, db.Model):
    __tablename__ = "user"

    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    name: so.Mapped[str] = so.mapped_column(
        sa.String(64), index=True, unique=True, nullable=False
    )
    restrictions: so.Mapped[list["Restriction"]] = so.relationship(
        secondary=user_restriction,
        back_populates="users",
    )
    reservations: so.Mapped[list["Reservation"]] = so.relationship(
        secondary=user_reservation,
        back_populates="users",
    )

    @classmethod
    def has_reservation(cls, userids: list[int], start: datetime, end: datetime):
        """Any user already has reservation for given time"""
        c = (
            db.session.query(Reservation)
            .filter(
                Reservation.start <= end,
                Reservation.end >= start,
                Reservation.users.any(User.id.in_(userids)),
            )
            .count()
        )
        return c > 0

    def __repr__(self):
        return "<User {}>".format(self.name)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "restrictions": [r.name.title() for r in self.restrictions],
            "_links": {
                "reservations": url_for(
                    "api.user_reservations", id=self.id, _external=True
                )
            },
        }


class Restaurant(PaginatedAPIMixin, db.Model):
    __tablename__ = "restaurant"

    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    name: so.Mapped[str] = so.mapped_column(
        sa.String(64), index=True, unique=True, nullable=False
    )

    endorsements: so.Mapped[list["Restriction"]] = so.relationship(
        secondary=restaurant_endorsement
    )
    tables: so.Mapped[list["Table"]] = so.relationship(back_populates="restaurant")

    @classmethod
    def search_has_table(cls, user_ids: list[int], start: datetime, end: datetime):
        """Restaurants that are available within a given time block"""

        size = len(user_ids)

        # Available table ids subquery
        table_q = db.session.query(Table.id).filter(
            Table.capacity >= size,
            ~Table.reservations.any(
                sa.and_(
                    Reservation.start <= end,
                    Reservation.end >= start,
                )
            ),
        )

        # All restriction ids subquery
        restriction_q = db.session.query(Restriction.id).filter(
            Restriction.users.any(User.id.in_(user_ids))
        )
        restriction_ids = set([r.id for r in restriction_q.all()])

        # NOTE: due to time constraints, this query is not fully fleshed out
        # Keeping this here for personal reference
        #     restaurant_q = (
        #         sa.select(Restaurant)
        #         .options(so.joinedload(Restaurant.endorsements, innerjoin=True))
        #         .where(
        #             # .options(so.joinedload(Restaurant.endorsements)).where(
        #             sa.and_(
        #                 Restaurant.tables.any(Table.id.in_(table_q)),
        #                 Restriction.id.in_(restriction_q),
        #             )
        #         )
        #     )
        restaurant_q = sa.select(Restaurant).where(
            Restaurant.tables.any(Table.id.in_(table_q)),
        )
        out = db.session.scalars(restaurant_q).all()

        def filter_(r):
            return restriction_ids.issubset({e.id for e in r.endorsements})

        restaurant_ids = [r.id for r in out if filter_(r)]

        return sa.select(Restaurant).where(Restaurant.id.in_(restaurant_ids))

    def __repr__(self):
        return "<Restaurant {}>".format(self.name)

    def book_table(self, user_ids: list[int], start: datetime, end: datetime):
        size = len(user_ids)
        table_q = (
            db.session.query(Table.id)
            .filter(
                Table.capacity >= size,
                Table.restaurant_id == self.id,
                ~Table.reservations.any(
                    sa.and_(
                        Reservation.start <= end,
                        Reservation.end >= start,
                    )
                ),
            )
            .order_by(Table.capacity.asc())
            .limit(1)
        )

        table_id = db.session.scalars(table_q).first()
        res = Reservation(
            start=start,
            end=end,
            table_id=table_id,
        )
        db.session.add(res)

        for uid in user_ids:
            res.users.append(User.query.get(uid))
        db.session.commit()
        return res

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "endorsements": [e.name.title() for e in self.endorsements],
        }


class Table(db.Model):
    __tablename__ = "table"

    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    capacity: so.Mapped[int] = so.mapped_column(sa.Integer, nullable=False)
    restaurant_id: so.Mapped[int] = so.mapped_column(
        sa.ForeignKey("restaurant.id"), nullable=False
    )

    restaurant: so.Mapped["Restaurant"] = so.relationship(
        "Restaurant", back_populates="tables"
    )
    reservations: so.Mapped[list["Reservation"]] = so.relationship(
        back_populates="table"
    )

    def __repr__(self):
        return f"<Table {self.id}:{self.capacity}>"


class Reservation(PaginatedAPIMixin, db.Model):
    __tablename__ = "reservation"

    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    start: so.Mapped[datetime] = so.mapped_column(sa.DateTime, nullable=False)
    end: so.Mapped[datetime] = so.mapped_column(sa.DateTime, nullable=False)
    table_id: so.Mapped[int] = so.mapped_column(
        sa.ForeignKey("table.id"), nullable=False
    )

    table: so.Mapped["Table"] = so.relationship(back_populates="reservations")
    users: so.Mapped[list["User"]] = so.relationship(
        secondary=user_reservation,
        back_populates="reservations",
    )

    def to_dict(self):
        return {
            "id": self.id,
            "start": self.start.replace(tzinfo=timezone.utc).isoformat(),
            "end": self.end.replace(tzinfo=timezone.utc).isoformat(),
            "size": len(self.users),
            "_links": {
                "users": [
                    url_for("api.user", id=u.id, _external=True) for u in self.users
                ]
            },
        }
