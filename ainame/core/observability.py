import logging
import time
import uuid
from collections import defaultdict
from threading import Lock
from typing import Any

from fastapi import Request
from starlette.responses import Response

import settings


logger = logging.getLogger("ainame.api")
metrics_logger = logging.getLogger("ainame.metrics")

_lock = Lock()
_metrics: dict[str, Any] = {
    "total_requests": 0,
    "total_errors": 0,
    "total_latency_ms": 0.0,
    "max_latency_ms": 0.0,
    "by_route": defaultdict(
        lambda: {
            "count": 0,
            "errors": 0,
            "total_latency_ms": 0.0,
            "max_latency_ms": 0.0,
            "status_codes": defaultdict(int),
        }
    ),
}


def setup_logging() -> None:
    logging.basicConfig(
        level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )


def _route_key(request: Request) -> str:
    route = request.scope.get("route")
    path = getattr(route, "path", request.url.path)
    return f"{request.method} {path}"


def record_request(route_key: str, status_code: int, latency_ms: float) -> None:
    is_error = status_code >= 500
    with _lock:
        _metrics["total_requests"] += 1
        _metrics["total_latency_ms"] += latency_ms
        _metrics["max_latency_ms"] = max(_metrics["max_latency_ms"], latency_ms)
        if is_error:
            _metrics["total_errors"] += 1

        route_metrics = _metrics["by_route"][route_key]
        route_metrics["count"] += 1
        route_metrics["total_latency_ms"] += latency_ms
        route_metrics["max_latency_ms"] = max(route_metrics["max_latency_ms"], latency_ms)
        route_metrics["status_codes"][status_code] += 1
        if is_error:
            route_metrics["errors"] += 1


def get_metrics_snapshot() -> dict[str, Any]:
    with _lock:
        total_requests = _metrics["total_requests"]
        total_latency_ms = _metrics["total_latency_ms"]
        routes = {}
        for route_key, item in _metrics["by_route"].items():
            count = item["count"]
            routes[route_key] = {
                "count": count,
                "errors": item["errors"],
                "avg_latency_ms": round(item["total_latency_ms"] / count, 2) if count else 0,
                "max_latency_ms": round(item["max_latency_ms"], 2),
                "status_codes": {str(code): value for code, value in item["status_codes"].items()},
            }

        return {
            "total_requests": total_requests,
            "total_errors": _metrics["total_errors"],
            "avg_latency_ms": round(total_latency_ms / total_requests, 2) if total_requests else 0,
            "max_latency_ms": round(_metrics["max_latency_ms"], 2),
            "routes": routes,
        }


async def request_logging_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    request.state.request_id = request_id
    started_at = time.perf_counter()
    status_code = 500

    try:
        response: Response = await call_next(request)
        status_code = response.status_code
        return response
    except Exception:
        latency_ms = (time.perf_counter() - started_at) * 1000
        route_key = _route_key(request)
        record_request(route_key, status_code, latency_ms)
        logger.exception(
            "request_failed request_id=%s method=%s path=%s latency_ms=%.2f",
            request_id,
            request.method,
            request.url.path,
            latency_ms,
        )
        raise
    finally:
        latency_ms = (time.perf_counter() - started_at) * 1000
        route_key = _route_key(request)
        if "response" in locals():
            response.headers["X-Request-ID"] = request_id
            record_request(route_key, status_code, latency_ms)
            log = metrics_logger.warning if latency_ms >= settings.REQUEST_SLOW_MS else metrics_logger.info
            log(
                "request_completed request_id=%s method=%s path=%s status=%s latency_ms=%.2f",
                request_id,
                request.method,
                request.url.path,
                status_code,
                latency_ms,
            )
