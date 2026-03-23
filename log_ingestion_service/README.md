# Log Ingestion Service

Python FastAPI microservice with a gRPC upload endpoint for `.log` ingestion.

## gRPC Endpoint

Method:

- `UploadLog(stream LogChunk) returns (UploadResponse)`

Proto contract is stored in:

- `contracts/log_ingestion.proto`

## Supported Input Formats

Every line in the uploaded `.log` must follow exactly one of these formats
(all lines must use the same one):

1. `[TYPE] TIMESTAMP message`
2. `TIMESTAMP [TYPE] message`
3. `[TYPE] (TIMESTAMP) message`
4. `<TIMESTAMP> (TYPE) message`
5. `TIMESTAMP (TYPE) message`
6. `TYPE <TIMESTAMP> message`

Rules:

- `TIMESTAMP` must be `[MM/DD/YYYY hh:mm:ss]`
- `TYPE` must be one of `INFO`, `ERROR`, `WARN`
- `message` must be single-line and must not contain `;`

If any line breaks these rules, the response returns `success=false`.

## Run

Install dependencies:

```bash
pip install -r requirements.txt
```

Start service:

```bash
python run.py
```

FastAPI health check:

- `GET /health` on `http://localhost:8001/health`

gRPC endpoint:

- `0.0.0.0:50051` (default)

## Environment Variables

- `LOG_INGESTION_HTTP_HOST` (default: `0.0.0.0`)
- `LOG_INGESTION_HTTP_PORT` (default: `8001`)
- `LOG_INGESTION_GRPC_HOST` (default: `0.0.0.0`)
- `LOG_INGESTION_GRPC_PORT` (default: `50051`)
- `LOG_INGESTION_MAX_UPLOAD_BYTES` (default: `10485760`)

## Tests

```bash
python -m unittest discover -s tests -p "test_*.py"
```

## Example gRPC Client

```bash
python scripts/upload_log_client.py --file "c:\path\to\your.log" --target 127.0.0.1:50051 --timeout-seconds 10
```
