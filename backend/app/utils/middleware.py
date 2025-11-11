from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from app.services.audit_service import AuditService
from app.utils.database import AsyncSessionLocal
from app.utils.logger import logger
import time
import json


class AuditMiddleware(BaseHTTPMiddleware):
    """Middleware to log all API requests for audit trail"""

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        # Extract request info
        method = request.method
        endpoint = str(request.url.path)
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")

        # Read request body (for audit logging)
        request_body = None
        if method in ["POST", "PUT", "PATCH"]:
            try:
                body = await request.body()
                if body:
                    request_body = json.loads(body.decode())
                # Reset the request body for downstream processing
                async def receive():
                    return {"type": "http.request", "body": body}
                request._receive = receive
            except:
                pass

        # Process request
        response = await call_next(request)

        # Calculate processing time
        process_time = time.time() - start_time

        # Log to audit trail (async, don't block response)
        if not endpoint.startswith("/ws"):  # Skip websocket endpoints
            try:
                async with AsyncSessionLocal() as db:
                    # Extract resource type and action from endpoint
                    parts = endpoint.split("/")
                    resource_type = parts[2] if len(parts) > 2 else "unknown"
                    action = f"{method.lower()}_{resource_type}"

                    await AuditService.log_request(
                        db=db,
                        action=action,
                        resource_type=resource_type,
                        method=method,
                        endpoint=endpoint,
                        ip_address=ip_address,
                        user_agent=user_agent,
                        request_body=request_body,
                        response_status=response.status_code
                    )
            except Exception as e:
                logger.error(f"Failed to log audit trail: {e}")

        # Add processing time header
        response.headers["X-Process-Time"] = str(process_time)

        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple rate limiting middleware"""

    def __init__(self, app, max_requests: int = 100, window: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window = window
        self.requests = {}

    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host if request.client else "unknown"

        # Clean old entries
        current_time = time.time()
        self.requests = {
            ip: [req_time for req_time in times if current_time - req_time < self.window]
            for ip, times in self.requests.items()
        }

        # Check rate limit
        if client_ip in self.requests:
            if len(self.requests[client_ip]) >= self.max_requests:
                return Response(
                    content="Rate limit exceeded",
                    status_code=429,
                    headers={"Retry-After": str(self.window)}
                )

        # Add current request
        if client_ip not in self.requests:
            self.requests[client_ip] = []
        self.requests[client_ip].append(current_time)

        response = await call_next(request)
        return response
