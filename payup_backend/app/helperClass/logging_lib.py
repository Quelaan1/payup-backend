import os
import logging
import time
import json
from typing import Callable
from uuid import uuid4
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from fastapi.responses import StreamingResponse
from ..config.constants import get_settings

config = get_settings()

ignore_endpoints = ["docs", "openapi.json"]


class LoggingMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp, logger: logging.Logger) -> None:
        super().__init__(app)
        self.logger = logger

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        endpoints = str(request.url).split("/")
        if any(key in endpoints for key in ignore_endpoints):
            return await call_next(request)

        request_id = str(uuid4())
        start_time = time.perf_counter()

        # Read and cache the request body for logging
        if (
            config.ENV == "local"
            and request.headers.get("Content-Type") == "application/json"
        ):
            body_bytes = await request.body()
            request.state.body = body_bytes.decode("utf-8")

        response = await call_next(request)
        response.headers["X-API-Request-ID"] = request_id

        finish_time = time.perf_counter()
        response_time = finish_time - start_time

        # Log request and response details
        self.log_request(request, request_id)
        self.log_response(response, response_time, request_id)

        return response

    def log_request(self, request: Request, request_id: str) -> None:
        request_info = {
            "X-API-Request-ID": request_id,
            "method": request.method,
            "url": str(request.url),
            "ip": request.client.host,
        }

        # Log the cached request body if available
        if hasattr(request.state, "body"):
            log_message = f"[Request Body]: {request.state.body}"
            self.logger.info(log_message)

        self.logger.info(f"Request: {json.dumps(request_info)}")

    def log_response(
        self, response: Response, response_time: float, request_id: str
    ) -> None:
        response_info = {
            "X-API-Request-ID": request_id,
            "status_code": response.status_code,
            "response_time": f"{response_time:.4f}s",
        }
        if isinstance(response, StreamingResponse):
            # For streaming responses, skip logging the body
            self.logger.info(f"Response (Streaming): {json.dumps(response_info)}")
        else:
            # For non-streaming responses, you can attempt to log the body
            # Be cautious with large responses and consider truncating or summarizing
            self.logger.info(f"Response: {json.dumps(response_info)}")
