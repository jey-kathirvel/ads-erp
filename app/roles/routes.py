from fastapi import APIRouter
from fastapi import Depends
from fastapi import Form
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.auth.dependencies import login_required
from app.roles.service import RoleService
from app.roles.schemas import RoleCreate
from app.roles.schemas import RoleUpdate

router = APIRouter()

templates = Jinja2Templates(
    directory="app/templates"
)

# ----------------------------------------------------
# Role List
# ----------------------------------------------------

@router.get(
    "/roles",
    response_class=HTMLResponse
)
async def role_list(

    request: Request,

    db: Session = Depends(get_db),

    user=Depends(login_required)

):

    roles = RoleService.get_all(db)

    return templates.TemplateResponse(

        request=request,

        name="roles/list.html",

        context={

            "roles": roles,

            "user": user

        }

    )


# ----------------------------------------------------
# Create Role Page
# ----------------------------------------------------

@router.get(
    "/roles/create",
    response_class=HTMLResponse
)
async def create_role_page(

    request: Request,

    user=Depends(login_required)

):

    return templates.TemplateResponse(

        request=request,

        name="roles/create.html",

        context={

            "user": user

        }

    )


# ----------------------------------------------------
# Save Role
# ----------------------------------------------------

@router.post("/roles/create")
async def create_role(

    role_code: str = Form(...),

    role_name: str = Form(...),

    description: str = Form(""),

    is_active: bool = Form(True),

    db: Session = Depends(get_db),

    user=Depends(login_required)

):

    data = RoleCreate(

        role_code=role_code,

        role_name=role_name,

        description=description,

        is_active=is_active

    )

    RoleService.create(

        db,

        data

    )

    return RedirectResponse(

        "/roles",

        status_code=303

    )


# ----------------------------------------------------
# Edit Role Page
# ----------------------------------------------------

@router.get(
    "/roles/{role_id}/edit",
    response_class=HTMLResponse
)
async def edit_role_page(

    role_id: int,

    request: Request,

    db: Session = Depends(get_db),

    user=Depends(login_required)

):

    role = RoleService.get_by_id(

        db,

        role_id

    )

    return templates.TemplateResponse(

        request=request,

        name="roles/edit.html",

        context={

            "role": role,

            "user": user

        }

    )


# ----------------------------------------------------
# Update Role
# ----------------------------------------------------

@router.post(
    "/roles/{role_id}/edit"
)
async def update_role(

    role_id: int,

    role_code: str = Form(...),

    role_name: str = Form(...),

    description: str = Form(""),

    is_active: bool = Form(True),

    db: Session = Depends(get_db),

    user=Depends(login_required)

):

    data = RoleUpdate(

        role_code=role_code,

        role_name=role_name,

        description=description,

        is_active=is_active

    )

    RoleService.update(

        db,

        role_id,

        data

    )

    return RedirectResponse(

        "/roles",

        status_code=303

    )


# ----------------------------------------------------
# Enable / Disable
# ----------------------------------------------------

@router.get(
    "/roles/{role_id}/toggle"
)
async def toggle_role(

    role_id: int,

    db: Session = Depends(get_db),

    user=Depends(login_required)

):

    RoleService.toggle_status(

        db,

        role_id

    )

    return RedirectResponse(

        "/roles",

        status_code=303

    )


# ----------------------------------------------------
# Permissions
# ----------------------------------------------------

@router.get(
    "/roles/{role_id}/permissions",
    response_class=HTMLResponse
)
async def role_permissions(

    role_id: int,

    request: Request,

    db: Session = Depends(get_db),

    user=Depends(login_required)

):

    role = RoleService.get_by_id(

        db,

        role_id

    )

    permissions = RoleService.get_permissions(

        db,

        role_id

    )

    return templates.TemplateResponse(

        request=request,

        name="roles/permissions.html",

        context={

            "role": role,

            "permissions": permissions,

            "user": user

        }

    )