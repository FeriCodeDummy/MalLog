# Log Ingestion Service

Python FastAPI microservice with a gRPC upload endpoint for `.log` ingestion.

## gRPC Endpoint

Method:

- `UploadLog(stream LogChunk) returns (UploadResponse)`

Proto contract is stored in:

- `contracts/log_ingestion.proto`

## Supported Log Types

The service now detects and normalizes these log families:

1. `iis_header` (`#Fields: ...`)
2. `nginx_error`
3. `haproxy`
4. `tomcat_catalina`
5. `http_access_common`
6. `iis_w3c_line_fallback`

Detection uses strict regex patterns in `services/log_parser.py`.

If any line breaks these rules, the response returns `success=false`.

## Normalized JSON Shape

`normalized_logs_json` contains:

```json
{
  "log_type": "nginx_error",
  "entry_count": 1,
  "entries": [
    {
      "log_type": "nginx_error",
      "raw_line": "...",
      "message": "...",
      "timestamp": "2026-03-30T14:22:05",
      "severity": "error",
      "parsed_fields": {
        "worker": "1234#1234"
      }
    }
  ]
}
```

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
- `LOG_INGESTION_GRPC_MAX_MESSAGE_BYTES` (default: `1073741824`)
- `LOG_INGESTION_MAX_UPLOAD_BYTES` (default: `1073741824`)

## Tests

```bash
python -m unittest discover -s tests -p "test_*.py"
```

## Example gRPC Client

```bash
python scripts/upload_log_client.py --file "c:\path\to\your.log" --target 127.0.0.1:50051 --timeout-seconds 10
```
