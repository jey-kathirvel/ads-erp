from fastapi import APIRouter
from fastapi import Depends
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from sqlalchemy.orm import Session

from app.config.database import get_db
from app.permissions.service import PermissionService
from fastapi import Form
from fastapi.responses import RedirectResponse

router = APIRouter()

templates = Jinja2Templates(directory="app/templates")

MODULES = [
    "dashboard",
    "customers",
    "suppliers",
    "products",
    "categories",
    "billing",
    "inventory",
    "purchase",
    "reports",
    "accounts",
    "company",
    "users",
    "roles",
]


@router.get("/permissions", response_class=HTMLResponse)
async def permission_page(request: Request, db: Session = Depends(get_db)):

    roles = PermissionService.get_roles(db)

    role_id = request.query_params.get("role_id")

    permissions = {}

    if role_id:

        permissions = PermissionService.get_permissions(db, int(role_id))

    return templates.TemplateResponse(
        request=request,
        name="permissions/index.html",
        context={
            "roles": roles,
            "modules": MODULES,
            "permissions": permissions,
            "selected_role": role_id,
        },
    )


@router.post("/permissions/save")
async def save_permissions(
    request: Request, role_id: int = Form(...), db: Session = Depends(get_db)
):

    for module in MODULES:

        PermissionService.save(
            db=db,
            role_id=role_id,
            module_name=module,
            can_view=(f"{module}_view" in await request.form()),
            can_add=(f"{module}_add" in await request.form()),
            can_edit=(f"{module}_edit" in await request.form()),
            can_delete=(f"{module}_delete" in await request.form()),
        )

    return RedirectResponse(url=f"/permissions?role_id={role_id}", status_code=303)
