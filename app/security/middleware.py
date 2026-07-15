from urllib.parse import urlparse

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, PlainTextResponse


SAFE_METHODS = {"GET", "HEAD", "OPTIONS", "TRACE"}
LEGACY_MUTATION_MARKERS = ("/delete/", "/toggle/", "/backup/run")


class CSRFMiddleware(BaseHTTPMiddleware):
    """Reject cross-site browser mutations using Fetch Metadata and Origin."""

    async def dispatch(self, request: Request, call_next):
        method = request.method.upper()
        path = request.url.path.lower()
        # Several legacy screens still perform mutations through GET links.
        # Treat them as unsafe until they can be migrated to POST forms.
        is_unsafe = method not in SAFE_METHODS or (
            method == "GET" and any(marker in path for marker in LEGACY_MUTATION_MARKERS)
        )
        if is_unsafe:
            fetch_site = request.headers.get("sec-fetch-site", "").lower()
            if fetch_site == "cross-site":
                return JSONResponse({"detail": "Cross-site request blocked"}, status_code=403)

            origin = request.headers.get("origin")
            if origin:
                origin_host = urlparse(origin).netloc.lower()
                request_host = request.headers.get("host", "").lower()
                if origin_host != request_host:
                    return JSONResponse({"detail": "Invalid request origin"}, status_code=403)

        return await call_next(request)


class ModuleAuthorizationMiddleware(BaseHTTPMiddleware):
    """Enforce module visibility on the backend, independently of the sidebar."""

    PATH_MODULES = {
        "/dashboard": "dashboard", "/customers": "customers", "/suppliers": "suppliers",
        "/products": "products", "/categories": "categories", "/billing": "billing",
        "/booking": "booking", "/inventory": "inventory", "/purchase": "purchase",
        "/reports": "reports", "/accounts": "accounts", "/supplier-payments": "accounts",
        "/hrm": "hrm", "/custom-gst": "custom_gst", "/incidents": "incidents",
        "/finance-tools": "finance_tools", "/users": "users", "/roles": "roles",
        "/permissions": "roles", "/settings/company": "company",
    }

    async def dispatch(self, request: Request, call_next):
        user = request.session.get("user")
        if not user or str(user.get("role_code", "")).upper() == "ADMIN":
            return await call_next(request)

        path = request.url.path.rstrip("/") or "/"
        matches = [(prefix, module) for prefix, module in self.PATH_MODULES.items()
                   if path == prefix or path.startswith(prefix + "/")]
        if matches:
            _, module = max(matches, key=lambda item: len(item[0]))
            allowed = {str(item).lower() for item in request.session.get("allowed_modules", [])}
            if module not in allowed:
                return PlainTextResponse("You Are Not Authorized", status_code=403)

        return await call_next(request)
