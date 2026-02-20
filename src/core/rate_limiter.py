"""
Rate limiting system for Wingman AI.

Provides token bucket and sliding window rate limiting for API providers.
Inspired by OpenClaw's rate limiting architecture.
"""

from __future__ import annotations

import asyncio
import logging
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict

logger = logging.getLogger(__name__)


class RateLimitStrategy(str, Enum):
    """Rate limiting strategies."""
    TOKEN_BUCKET = "token_bucket"
    SLIDING_WINDOW = "sliding_window"
    FIXED_WINDOW = "fixed_window"


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting."""
    max_requests: int = 60  # Max requests per window
    window_seconds: int = 60  # Time window in seconds
    burst_size: int | None = None  # Max burst (token bucket only)
    strategy: RateLimitStrategy = RateLimitStrategy.TOKEN_BUCKET


@dataclass
class TokenBucket:
    """Token bucket for rate limiting."""
    capacity: int
    refill_rate: float  # Tokens per second
    tokens: float = field(init=False)
    last_refill: float = field(init=False)
    
    def __post_init__(self):
        self.tokens = float(self.capacity)
        self.last_refill = time.time()
    
    def _refill(self):
        """Refill tokens based on elapsed time."""
        now = time.time()
        elapsed = now - self.last_refill
        
        # Add tokens based on elapsed time
        self.tokens = min(
            self.capacity,
            self.tokens + (elapsed * self.refill_rate)
        )
        self.last_refill = now
    
    def consume(self, tokens: int = 1) -> bool:
        """
        Try to consume tokens.
        
        Returns:
            True if tokens available, False otherwise
        """
        self._refill()
        
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        
        return False
    
    def get_wait_time(self, tokens: int = 1) -> float:
        """Get time to wait before tokens available."""
        self._refill()
        
        if self.tokens >= tokens:
            return 0.0
        
        # Calculate wait time
        needed_tokens = tokens - self.tokens
        return needed_tokens / self.refill_rate


@dataclass
class SlidingWindow:
    """Sliding window for rate limiting."""
    max_requests: int
    window_seconds: int
    requests: deque = field(default_factory=deque)
    
    def _clean_old_requests(self):
        """Remove requests outside the time window."""
        now = time.time()
        cutoff = now - self.window_seconds
        
        # Remove old requests from left
        while self.requests and self.requests[0] < cutoff:
            self.requests.popleft()
    
    def can_proceed(self) -> bool:
        """Check if request can proceed."""
        self._clean_old_requests()
        return len(self.requests) < self.max_requests
    
    def record_request(self):
        """Record a new request."""
        self.requests.append(time.time())
    
    def get_wait_time(self) -> float:
        """Get time to wait before request can proceed."""
        self._clean_old_requests()
        
        if len(self.requests) < self.max_requests:
            return 0.0
        
        # Wait until oldest request expires
        oldest = self.requests[0]
        now = time.time()
        return (oldest + self.window_seconds) - now


class RateLimiter:
    """
    Rate limiter with multiple strategies.
    
    Supports per-provider, per-endpoint, and global rate limiting.
    """
    
    def __init__(self):
        self._buckets: Dict[str, TokenBucket] = {}
        self._windows: Dict[str, SlidingWindow] = {}
        self._configs: Dict[str, RateLimitConfig] = {}
        self._locks: Dict[str, asyncio.Lock] = defaultdict(asyncio.Lock)
    
    def configure(self, key: str, config: RateLimitConfig):
        """
        Configure rate limiting for a key.
        
        Args:
            key: Rate limit key (e.g., "openai", "openai:chat", "global")
            config: Rate limit configuration
        """
        self._configs[key] = config
        
        if config.strategy == RateLimitStrategy.TOKEN_BUCKET:
            burst_size = config.burst_size or config.max_requests
            refill_rate = burst_size / config.window_seconds
            
            self._buckets[key] = TokenBucket(
                capacity=burst_size,
                refill_rate=refill_rate,
            )
            logger.info(
                f"Configured token bucket for {key}: "
                f"{burst_size} tokens, {refill_rate:.2f} tokens/sec"
            )
        
        elif config.strategy in (RateLimitStrategy.SLIDING_WINDOW, RateLimitStrategy.FIXED_WINDOW):
            self._windows[key] = SlidingWindow(
                max_requests=config.max_requests,
                window_seconds=config.window_seconds,
            )
            logger.info(
                f"Configured sliding window for {key}: "
                f"{config.max_requests} requests per {config.window_seconds}s"
            )
    
    async def acquire(self, key: str, tokens: int = 1) -> None:
        """
        Acquire rate limit token(s), waiting if necessary.
        
        Args:
            key: Rate limit key
            tokens: Number of tokens to consume
        """
        if key not in self._configs:
            # No rate limit configured
            return
        
        config = self._configs[key]
        
        async with self._locks[key]:
            if config.strategy == RateLimitStrategy.TOKEN_BUCKET:
                await self._acquire_token_bucket(key, tokens)
            
            elif config.strategy == RateLimitStrategy.SLIDING_WINDOW:
                await self._acquire_sliding_window(key)
    
    async def _acquire_token_bucket(self, key: str, tokens: int):
        """Acquire tokens from token bucket."""
        bucket = self._buckets[key]
        
        while not bucket.consume(tokens):
            wait_time = bucket.get_wait_time(tokens)
            logger.debug(f"Rate limit for {key}: waiting {wait_time:.2f}s")
            await asyncio.sleep(wait_time)
    
    async def _acquire_sliding_window(self, key: str):
        """Acquire slot in sliding window."""
        window = self._windows[key]
        
        while not window.can_proceed():
            wait_time = window.get_wait_time()
            logger.debug(f"Rate limit for {key}: waiting {wait_time:.2f}s")
            await asyncio.sleep(wait_time)
        
        window.record_request()
    
    def get_stats(self, key: str) -> dict:
        """Get current rate limit statistics."""
        if key not in self._configs:
            return {"configured": False}
        
        config = self._configs[key]
        
        if config.strategy == RateLimitStrategy.TOKEN_BUCKET:
            bucket = self._buckets[key]
            bucket._refill()
            
            return {
                "configured": True,
                "strategy": "token_bucket",
                "available_tokens": bucket.tokens,
                "capacity": bucket.capacity,
                "refill_rate": bucket.refill_rate,
            }
        
        elif config.strategy == RateLimitStrategy.SLIDING_WINDOW:
            window = self._windows[key]
            window._clean_old_requests()
            
            return {
                "configured": True,
                "strategy": "sliding_window",
                "requests_in_window": len(window.requests),
                "max_requests": window.max_requests,
                "window_seconds": window.window_seconds,
            }
        
        return {"configured": False}


# Global rate limiter instance
_rate_limiter = RateLimiter()


def get_rate_limiter() -> RateLimiter:
    """Get global rate limiter instance."""
    return _rate_limiter


# Example usage
if __name__ == "__main__":
    async def main():
        limiter = get_rate_limiter()
        
        # Configure rate limits
        limiter.configure(
            "openai",
            RateLimitConfig(
                max_requests=60,
                window_seconds=60,
                burst_size=10,
                strategy=RateLimitStrategy.TOKEN_BUCKET,
            ),
        )
        
        limiter.configure(
            "gemini",
            RateLimitConfig(
                max_requests=15,
                window_seconds=60,
                strategy=RateLimitStrategy.SLIDING_WINDOW,
            ),
        )
        
        # Simulate API calls
        for i in range(20):
            await limiter.acquire("openai")
            print(f"Request {i+1}: {limiter.get_stats('openai')}")
            await asyncio.sleep(0.1)
    
    asyncio.run(main())
