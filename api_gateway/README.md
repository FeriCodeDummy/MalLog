# API Gateway

Flask API gateway for the system-test flow:

1. Reads every `*.log` file in `./system_test` (sequentially, one by one)
2. Sends each file to `log_ingestion_service` via gRPC
3. Publishes normalized entries to RabbitMQ for anomaly detection
4. Waits for detection result on a reply queue for each file
5. Returns a per-file summary from `GET /test`
6. Writes gateway<->microservice call logs to Cassandra

## Endpoints

- `GET /health`
- `GET /openapi.json`
- `GET /test`
- `GET /logs`

## Run locally

```bash
python -m pip install -r requirements.txt
python run.py
```

## Tests

```bash
python -m unittest discover -s tests -p "test_*.py"
```
