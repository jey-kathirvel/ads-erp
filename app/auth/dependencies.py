from fastapi import Request
from fastapi.responses import RedirectResponse


def login_required(request: Request):

    if "user" not in request.session:

        return RedirectResponse(
            url="/login",
            status_code=303
        )

    return request.session.get("user")


# Backward compatibility
require_login = login_required