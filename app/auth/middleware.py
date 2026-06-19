from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.responses import RedirectResponse


class AuthenticationMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request, call_next):

        path = request.url.path

        # ----------------------------
        # Public URLs
        # ----------------------------

        public_urls = [

            "/",

            "/login",

            "/health",

            "/docs",

            "/redoc",

            "/openapi.json"

        ]

        # ----------------------------
        # Allow Static Files
        # ----------------------------

        if path.startswith("/static"):

            return await call_next(request)

        if path.startswith("/favicon.ico"):

            return await call_next(request)

        # ----------------------------
        # Allow Public URLs
        # ----------------------------

        if path in public_urls:

            return await call_next(request)

        # ----------------------------
        # Session Check
        # ----------------------------

        try:

            session = request.session

        except Exception:

            return await call_next(request)

        if "user" not in session:

            return RedirectResponse(

                url="/login?next=" + path,

                status_code=303

            )

        return await call_next(request)