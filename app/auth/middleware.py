from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.responses import RedirectResponse


class AuthenticationMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request, call_next):

        path = request.url.path

        public_urls = [
            "/",
            "/login",
            "/logout",
            "/health",
            "/docs",
            "/redoc",
            "/openapi.json",
        ]

        # Static Files

        if path.startswith("/static"):

            return await call_next(request)

        if path.startswith("/favicon"):

            return await call_next(request)

        # Public URLs

        if path in public_urls:

            return await call_next(request)

        # Session

        try:

            session = request.session

        except Exception:

            return RedirectResponse("/login", status_code=303)

        # Debug

        print("MIDDLEWARE SESSION =", dict(session))

        if "user" not in session:

            return RedirectResponse(url=f"/login?next={path}", status_code=303)

        return await call_next(request)
