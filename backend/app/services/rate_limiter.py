import time
from collections import defaultdict
from typing import Optional
from fastapi import Request, HTTPException, status

class SlidingWindowRateLimiter:
    """
    In-memory sliding-window rate limiter per client IP address.
    Protects public/anonymous endpoints from automated abuse and flooding
    while preserving legitimate community contributions.
    """
    def __init__(self, requests_per_minute: int = 10, window_seconds: int = 60):
        self.requests_per_minute = requests_per_minute
        self.window_seconds = window_seconds
        self.history = defaultdict(list)

    def check(self, request: Optional[Request], endpoint_key: str = "general") -> None:
        client_ip = "127.0.0.1"
        if request:
            forwarded = request.headers.get("x-forwarded-for")
            if forwarded:
                client_ip = forwarded.split(",")[0].strip()
            elif request.client and request.client.host:
                client_ip = request.client.host

        key = f"{endpoint_key}:{client_ip}"
        now = time.time()
        cutoff = now - self.window_seconds

        # Prune timestamps older than window
        self.history[key] = [t for t in self.history[key] if t > cutoff]

        if len(self.history[key]) >= self.requests_per_minute:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded: maximum {self.requests_per_minute} submissions per minute. Please try again later."
            )

        self.history[key].append(now)

    def reset(self) -> None:
        """Reset history (useful during testing)."""
        self.history.clear()

rate_limiter = SlidingWindowRateLimiter(requests_per_minute=10, window_seconds=60)

