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
from app.access_control.models import UserUrlBlock
from app.access_control.service import UrlAccessService

from fastapi import Depends

from app.auth.dependencies import login_required

router = APIRouter(dependencies=[Depends(login_required)])


templates = Jinja2Templates(directory="app/templates")


# ----------------------------------------------------
# User List
# ----------------------------------------------------



def _parse_blocked_urls(
    value: str,
) -> list[str]:
    patterns = []
    seen = set()

    raw_items = (
        (value or "")
        .replace("\r\n", "\n")
        .replace("\r", "\n")
        .split("\n")
    )

    for raw_item in raw_items:
        raw_item = raw_item.strip()

        if not raw_item:
            continue

        normalized = (
            UrlAccessService.normalize_pattern(
                raw_item
            )
        )

        if normalized in seen:
            continue

        seen.add(normalized)
        patterns.append(normalized)

    return patterns


def _replace_user_url_blocks(
    db: Session,
    user_id: int,
    blocked_urls: str,
) -> list[str]:
    patterns = _parse_blocked_urls(
        blocked_urls
    )

    (
        db.query(UserUrlBlock)
        .filter(
            UserUrlBlock.user_id == user_id
        )
        .delete(
            synchronize_session=False
        )
    )

    for pattern in patterns:
        db.add(
            UserUrlBlock(
                user_id=user_id,
                url_pattern=pattern,
                is_active=True,
            )
        )

    return patterns


def _blocked_urls_text(
    db: Session,
    user_id: int,
) -> str:
    rows = (
        db.query(UserUrlBlock)
        .filter(
            UserUrlBlock.user_id == user_id,
            UserUrlBlock.is_active == True,
        )
        .order_by(
            UserUrlBlock.id.asc()
        )
        .all()
    )

    return "\n".join(
        row.url_pattern
        for row in rows
    )


@router.get("/users", response_class=HTMLResponse)
async def user_list(request: Request, db: Session = Depends(get_db)):

    users = UserService.get_all(db)

    return templates.TemplateResponse(
        request=request, name="users/list.html", context={"users": users}
    )


# ----------------------------------------------------
# Create User Page
# ----------------------------------------------------


@router.get("/users/create", response_class=HTMLResponse)
async def create_user_page(request: Request, db: Session = Depends(get_db)):

    roles = AuthService.get_all_roles(db)

    return templates.TemplateResponse(
        request=request, name="users/create.html", context={"roles": roles}
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
    blocked_urls: str = Form(""),
    db: Session = Depends(get_db),
):

    user = UserCreate(
        full_name=full_name,
        email=email,
        password=password,
        role_id=role_id,
        is_active=(is_active == "true"),
    )

    created_user = UserService.create(
        db,
        user,
    )

    if created_user is None:
        raise RuntimeError(
            "UserService.create returned None"
        )

    _replace_user_url_blocks(
        db=db,
        user_id=created_user.id,
        blocked_urls=blocked_urls,
    )

    db.commit()

    return RedirectResponse(url="/users", status_code=303)


# ----------------------------------------------------
# Edit User Page
# ----------------------------------------------------


@router.get("/users/{user_id}/edit", response_class=HTMLResponse)
async def edit_user_page(user_id: int, request: Request, db: Session = Depends(get_db)):

    user = UserService.get_by_id(db, user_id)

    roles = AuthService.get_all_roles(db)

    blocked_urls = _blocked_urls_text(
        db=db,
        user_id=user_id,
    )

    return templates.TemplateResponse(
        request=request,
        name="users/edit.html",
        context={
            "user": user,
            "roles": roles,
            "blocked_urls": blocked_urls,
        }
    )


# ----------------------------------------------------
# Update User
# ----------------------------------------------------


@router.post("/users/{user_id}/edit")
async def update_user(
    user_id: int,
    full_name: str = Form(...),
    email: str = Form(...),
    role_id: int = Form(...),
    is_active: str = Form("true"),
    password: str = Form(""),
    blocked_urls: str = Form(""),
    db: Session = Depends(get_db),
):

    data = UserUpdate(
        full_name=full_name,
        email=email,
        role_id=role_id,
        is_active=(is_active == "true"),
    )

    # Optional password update
    data.password = password

    UserService.update(
        db,
        user_id,
        data,
    )

    _replace_user_url_blocks(
        db=db,
        user_id=user_id,
        blocked_urls=blocked_urls,
    )

    db.commit()

    return RedirectResponse(url="/users", status_code=303)


# ----------------------------------------------------
# Reset Password
# ----------------------------------------------------


@router.post("/users/{user_id}/reset-password")
async def reset_password(
    user_id: int, password: str = Form(...), db: Session = Depends(get_db)
):

    UserService.reset_password(db, user_id, password)

    return RedirectResponse(url="/users", status_code=303)


# ----------------------------------------------------
# Activate / Deactivate User
# ----------------------------------------------------


@router.get("/users/{user_id}/toggle")
async def toggle_user(user_id: int, db: Session = Depends(get_db)):

    UserService.toggle_status(db, user_id)

    return RedirectResponse(url="/users", status_code=303)
