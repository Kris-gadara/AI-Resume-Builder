"""
Production Monitoring & Metrics
=================================
Track AI model performance, API latency, and errors.
"""

import time
import logging
from functools import wraps
from prometheus_client import Counter, Histogram, Gauge
from typing import Callable

logger = logging.getLogger(__name__)

# Metrics
api_requests_total = Counter(
    'resume_api_requests_total',
    'Total API requests',
    ['endpoint', 'status']
)

api_latency_seconds = Histogram(
    'resume_api_latency_seconds',
    'API endpoint latency',
    ['endpoint'],
    buckets=[0.1, 0.5, 1.0, 2.5, 5.0, 10.0]
)

gemini_calls_total = Counter(
    'gemini_api_calls_total',
    'Total Gemini API calls',
    ['function', 'status']
)

gemini_latency_seconds = Histogram(
    'gemini_api_latency_seconds',
    'Gemini API response time',
    ['function'],
    buckets=[0.5, 1.0, 2.0, 5.0, 10.0, 30.0]
)

match_score_distribution = Histogram(
    'job_match_score_distribution',
    'Distribution of job match scores',
    buckets=[0, 20, 40, 60, 80, 100]
)

active_requests = Gauge(
    'active_requests',
    'Number of requests currently being processed'
)

pdf_generation_total = Counter(
    'pdf_generation_total',
    'Total PDF generations',
    ['status']
)

cache_hits_total = Counter(
    'cache_hits_total',
    'Total cache hits',
    ['cache_key']
)

cache_misses_total = Counter(
    'cache_misses_total',
    'Total cache misses',
    ['cache_key']
)


def track_api_call(endpoint: str):
    """Decorator to track API endpoint metrics."""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            active_requests.inc()
            start_time = time.time()
            status = 'success'
            
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                status = 'error'
                raise
            finally:
                duration = time.time() - start_time
                api_latency_seconds.labels(endpoint=endpoint).observe(duration)
                api_requests_total.labels(endpoint=endpoint, status=status).inc()
                active_requests.dec()
                
                logger.info(
                    f"API call to {endpoint} completed in {duration:.2f}s with status {status}"
                )
        
        return wrapper
    return decorator


def track_gemini_call(function_name: str):
    """Decorator to track Gemini API calls."""
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            status = 'success'
            
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                status = 'error'
                logger.error(f"Gemini call failed for {function_name}: {e}")
                raise
            finally:
                duration = time.time() - start_time
                gemini_latency_seconds.labels(function=function_name).observe(duration)
                gemini_calls_total.labels(function=function_name, status=status).inc()
        
        return wrapper
    return decorator


def record_match_score(score: float):
    """Record a job match score for distribution analysis."""
    match_score_distribution.observe(score)


def record_pdf_generation(status: str = 'success'):
    """Record a PDF generation event."""
    pdf_generation_total.labels(status=status).inc()


def record_cache_hit(cache_key: str):
    """Record a cache hit."""
    cache_hits_total.labels(cache_key=cache_key).inc()


def record_cache_miss(cache_key: str):
    """Record a cache miss."""
    cache_misses_total.labels(cache_key=cache_key).inc()
