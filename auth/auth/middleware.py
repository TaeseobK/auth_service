from time import time
from prometheus_client import Counter, Histogram

REQUEST_COUNT = Counter('request_count', 'Total request count', ['method', 'endpoint'])
REQUEST_DURATION = Histogram('request_duration_seconds', 'Request duration in seconds', ['method', 'endpoint'])

class PrometheusMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Start timing the request
        start_time = time()

        # Process the request
        response = self.get_response(request)

        # Record metrics
        REQUEST_COUNT.labels(method=request.method, endpoint=request.path).inc()
        REQUEST_DURATION.labels(method=request.method, endpoint=request.path).observe(time() - start_time)

        return response