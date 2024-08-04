# Running
If you have poetry, you can install the deps & run with `FLASK_APP=rec.py poetry run flask run`.

However, you can run easily with Docker:
- `docker build -t rec:latest .`
- `docker run --name rec -p 5000:5000 --rm rec:latest`

The deliverable api endpoints are:
- `/restaurant/search`
- `/restaurant/<int:id>/reservation`
- `/reservation/<int:id>`

For example: http://localhost:5000/restaurant/search?user_ids=1&user_ids=2&datetime=2024-08-04T18%3A15%3A06.844854%2B00%3A00

Other endpoints:
- You can get a list of some of the models (reservation, restaurant, user)
- You can directly GET the above models (eg, `/reservation/<int:id>`)
- User reservations: `/user/<int:id>/reservations`

# Thoughts

You can find the complex queries in `models.py`, and there are tests in `test_rec.py` that may clarify the usage.

SQLAlchemy has an old-style query syntax (more standard ORM-style) and a new-style that (more like SQL), so you will see a mix. Queries + flask context can sometimes be touchy, so I may have overdone the `db.session.add()` calls.

The table search is not as clean as I'd like. Figuring out the right `CONTAINS` query for the restrictions/endorsements was taking too long, so I made it raw Python. The other queries are closer to SQL - this allows us to leverage `PaginatedAPIMixin`, which can paginate a list response before the query is resolved.

If you are wondering why I'm using Poetry on top of Python (instead of just having a `requirements` file), it's because I just hate dependency management in Python. I don't care if it's just my computer and nobody else directly runs it. Interestingly, this means I'm not using gunicorn. Gunicorn (or another webserver) would be necessary for production, so I'd have to adapt the dependency management to support both. gunicorn can be used with poetry, but requires some more setup.

There's a lot of API methods. I used many of them for debugging. I find it easier to write a four-line API endpoint than jumping into the SQLite db. For production use, I'd use PostgreSQL along with a investigation tool just for Postgres.


## possible extensions:
- extend "vegan" to include "vegetarian" for user or restaurant
- add UUIDs to all models
- mvc formatting (helper methods for queries aren't easily chained)
- pre-load relationships for some queries
- late-evaluate many-to-many relationships
- only query needed columns (eg, ids/names) b/c ORM queries whole python object
- only soft-delete reservations (this would need query change)
- abbreviated links for relationships