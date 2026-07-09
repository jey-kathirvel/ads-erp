from fastapi import APIRouter
from fastapi import Depends
from fastapi import Form
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.users.service import UserService
from app.auth.service import AuthService

router = APIRouter()

templates = Jinja2Templates(directory="app/templates")


# ----------------------------------------------------
# Login Page
# ----------------------------------------------------


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):

    # Temporarily always show login page
    # (Disable auto redirect while debugging)

    return templates.TemplateResponse(
        request=request, name="auth/login.html", context={"message": ""}
    )


# ----------------------------------------------------
# Login
# ----------------------------------------------------


@router.post("/login")
async def login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):

    user = UserService.authenticate(db, email, password)

    if user is None:

        return templates.TemplateResponse(
            request=request,
            name="auth/login.html",
            context={"message": "Invalid Email or Password"},
        )

    role = AuthService.get_role(db, user.role_id)

    request.session["user"] = {
        "id": user.id,
        "email": user.email,
        "name": user.full_name,
        "role_id": role.id,
        "role_code": role.role_code,
        "role_name": role.role_name,
    }

    # STEP 69R2A-R1: cache allowed modules in session
    permissions = AuthService.get_permissions(
        db,
        role.id,
    )

    request.session["allowed_modules"] = sorted(
        {
            permission.module_name.lower()
            for permission in permissions
            if permission.can_view
        }
    )

    request.session["name"] = user.full_name

    print("=================================")
    print("LOGIN SUCCESS")
    print(request.session)
    print("=================================")

    return RedirectResponse(url="/dashboard", status_code=303)


# ----------------------------------------------------
# Logout
# ----------------------------------------------------


@router.get("/logout")
async def logout(request: Request):

    request.session.clear()

    return RedirectResponse(url="/login", status_code=303)
