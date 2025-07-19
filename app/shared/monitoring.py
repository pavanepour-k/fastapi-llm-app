"""
Monitoring and observability setup
Reference: https://opentelemetry.io/docs/instrumentation/python/
"""

import logging
import time
from typing import Dict, Any, Optional
from contextlib import asynccontextmanager
from datetime import datetime

import structlog
from prometheus_client import Counter, Histogram, Gauge, start_http_server
from opentelemetry import trace, metrics
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor

from app.shared.config import settings

# Prometheus metrics
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status_code']
)

REQUEST_DURATION = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint']
)

ACTIVE_CONNECTIONS = Gauge(
    'websocket_active_connections',
    'Number of active WebSocket connections'
)

LLM_REQUEST_COUNT = Counter(
    'llm_requests_total',
    'Total LLM requests',
    ['model', 'status']
)

LLM_REQUEST_DURATION = Histogram(
    'llm_request_duration_seconds',
    'LLM request duration in seconds',
    ['model']
)

VECTOR_STORE_OPERATIONS = Counter(
    'vector_store_operations_total',
    'Total vector store operations',
    ['operation', 'status']
)


class MonitoringManager:
    """
    Centralized monitoring and observability manager.
    
    Single Responsibility: Monitoring infrastructure management
    """
    
    def __init__(self):
        self.setup_logging()
        self.setup_tracing()
        self.setup_metrics()
    
    def setup_logging(self):
        """Configure structured logging."""
        structlog.configure(
            processors=[
                structlog.stdlib.filter_by_level,
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
                structlog.stdlib.PositionalArgumentsFormatter(),
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.processors.UnicodeDecoder(),
                structlog.processors.JSONRenderer()
            ],
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )
    
    def setup_tracing(self):
        """Configure distributed tracing."""
        if settings.environment == "production":
            trace.set_tracer_provider(TracerProvider())
            
            jaeger_exporter = JaegerExporter(
                agent_host_name="jaeger",
                agent_port=6831,
            )
            
            span_processor = BatchSpanProcessor(jaeger_exporter)
            trace.get_tracer_provider().add_span_processor(span_processor)
    
    def setup_metrics(self):
        """Start Prometheus metrics server."""
        if settings.environment == "production":
            start_http_server(9090)
    
    def instrument_fastapi(self, app):
        """Instrument FastAPI application."""
        FastAPIInstrumentor.instrument_app(app)
        HTTPXClientInstrumentor().instrument()


class PerformanceMonitor:
    """
    Performance monitoring utilities.
    
    Single Responsibility: Performance measurement and tracking
    """
    
    @staticmethod
    @asynccontextmanager
    async def monitor_request(method: str, endpoint: str):
        """Monitor HTTP request performance."""
        start_time = time.time()
        status_code = "500"  # Default to error
        
        try:
            yield
            status_code = "200"  # Success
        except Exception as e:
            status_code = "500"
            raise
        finally:
            duration = time.time() - start_time
            
            REQUEST_COUNT.labels(
                method=method,
                endpoint=endpoint,
                status_code=status_code
            ).inc()
            
            REQUEST_DURATION.labels(
                method=method,
                endpoint=endpoint
            ).observe(duration)
    
    @staticmethod
    @asynccontextmanager
    async def monitor_llm_request(model: str):
        """Monitor LLM request performance."""
        start_time = time.time()
        status = "error"
        
        try:
            yield
            status = "success"
        except Exception as e:
            status = "error"
            raise
        finally:
            duration = time.time() - start_time
            
            LLM_REQUEST_COUNT.labels(
                model=model,
                status=status
            ).inc()
            
            LLM_REQUEST_DURATION.labels(
                model=model
            ).observe(duration)
    
    @staticmethod
    def track_vector_operation(operation: str, status: str = "success"):
        """Track vector store operations."""
        VECTOR_STORE_OPERATIONS.labels(
            operation=operation,
            status=status
        ).inc()
    
    @staticmethod
    def update_active_connections(count: int):
        """Update active WebSocket connections count."""
        ACTIVE_CONNECTIONS.set(count)


class ApplicationLogger:
    """
    Application-specific logging utilities.
    
    Single Responsibility: Application logging management
    """
    
    def __init__(self):
        self.logger = structlog.get_logger(__name__)
    
    def log_user_action(self, user_id: str, action: str, details: Dict[str, Any] = None):
        """Log user actions for audit trail."""
        self.logger.info(
            "User action",
            user_id=user_id,
            action=action,
            details=details or {},
            timestamp=datetime.utcnow().isoformat()
        )
    
    def log_llm_interaction(
        self,
        user_id: str,
        model: str,
        prompt_length: int,
        response_length: int,
        duration: float,
        success: bool
    ):
        """Log LLM interactions for analysis."""
        self.logger.info(
            "LLM interaction",
            user_id=user_id,
            model=model,
            prompt_length=prompt_length,
            response_length=response_length,
            duration=duration,
            success=success,
            timestamp=datetime.utcnow().isoformat()
        )
    
    def log_document_upload(
        self,
        user_id: str,
        filename: str,
        file_size: int,
        chunks_created: int,
        success: bool
    ):
        """Log document upload events."""
        self.logger.info(
            "Document upload",
            user_id=user_id,
            filename=filename,
            file_size=file_size,
            chunks_created=chunks_created,
            success=success,
            timestamp=datetime.utcnow().isoformat()
        )
    
    def log_security_event(
        self,
        event_type: str,
        user_id: Optional[str],
        ip_address: str,
        details: Dict[str, Any] = None
    ):
        """Log security-related events."""
        self.logger.warning(
            "Security event",
            event_type=event_type,
            user_id=user_id,
            ip_address=ip_address,
            details=details or {},
            timestamp=datetime.utcnow().isoformat()
        )


# Global instances
monitoring_manager = MonitoringManager()
performance_monitor = PerformanceMonitor()
app_logger = ApplicationLogger()
