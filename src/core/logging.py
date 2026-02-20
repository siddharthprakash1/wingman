"""
Advanced logging system for Wingman AI.

Provides structured logging with log aggregation, search, and analysis.
"""

from __future__ import annotations

import json
import logging
import logging.handlers
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from rich.console import Console
from rich.logging import RichHandler


class StructuredFormatter(logging.Formatter):
    """JSON structured log formatter."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data: Dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields
        if hasattr(record, "extra_fields"):
            log_data.update(record.extra_fields)
        
        # Add context fields
        for attr in ["session_id", "user_id", "request_id", "provider", "tool"]:
            if hasattr(record, attr):
                log_data[attr] = getattr(record, attr)
        
        return json.dumps(log_data)


class StructuredLogger:
    """
    Structured logger with context management.
    
    Supports log aggregation to files and search/analysis capabilities.
    """
    
    def __init__(
        self,
        name: str,
        log_dir: Path | None = None,
        console_output: bool = True,
        file_output: bool = True,
        json_output: bool = True,
    ):
        """
        Initialize structured logger.
        
        Args:
            name: Logger name
            log_dir: Directory for log files (default: ~/.wingman/logs)
            console_output: Enable console logging with Rich
            file_output: Enable file logging (human-readable)
            json_output: Enable JSON structured logging
        """
        self.name = name
        self.log_dir = log_dir or (Path.home() / ".wingman" / "logs")
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Get logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        self.logger.propagate = False
        
        # Remove existing handlers
        self.logger.handlers.clear()
        
        # Console handler with Rich
        if console_output:
            console_handler = RichHandler(
                console=Console(stderr=True),
                show_time=True,
                show_path=False,
                rich_tracebacks=True,
            )
            console_handler.setLevel(logging.INFO)
            self.logger.addHandler(console_handler)
        
        # File handler (human-readable)
        if file_output:
            file_handler = logging.handlers.RotatingFileHandler(
                self.log_dir / f"{name}.log",
                maxBytes=10 * 1024 * 1024,  # 10MB
                backupCount=5,
            )
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(
                logging.Formatter(
                    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
                )
            )
            self.logger.addHandler(file_handler)
        
        # JSON handler (structured)
        if json_output:
            json_handler = logging.handlers.RotatingFileHandler(
                self.log_dir / f"{name}.jsonl",
                maxBytes=10 * 1024 * 1024,  # 10MB
                backupCount=5,
            )
            json_handler.setLevel(logging.DEBUG)
            json_handler.setFormatter(StructuredFormatter())
            self.logger.addHandler(json_handler)
    
    def debug(self, message: str, **kwargs):
        """Log debug message with context."""
        extra = {"extra_fields": kwargs} if kwargs else {}
        self.logger.debug(message, extra=extra)
    
    def info(self, message: str, **kwargs):
        """Log info message with context."""
        extra = {"extra_fields": kwargs} if kwargs else {}
        self.logger.info(message, extra=extra)
    
    def warning(self, message: str, **kwargs):
        """Log warning message with context."""
        extra = {"extra_fields": kwargs} if kwargs else {}
        self.logger.warning(message, extra=extra)
    
    def error(self, message: str, **kwargs):
        """Log error message with context."""
        extra = {"extra_fields": kwargs} if kwargs else {}
        self.logger.error(message, extra=extra)
    
    def critical(self, message: str, **kwargs):
        """Log critical message with context."""
        extra = {"extra_fields": kwargs} if kwargs else {}
        self.logger.critical(message, extra=extra)
    
    def search_logs(
        self,
        query: str | None = None,
        level: str | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        limit: int = 100,
    ) -> list[dict]:
        """
        Search structured logs.
        
        Args:
            query: Text search in message
            level: Filter by log level
            start_time: Filter by start time
            end_time: Filter by end time
            limit: Maximum results
        
        Returns:
            List of matching log entries
        """
        results = []
        jsonl_path = self.log_dir / f"{self.name}.jsonl"
        
        if not jsonl_path.exists():
            return results
        
        with open(jsonl_path, "r") as f:
            for line in f:
                if not line.strip():
                    continue
                
                try:
                    log_entry = json.loads(line)
                    
                    # Apply filters
                    if level and log_entry.get("level") != level:
                        continue
                    
                    if query and query.lower() not in log_entry.get("message", "").lower():
                        continue
                    
                    if start_time:
                        entry_time = datetime.fromisoformat(log_entry["timestamp"])
                        if entry_time < start_time:
                            continue
                    
                    if end_time:
                        entry_time = datetime.fromisoformat(log_entry["timestamp"])
                        if entry_time > end_time:
                            continue
                    
                    results.append(log_entry)
                    
                    if len(results) >= limit:
                        break
                
                except Exception as e:
                    logging.error(f"Failed to parse log line: {e}")
        
        return results
    
    def get_stats(self) -> dict:
        """Get logging statistics."""
        stats = {
            "log_dir": str(self.log_dir),
            "logger_name": self.name,
            "handlers": len(self.logger.handlers),
        }
        
        # Get file sizes
        for handler in self.logger.handlers:
            if isinstance(handler, logging.handlers.RotatingFileHandler):
                log_file = Path(handler.baseFilename)
                if log_file.exists():
                    stats[f"{log_file.name}_size"] = log_file.stat().st_size
        
        return stats


# Example usage
if __name__ == "__main__":
    logger = StructuredLogger("test")
    
    logger.info("Application started", version="0.1.0", environment="production")
    logger.debug("Processing request", session_id="abc123", user_id="user456")
    logger.warning("High memory usage", memory_mb=1024, threshold_mb=512)
    logger.error("API call failed", provider="openai", error_code=429)
    
    # Search logs
    print("\nSearching logs for 'failed':")
    results = logger.search_logs(query="failed", limit=10)
    for result in results:
        print(json.dumps(result, indent=2))
    
    # Get stats
    print("\nLogger stats:")
    print(json.dumps(logger.get_stats(), indent=2))
