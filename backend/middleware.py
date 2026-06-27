import time
from collections import defaultdict

from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Sliding-window per-IP rate limiter.
    Reads X-Real-IP (set by Caddy) so limits are per real client, not per proxy.
    Internal Selenium endpoints and CORS preflight are exempt.
    """

    _RULES: dict[tuple[str, str], tuple[int, int]] = {
        ("POST", "/releases"):             (5,  3600),  # 5 uploads / hour
        ("POST", "/transactions/receipt"): (5,  3600),  # 5 receipts / hour
        ("POST", "/users/me/language"):    (20, 60),    # 20 changes / min
    }
    _DEFAULT = (60, 60)  # 60 req / min for everything else

    def __init__(self, app):
        super().__init__(app)
        self._store: dict[tuple, list[float]] = defaultdict(list)

    def _client_ip(self, request) -> str:
        real = request.headers.get("X-Real-IP")
        if real:
            return real
        fwd = request.headers.get("X-Forwarded-For", "")
        if fwd:
            return fwd.split(",")[0].strip()
        return getattr(request.client, "host", "unknown")

    async def dispatch(self, request, call_next):
        if request.method == "OPTIONS" or request.url.path.startswith("/internal/"):
            return await call_next(request)

        ip = self._client_ip(request)
        limit, window = self._RULES.get(
            (request.method, request.url.path), self._DEFAULT
        )
        key = (ip, request.method, request.url.path)
        now = time.monotonic()

        self._store[key] = [t for t in self._store[key] if now - t < window]

        if len(self._store[key]) >= limit:
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many requests. Please slow down."},
                headers={"Retry-After": str(window)},
            )

        self._store[key].append(now)
        return await call_next(request)
