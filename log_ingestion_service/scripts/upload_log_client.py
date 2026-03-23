import argparse
import asyncio
from pathlib import Path
import sys

import grpc

# Make sibling packages (e.g., contracts/) importable when this file is executed
# directly via `python scripts/upload_log_client.py`.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from contracts import log_ingestion_pb2, log_ingestion_pb2_grpc


async def upload_log(
    file_path: str,
    grpc_target: str,
    chunk_size: int,
    timeout_seconds: float,
) -> None:
    payload = Path(file_path).read_bytes()

    async def request_iterator():
        for index in range(0, len(payload), chunk_size):
            yield log_ingestion_pb2.LogChunk(content=payload[index : index + chunk_size])

    try:
        async with grpc.aio.insecure_channel(grpc_target) as channel:
            await asyncio.wait_for(channel.channel_ready(), timeout=timeout_seconds)
            stub = log_ingestion_pb2_grpc.LogIngestionServiceStub(channel)
            response = await asyncio.wait_for(
                stub.UploadLog(request_iterator()), timeout=timeout_seconds
            )
    except TimeoutError as exc:
        raise RuntimeError(
            f"Timed out after {timeout_seconds}s waiting for gRPC server at {grpc_target}."
        ) from exc
    except grpc.aio.AioRpcError as exc:
        raise RuntimeError(
            f"gRPC request failed with code={exc.code().name}: {exc.details()}"
        ) from exc

    print(f"success={response.success}")
    print(f"message={response.message}")
    print(f"detected_format={response.detected_format}")
    print(f"entry_count={response.entry_count}")
    if response.normalized_logs_json:
        print(response.normalized_logs_json)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Upload a .log file to LogIngestionService via gRPC."
    )
    parser.add_argument("--file", required=True, help="Path to local .log file")
    parser.add_argument(
        "--target",
        default="127.0.0.1:50051",
        help="gRPC target host:port (default: 127.0.0.1:50051)",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=4096,
        help="Upload chunk size in bytes (default: 4096)",
    )
    parser.add_argument(
        "--timeout-seconds",
        type=float,
        default=10.0,
        help="Timeout for connecting and request execution (default: 10s)",
    )

    args = parser.parse_args()
    try:
        asyncio.run(
            upload_log(
                file_path=args.file,
                grpc_target=args.target,
                chunk_size=args.chunk_size,
                timeout_seconds=args.timeout_seconds,
            )
        )
    except Exception as exc:
        print(f"error={exc}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
