from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import settings
from services.grpc_service import GrpcServerManager

grpc_server = GrpcServerManager(
    host=settings.grpc_host,
    port=settings.grpc_port,
    max_upload_bytes=settings.max_upload_bytes,
)


@asynccontextmanager
async def lifespan(_: FastAPI):
    await grpc_server.start()
    try:
        yield
    finally:
        await grpc_server.stop()


app = FastAPI(
    title="Log Ingestion Service",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/health")
async def health() -> dict[str, str]:
    return {
        "status": "ok",
        "grpc_endpoint": f"{settings.grpc_host}:{settings.grpc_port}",
    }
