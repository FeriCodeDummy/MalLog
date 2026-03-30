# Anomaly Detection Service

Flask microservice that receives normalized logs, sends them to RabbitMQ for
asynchronous processing, stores results in MySQL, and emits result events back
to RabbitMQ.

## API

- `GET /health`
- `GET /openapi.json`
- `POST /api/v1/anomaly/jobs`
- `GET /api/v1/anomaly/jobs/<uid>`

## Run locally

```bash
python -m pip install -r requirements.txt
python run.py
```

## Tests

```bash
python -m unittest discover -s tests -p "test_*.py"
```
