from fastapi import Request
from fastapi.responses import RedirectResponse


def require_login(request: Request):

    if "user" not in request.session:

        return RedirectResponse("/login", status_code=303)

    return None
