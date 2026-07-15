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
from app.auth.dependencies import login_required
from app.auth.security import PasswordSecurity
from app.users.models import User

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


# ----------------------------------------------------
# Change Password
# ----------------------------------------------------


@router.get("/change-password", response_class=HTMLResponse)
async def change_password_page(request: Request, user=Depends(login_required)):
    return templates.TemplateResponse(
        request=request,
        name="auth/change_password.html",
        context={"message": "", "success": False},
    )


@router.post("/change-password", response_class=HTMLResponse)
async def change_password(
    request: Request,
    current_password: str = Form(...),
    new_password: str = Form(...),
    confirm_password: str = Form(...),
    user=Depends(login_required),
    db: Session = Depends(get_db),
):
    session_user = request.session.get("user", {})
    db_user = db.get(User, session_user.get("id"))

    message = ""
    if not db_user or not PasswordSecurity.verify_password(
        current_password, db_user.password_hash
    ):
        message = "Current password is incorrect."
    elif new_password != confirm_password:
        message = "New password and confirmation do not match."
    elif len(new_password) < 8:
        message = "New password must contain at least 8 characters."
    elif new_password == current_password:
        message = "New password must be different from the current password."

    if message:
        return templates.TemplateResponse(
            request=request,
            name="auth/change_password.html",
            context={"message": message, "success": False},
            status_code=400,
        )

    db_user.password_hash = PasswordSecurity.hash_password(new_password)
    db.commit()

    return templates.TemplateResponse(
        request=request,
        name="auth/change_password.html",
        context={
            "message": "Password changed successfully.",
            "success": True,
        },
    )
