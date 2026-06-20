from fastapi import APIRouter
from fastapi import Depends
from fastapi import Form
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.users.schemas import UserCreate
from app.users.schemas import UserUpdate
from app.users.service import UserService
from app.auth.service import AuthService

from fastapi import Depends

from app.auth.dependencies import login_required

router = APIRouter(

    dependencies=[

        Depends(login_required)

    ]

)


templates = Jinja2Templates(
    directory="app/templates"
)


# ----------------------------------------------------
# User List
# ----------------------------------------------------

@router.get(
    "/users",
    response_class=HTMLResponse
)
async def user_list(
    request: Request,
    db: Session = Depends(get_db)
):

    users = UserService.get_all(db)

    return templates.TemplateResponse(
        request=request,
        name="users/list.html",
        context={
            "users": users
        }
    )


# ----------------------------------------------------
# Create User Page
# ----------------------------------------------------

@router.get(
    "/users/create",
    response_class=HTMLResponse
)
async def create_user_page(
    request: Request,
    db: Session = Depends(get_db)
):

    roles = AuthService.get_all_roles(db)

    return templates.TemplateResponse(
        request=request,
        name="users/create.html",
        context={
            "roles": roles
        }
    )


# ----------------------------------------------------
# Save User
# ----------------------------------------------------

@router.post("/users/create")
async def create_user(
    full_name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    role_id: int = Form(...),
    is_active: str = Form("true"),
    db: Session = Depends(get_db)
):

    user = UserCreate(
        full_name=full_name,
        email=email,
        password=password,
        role_id=role_id,
        is_active=(is_active == "true")
    )

    UserService.create(
        db,
        user
    )

    return RedirectResponse(
        url="/users",
        status_code=303
    )


# ----------------------------------------------------
# Edit User Page
# ----------------------------------------------------

@router.get(
    "/users/{user_id}/edit",
    response_class=HTMLResponse
)
async def edit_user_page(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db)
):

    user = UserService.get_by_id(
        db,
        user_id
    )

    roles = AuthService.get_all_roles(db)

    return templates.TemplateResponse(
        request=request,
        name="users/edit.html",
        context={
            "user": user,
            "roles": roles
        }
    )


# ----------------------------------------------------
# Update User
# ----------------------------------------------------

@router.post(
    "/users/{user_id}/edit"
)
async def update_user(
    user_id: int,
    full_name: str = Form(...),
    email: str = Form(...),
    role_id: int = Form(...),
    is_active: str = Form("true"),
    password: str = Form(""),
    db: Session = Depends(get_db)
):

    data = UserUpdate(
        full_name=full_name,
        email=email,
        role_id=role_id,
        is_active=(is_active == "true")
    )

    # Optional password update
    data.password = password

    UserService.update(
        db,
        user_id,
        data
    )

    return RedirectResponse(
        url="/users",
        status_code=303
    )


# ----------------------------------------------------
# Reset Password
# ----------------------------------------------------

@router.post(
    "/users/{user_id}/reset-password"
)
async def reset_password(
    user_id: int,
    password: str = Form(...),
    db: Session = Depends(get_db)
):

    UserService.reset_password(
        db,
        user_id,
        password
    )

    return RedirectResponse(
        url="/users",
        status_code=303
    )


# ----------------------------------------------------
# Activate / Deactivate User
# ----------------------------------------------------

@router.get(
    "/users/{user_id}/toggle"
)
async def toggle_user(
    user_id: int,
    db: Session = Depends(get_db)
):

    UserService.toggle_status(
        db,
        user_id
    )

    return RedirectResponse(
        url="/users",
        status_code=303
    )
