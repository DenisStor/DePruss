"""
In-memory rate limiter for login attempts.
5 attempts per 15 minutes per IP address.
"""
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import threading


class RateLimiter:
    """Simple in-memory rate limiter with sliding window."""

    def __init__(self, max_attempts: int = 5, window_minutes: int = 15):
        self.max_attempts = max_attempts
        self.window = timedelta(minutes=window_minutes)
        self._attempts: Dict[str, List[datetime]] = defaultdict(list)
        self._lock = threading.Lock()

    def _cleanup_old_attempts(self, key: str) -> None:
        """Remove attempts older than the window."""
        cutoff = datetime.utcnow() - self.window
        self._attempts[key] = [
            ts for ts in self._attempts[key]
            if ts > cutoff
        ]

    def is_rate_limited(self, key: str) -> Tuple[bool, int]:
        """
        Check if a key is rate limited.

        Returns:
            Tuple[is_limited, remaining_attempts]
        """
        with self._lock:
            self._cleanup_old_attempts(key)
            current_attempts = len(self._attempts[key])
            remaining = max(0, self.max_attempts - current_attempts)
            return current_attempts >= self.max_attempts, remaining

    def record_attempt(self, key: str) -> Tuple[bool, int]:
        """
        Record an attempt and check if rate limited.

        Returns:
            Tuple[is_limited, remaining_attempts]
        """
        with self._lock:
            self._cleanup_old_attempts(key)

            if len(self._attempts[key]) >= self.max_attempts:
                return True, 0

            self._attempts[key].append(datetime.utcnow())
            remaining = self.max_attempts - len(self._attempts[key])
            return False, remaining

    def reset(self, key: str) -> None:
        """Reset attempts for a key (e.g., after successful login)."""
        with self._lock:
            self._attempts.pop(key, None)

    def get_retry_after(self, key: str) -> int:
        """Get seconds until oldest attempt expires."""
        with self._lock:
            if not self._attempts.get(key):
                return 0

            oldest = min(self._attempts[key])
            expires_at = oldest + self.window
            remaining = (expires_at - datetime.utcnow()).total_seconds()
            return max(0, int(remaining))


# Global instance for login rate limiting
login_limiter = RateLimiter(max_attempts=5, window_minutes=15)
