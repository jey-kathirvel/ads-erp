from starlette.middleware.base import (
    BaseHTTPMiddleware,
)
from starlette.requests import Request
from fastapi.templating import Jinja2Templates

from app.config.database import SessionLocal
from app.access_control.service import (
    UrlAccessService,
)


class UserUrlAccessMiddleware(
    BaseHTTPMiddleware
):

    async def dispatch(
        self,
        request: Request,
        call_next,
    ):
        user = request.session.get(
            "user"
        )

        request.state.blocked_url_patterns = []
        request.state.url_allowed = lambda path: True

        if not user:
            return await call_next(
                request
            )

        role_code = str(
            user.get(
                "role_code",
                ""
            )
            or ""
        ).strip().upper()

        if role_code == "ADMIN":
            return await call_next(
                request
            )

        user_id = user.get("id")

        if not user_id:
            return await call_next(
                request
            )

        request_path = (
            request.url.path
            or "/"
        )

        db = SessionLocal()

        try:
            patterns = UrlAccessService.get_active_patterns(db, int(user_id))

        finally:
            db.close()

        request.state.blocked_url_patterns = patterns
        request.state.url_allowed = lambda path: UrlAccessService.path_is_allowed(patterns, path)
        blocked = not request.state.url_allowed(request_path)

        if blocked:
            templates = Jinja2Templates(directory="app/templates")
            return templates.TemplateResponse(
                request=request,
                name="errors/403.html",
                context={"blocked_path": request_path},
                status_code=403,
            )

        return await call_next(
            request
        )
