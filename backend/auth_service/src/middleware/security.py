"""Enhanced security middleware for authentication service."""

import logging
import hashlib
import time
from datetime import datetime, timezone
from typing import Dict, Set
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import ipaddress

logger = logging.getLogger(__name__)

class SecurityEnhancementMiddleware(BaseHTTPMiddleware):
    """Middleware for additional security measures."""
    
    def __init__(
        self, 
        app,
        blocked_ips: Set[str] = None,
        allowed_ips: Set[str] = None,
        block_suspicious_agents: bool = True,
        enable_csrf_protection: bool = True,
        max_request_size: int = 10 * 1024 * 1024,  # 10MB
        enable_honeypot_detection: bool = True
    ):
        super().__init__(app)
        self.blocked_ips = blocked_ips or set()
        self.allowed_ips = allowed_ips or set()
        self.block_suspicious_agents = block_suspicious_agents
        self.enable_csrf_protection = enable_csrf_protection
        self.max_request_size = max_request_size
        self.enable_honeypot_detection = enable_honeypot_detection
        
        # Common suspicious patterns
        self.suspicious_agents = {
            "sqlmap", "nikto", "nmap", "masscan", "zap", "burpsuite",
            "w3af", "havij", "pangolin", "jsql", "commix", "xmlrpc"
        }
        
        # Honeypot paths that should never be accessed
        self.honeypot_paths = {
            "/admin", "/phpmyadmin", "/wp-admin", "/wp-login.php",
            "/xmlrpc.php", "/.env", "/config.php", "/backup",
            "/phpinfo.php", "/test.php", "/info.php"
        }
    
    async def dispatch(self, request: Request, call_next):
        # Extract client IP
        client_ip = self.get_client_ip(request)
        
        # 1. IP-based blocking
        if await self.check_ip_restrictions(client_ip, request):
            return self.create_blocked_response("IP address blocked")
        
        # 2. User-Agent filtering
        if self.block_suspicious_agents and await self.check_suspicious_user_agent(request):
            return self.create_blocked_response("Suspicious user agent detected")
        
        # 3. Request size limiting
        if await self.check_request_size(request):
            return self.create_blocked_response("Request too large")
        
        # 4. Honeypot detection
        if self.enable_honeypot_detection and await self.check_honeypot_access(request):
            await self.log_security_event("honeypot_access", client_ip, request)
            return self.create_blocked_response("Path not found", status_code=404)
        
        # 5. Basic SQL injection detection
        if await self.check_sql_injection_patterns(request):
            await self.log_security_event("sql_injection_attempt", client_ip, request)
            return self.create_blocked_response("Malicious request detected")
        
        # 6. CSRF protection for state-changing methods
        if (self.enable_csrf_protection and 
            request.method in ["POST", "PUT", "DELETE", "PATCH"] and
            not await self.check_csrf_token(request)):
            # Only enforce CSRF for browser requests (has Referer header)
            if request.headers.get("referer"):
                return self.create_blocked_response("CSRF token missing or invalid")
        
        # Process request
        start_time = time.time()
        response = await call_next(request)
        duration = time.time() - start_time
        
        # Add security headers
        response = await self.add_security_headers(response, duration)
        
        return response
    
    def get_client_ip(self, request: Request) -> str:
        """Extract client IP address."""
        # Check forwarded headers
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        return request.client.host if request.client else "unknown"
    
    async def check_ip_restrictions(self, client_ip: str, request: Request) -> bool:
        """Check if IP should be blocked."""
        if client_ip == "unknown":
            return False
        
        try:
            ip_addr = ipaddress.ip_address(client_ip)
            
            # Check explicit blocks
            if client_ip in self.blocked_ips:
                await self.log_security_event("blocked_ip_access", client_ip, request)
                return True
            
            # Check allowlist (if configured)
            if self.allowed_ips and client_ip not in self.allowed_ips:
                await self.log_security_event("ip_not_in_allowlist", client_ip, request)
                return True
            
            # Block known bad IP ranges (private IPs accessing from internet)
            if ip_addr.is_private and not self.is_local_request(request):
                await self.log_security_event("private_ip_external_access", client_ip, request)
                return True
                
        except ValueError:
            # Invalid IP format
            await self.log_security_event("invalid_ip_format", client_ip, request)
            return True
        
        return False
    
    def is_local_request(self, request: Request) -> bool:
        """Check if request is from local network."""
        # This is a simplified check - in production, you'd configure this properly
        return (request.headers.get("host", "").startswith("localhost") or
                request.headers.get("host", "").startswith("127.0.0.1"))
    
    async def check_suspicious_user_agent(self, request: Request) -> bool:
        """Check for suspicious user agents."""
        user_agent = request.headers.get("user-agent", "").lower()
        
        if not user_agent:
            await self.log_security_event("missing_user_agent", self.get_client_ip(request), request)
            return True
        
        for suspicious in self.suspicious_agents:
            if suspicious in user_agent:
                await self.log_security_event("suspicious_user_agent", self.get_client_ip(request), request)
                return True
        
        return False
    
    async def check_request_size(self, request: Request) -> bool:
        """Check request size limits."""
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > self.max_request_size:
            await self.log_security_event("oversized_request", self.get_client_ip(request), request)
            return True
        return False
    
    async def check_honeypot_access(self, request: Request) -> bool:
        """Check if accessing honeypot paths."""
        path = request.url.path.lower()
        return any(honeypot in path for honeypot in self.honeypot_paths)
    
    async def check_sql_injection_patterns(self, request: Request) -> bool:
        """Basic SQL injection pattern detection."""
        # Check URL parameters
        query_string = str(request.url.query).lower()
        
        # Simple SQL injection patterns
        sql_patterns = [
            "union select", "' or '1'='1", "' or 1=1", 
            "drop table", "delete from", "insert into",
            "exec xp_", "sp_executesql", "'; exec",
            "' and '1'='1", "' and 1=1", "/*", "*/"
        ]
        
        for pattern in sql_patterns:
            if pattern in query_string:
                return True
        
        return False
    
    async def check_csrf_token(self, request: Request) -> bool:
        """Basic CSRF token validation."""
        # For API endpoints, we typically use other methods like proper CORS
        # This is a simplified check - in production, implement proper CSRF tokens
        
        # Skip CSRF for API calls with proper headers
        if request.headers.get("content-type", "").startswith("application/json"):
            return True
        
        # Check for CSRF token in headers or form data
        csrf_token = (request.headers.get("x-csrf-token") or 
                     request.headers.get("x-xsrf-token"))
        
        if not csrf_token:
            return False  # No CSRF token provided
        
        # In production, validate the token against a stored value
        return True  # Simplified - always pass for now
    
    async def add_security_headers(self, response, duration: float):
        """Add security headers to response."""
        # Content Security Policy
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self'; "
            "connect-src 'self'; "
            "frame-ancestors 'none'"
        )
        
        # Additional security headers
        response.headers.update({
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": (
                "geolocation=(), microphone=(), camera=(), "
                "payment=(), usb=(), magnetometer=(), gyroscope=()"
            ),
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "X-Process-Time": f"{duration:.3f}",
            "X-Security-Headers": "enabled"
        })
        
        # Remove server info
        if "server" in response.headers:
            del response.headers["server"]
        
        return response
    
    async def log_security_event(self, event_type: str, client_ip: str, request: Request):
        """Log security events."""
        logger.warning(
            f"Security event: {event_type} from {client_ip} "
            f"- {request.method} {request.url.path} "
            f"- User-Agent: {request.headers.get('user-agent', 'N/A')}"
        )
    
    def create_blocked_response(self, message: str, status_code: int = 403) -> JSONResponse:
        """Create a response for blocked requests."""
        return JSONResponse(
            status_code=status_code,
            content={
                "detail": message,
                "timestamp": datetime.now(timezone.utc).isoformat()
            },
            headers={
                "X-Security-Block": "true",
                "X-Content-Type-Options": "nosniff"
            }
        )

class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    """Middleware specifically for request size limiting."""
    
    def __init__(self, app, max_size: int = 10 * 1024 * 1024):  # 10MB default
        super().__init__(app)
        self.max_size = max_size
    
    async def dispatch(self, request: Request, call_next):
        content_length = request.headers.get("content-length")
        
        if content_length and int(content_length) > self.max_size:
            return JSONResponse(
                status_code=413,
                content={
                    "detail": f"Request too large. Maximum size: {self.max_size} bytes",
                    "max_size": self.max_size,
                    "received_size": int(content_length)
                }
            )
        
        return await call_next(request)