from functools import wraps

from fastapi import Request
from fastapi import HTTPException
from fastapi import status

from app.config.database import SessionLocal
from app.auth.service import AuthService

# ----------------------------------------------------
# Login Required
# ----------------------------------------------------


def login_required(request: Request):

    user = request.session.get("user")

    if not user:

        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER, headers={"Location": "/login"}
        )

    return user


# ----------------------------------------------------
# Backward Compatibility
# ----------------------------------------------------

require_login = login_required


# ----------------------------------------------------
# Permission Required
# ----------------------------------------------------


def permission_required(module_name: str, action: str = "can_view"):

    def decorator(func):

        @wraps(func)
        async def wrapper(*args, **kwargs):

            request = kwargs.get("request")

            if request is None:

                for arg in args:

                    if isinstance(arg, Request):

                        request = arg

                        break

            if request is None:

                raise HTTPException(
                    status_code=status.HTTP_303_SEE_OTHER,
                    headers={"Location": "/login"},
                )

            user = login_required(request)

            db = SessionLocal()

            try:

                allowed = AuthService.has_permission(
                    db=db,
                    role_id=user["role_id"],
                    module_name=module_name,
                    action=action,
                )

            finally:

                db.close()

            if not allowed:

                raise HTTPException(
                    status_code=status.HTTP_303_SEE_OTHER,
                    headers={"Location": "/dashboard"},
                )

            return await func(*args, **kwargs)

        return wrapper

    return decorator
