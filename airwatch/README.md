# AirWatch

API for air-quality readings stored in PostgreSQL.

| Endpoint          | Description                                         |
|-------------------|-----------------------------------------------------|
| `POST /readings`  | body `{"sensor": "amphi-a", "pm25": 12.5}`          |
| `GET /readings`   | latest readings (`?limit=20`)                       |
| `GET /stats`      | number of readings and average PM2.5 per sensor     |
| `GET /health`     | 200 if the database is reachable, 503 otherwise     |

`simulate.py` sends random readings to the API running in the same container:
`python simulate.py 20`.
