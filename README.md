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


## possible extensions:
- extend "vegan" to include "vegetarian" for user or restaurant
- add UUIDs to all models
- mvc formatting (helper methods for queries aren't easily chained)
- pre-load relationships for some queries
- late-evaluate many-to-many relationships
- only query needed columns (eg, ids/names) b/c ORM queries whole python object
- only soft-delete reservations (this would need query change)
- abbreviated links for relationships