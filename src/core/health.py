"""
Health monitoring system for Wingman AI.

Provides metrics collection, health checks, and system monitoring.
"""

from __future__ import annotations

import asyncio
import logging
import platform
import psutil
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List

logger = logging.getLogger(__name__)


class HealthStatus(str, Enum):
    """Health check status."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


@dataclass
class HealthCheck:
    """Health check result."""
    name: str
    status: HealthStatus
    message: str = ""
    latency_ms: float | None = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class Metric:
    """Performance metric."""
    name: str
    value: float
    unit: str = ""
    tags: Dict[str, str] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


class MetricsCollector:
    """
    Collect and aggregate performance metrics.
    
    Supports counters, gauges, histograms, and timers.
    """
    
    def __init__(self):
        self._counters: Dict[str, float] = defaultdict(float)
        self._gauges: Dict[str, float] = {}
        self._histograms: Dict[str, List[float]] = defaultdict(list)
        self._timers: Dict[str, List[float]] = defaultdict(list)
    
    def increment(self, name: str, value: float = 1.0, tags: Dict[str, str] | None = None):
        """Increment counter."""
        key = self._make_key(name, tags)
        self._counters[key] += value
    
    def gauge(self, name: str, value: float, tags: Dict[str, str] | None = None):
        """Set gauge value."""
        key = self._make_key(name, tags)
        self._gauges[key] = value
    
    def histogram(self, name: str, value: float, tags: Dict[str, str] | None = None):
        """Record histogram value."""
        key = self._make_key(name, tags)
        self._histograms[key].append(value)
        
        # Keep last 1000 values
        if len(self._histograms[key]) > 1000:
            self._histograms[key] = self._histograms[key][-1000:]
    
    def timing(self, name: str, duration_ms: float, tags: Dict[str, str] | None = None):
        """Record timing."""
        key = self._make_key(name, tags)
        self._timers[key].append(duration_ms)
        
        # Keep last 1000 values
        if len(self._timers[key]) > 1000:
            self._timers[key] = self._timers[key][-1000:]
    
    def _make_key(self, name: str, tags: Dict[str, str] | None) -> str:
        """Make metric key with tags."""
        if not tags:
            return name
        
        tag_str = ",".join(f"{k}={v}" for k, v in sorted(tags.items()))
        return f"{name}[{tag_str}]"
    
    def get_stats(self, name: str, tags: Dict[str, str] | None = None) -> dict:
        """Get statistics for metric."""
        key = self._make_key(name, tags)
        
        stats = {}
        
        if key in self._counters:
            stats["counter"] = self._counters[key]
        
        if key in self._gauges:
            stats["gauge"] = self._gauges[key]
        
        if key in self._histograms:
            values = self._histograms[key]
            stats["histogram"] = {
                "count": len(values),
                "min": min(values),
                "max": max(values),
                "avg": sum(values) / len(values),
                "p50": self._percentile(values, 0.5),
                "p95": self._percentile(values, 0.95),
                "p99": self._percentile(values, 0.99),
            }
        
        if key in self._timers:
            values = self._timers[key]
            stats["timing"] = {
                "count": len(values),
                "min_ms": min(values),
                "max_ms": max(values),
                "avg_ms": sum(values) / len(values),
                "p50_ms": self._percentile(values, 0.5),
                "p95_ms": self._percentile(values, 0.95),
                "p99_ms": self._percentile(values, 0.99),
            }
        
        return stats
    
    def _percentile(self, values: List[float], p: float) -> float:
        """Calculate percentile."""
        sorted_values = sorted(values)
        index = int(len(sorted_values) * p)
        return sorted_values[min(index, len(sorted_values) - 1)]
    
    def get_all_stats(self) -> dict:
        """Get all metrics statistics."""
        all_stats = {}
        
        for key in set(
            list(self._counters.keys()) +
            list(self._gauges.keys()) +
            list(self._histograms.keys()) +
            list(self._timers.keys())
        ):
            # Parse key to get name and tags
            if "[" in key:
                name = key.split("[")[0]
                tags_str = key.split("[")[1].rstrip("]")
                tags = dict(tag.split("=") for tag in tags_str.split(","))
            else:
                name = key
                tags = None
            
            all_stats[key] = self.get_stats(name, tags)
        
        return all_stats


class HealthMonitor:
    """
    System health monitoring.
    
    Runs periodic health checks and collects system metrics.
    """
    
    def __init__(self):
        self.metrics = MetricsCollector()
        self._health_checks: Dict[str, Callable[[], HealthCheck]] = {}
        self._running = False
        self._task = None
    
    def register_check(self, name: str, check_fn: Callable[[], HealthCheck]):
        """Register health check function."""
        self._health_checks[name] = check_fn
        logger.info(f"Registered health check: {name}")
    
    async def run_checks(self) -> Dict[str, HealthCheck]:
        """Run all health checks."""
        results = {}
        
        for name, check_fn in self._health_checks.items():
            try:
                start = time.time()
                result = await asyncio.get_event_loop().run_in_executor(
                    None,
                    check_fn,
                )
                latency_ms = (time.time() - start) * 1000
                result.latency_ms = latency_ms
                
                results[name] = result
                
                # Record metrics
                self.metrics.timing(
                    f"health_check.{name}.latency",
                    latency_ms,
                )
                self.metrics.increment(
                    f"health_check.{name}.status",
                    tags={"status": result.status.value},
                )
            
            except Exception as e:
                logger.error(f"Health check {name} failed: {e}")
                results[name] = HealthCheck(
                    name=name,
                    status=HealthStatus.UNHEALTHY,
                    message=f"Check failed: {e}",
                )
        
        return results
    
    def collect_system_metrics(self):
        """Collect system-level metrics."""
        # CPU
        cpu_percent = psutil.cpu_percent(interval=0.1)
        self.metrics.gauge("system.cpu.percent", cpu_percent)
        
        # Memory
        memory = psutil.virtual_memory()
        self.metrics.gauge("system.memory.percent", memory.percent)
        self.metrics.gauge("system.memory.used_mb", memory.used / 1024 / 1024)
        self.metrics.gauge("system.memory.available_mb", memory.available / 1024 / 1024)
        
        # Disk
        disk = psutil.disk_usage("/")
        self.metrics.gauge("system.disk.percent", disk.percent)
        self.metrics.gauge("system.disk.used_gb", disk.used / 1024 / 1024 / 1024)
        self.metrics.gauge("system.disk.free_gb", disk.free / 1024 / 1024 / 1024)
        
        # Process
        process = psutil.Process()
        self.metrics.gauge("process.memory.rss_mb", process.memory_info().rss / 1024 / 1024)
        self.metrics.gauge("process.cpu.percent", process.cpu_percent(interval=0.1))
        self.metrics.gauge("process.threads", process.num_threads())
    
    def start_monitoring(self, interval_seconds: int = 60):
        """Start background monitoring."""
        if self._running:
            logger.warning("Health monitoring already running")
            return
        
        self._running = True
        self._task = asyncio.create_task(self._monitor_loop(interval_seconds))
        logger.info(f"Started health monitoring (interval: {interval_seconds}s)")
    
    async def _monitor_loop(self, interval_seconds: int):
        """Background monitoring loop."""
        while self._running:
            try:
                # Collect system metrics
                await asyncio.get_event_loop().run_in_executor(
                    None,
                    self.collect_system_metrics,
                )
                
                # Run health checks
                await self.run_checks()
                
                await asyncio.sleep(interval_seconds)
            
            except Exception as e:
                logger.error(f"Health monitoring error: {e}")
                await asyncio.sleep(interval_seconds)
    
    def stop_monitoring(self):
        """Stop background monitoring."""
        self._running = False
        if self._task:
            self._task.cancel()
            self._task = None
        logger.info("Stopped health monitoring")
    
    def get_health_status(self) -> dict:
        """Get overall health status."""
        system_info = {
            "platform": platform.system(),
            "python_version": platform.python_version(),
            "cpu_count": psutil.cpu_count(),
        }
        
        # Get latest metrics
        metrics = self.metrics.get_all_stats()
        
        return {
            "status": "healthy",  # Can be computed from checks
            "system": system_info,
            "metrics": metrics,
        }


# Global health monitor
_health_monitor = HealthMonitor()


def get_health_monitor() -> HealthMonitor:
    """Get global health monitor instance."""
    return _health_monitor


# Example health checks
def check_memory() -> HealthCheck:
    """Check memory usage."""
    memory = psutil.virtual_memory()
    
    if memory.percent > 90:
        return HealthCheck(
            name="memory",
            status=HealthStatus.UNHEALTHY,
            message=f"Memory usage critical: {memory.percent}%",
            metadata={"percent": memory.percent},
        )
    elif memory.percent > 75:
        return HealthCheck(
            name="memory",
            status=HealthStatus.DEGRADED,
            message=f"Memory usage high: {memory.percent}%",
            metadata={"percent": memory.percent},
        )
    else:
        return HealthCheck(
            name="memory",
            status=HealthStatus.HEALTHY,
            message=f"Memory usage normal: {memory.percent}%",
            metadata={"percent": memory.percent},
        )


def check_disk() -> HealthCheck:
    """Check disk usage."""
    disk = psutil.disk_usage("/")
    
    if disk.percent > 95:
        return HealthCheck(
            name="disk",
            status=HealthStatus.UNHEALTHY,
            message=f"Disk usage critical: {disk.percent}%",
            metadata={"percent": disk.percent},
        )
    elif disk.percent > 85:
        return HealthCheck(
            name="disk",
            status=HealthStatus.DEGRADED,
            message=f"Disk usage high: {disk.percent}%",
            metadata={"percent": disk.percent},
        )
    else:
        return HealthCheck(
            name="disk",
            status=HealthStatus.HEALTHY,
            message=f"Disk usage normal: {disk.percent}%",
            metadata={"percent": disk.percent},
        )


# Example usage
if __name__ == "__main__":
    import json
    
    async def main():
        monitor = get_health_monitor()
        
        # Register health checks
        monitor.register_check("memory", check_memory)
        monitor.register_check("disk", check_disk)
        
        # Run checks
        results = await monitor.run_checks()
        for name, result in results.items():
            print(f"{name}: {result.status.value} - {result.message}")
        
        # Collect metrics
        monitor.collect_system_metrics()
        
        # Get stats
        print("\nSystem metrics:")
        print(json.dumps(monitor.get_health_status(), indent=2, default=str))
    
    asyncio.run(main())
