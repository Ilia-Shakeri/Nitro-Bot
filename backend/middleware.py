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

    _SWEEP_EVERY = 300  # seconds between full prunes of drained buckets

    def __init__(self, app):
        super().__init__(app)
        self._store: dict[tuple, list[float]] = defaultdict(list)
        self._last_sweep = 0.0

    def _sweep(self, now: float) -> None:
        """Drop buckets whose timestamps have all aged out, so the store does not
        grow unbounded with one-off client IPs."""
        if now - self._last_sweep < self._SWEEP_EVERY:
            return
        self._last_sweep = now
        for k in list(self._store.keys()):
            _, _, path = k
            _, window = self._RULES.get((k[1], path), self._DEFAULT)
            if all(now - t >= window for t in self._store[k]):
                del self._store[k]

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
        self._sweep(now)

        recent = [t for t in self._store[key] if now - t < window]

        if len(recent) >= limit:
            self._store[key] = recent
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many requests. Please slow down."},
                headers={"Retry-After": str(window)},
            )

        recent.append(now)
        self._store[key] = recent
        return await call_next(request)
