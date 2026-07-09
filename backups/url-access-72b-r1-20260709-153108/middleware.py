from starlette.middleware.base import (
    BaseHTTPMiddleware,
)
from starlette.requests import Request
from starlette.responses import PlainTextResponse

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
            blocked = (
                UrlAccessService.is_blocked(
                    db=db,
                    user_id=int(user_id),
                    request_path=request_path,
                )
            )

        finally:
            db.close()

        if blocked:
            return PlainTextResponse(
                "You Are Not Authorized",
                status_code=403,
            )

        return await call_next(
            request
        )
