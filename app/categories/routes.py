from fastapi import APIRouter
from fastapi import Depends
from fastapi import Form
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.categories.schemas import CategoryCreate
from app.categories.service import CategoryService
from app.auth.dependencies import login_required

router = APIRouter()

templates = Jinja2Templates(
    directory="app/templates"
)


# -----------------------------------
# Category List
# -----------------------------------

@router.get(
    "/categories",
    response_class=HTMLResponse
)
async def category_list(
    request: Request,

    user=Depends(login_required),

    db: Session = Depends(get_db)

):

    # ------------------------------------
    # Redirect to Login if session expired
    # ------------------------------------

    if isinstance(user, RedirectResponse):

        return user

    categories = CategoryService.get_all(db)

    return templates.TemplateResponse(
        request=request,
        name="categories/list.html",
        context={
            "categories": categories
        }
    )


# -----------------------------------
# Create Category Page
# -----------------------------------

@router.get(
    "/categories/create",
    response_class=HTMLResponse
)
async def create_category_page(
    request: Request
):

    return templates.TemplateResponse(
        request=request,
        name="categories/create.html"
    )


# -----------------------------------
# Save Category
# -----------------------------------

@router.post("/categories/create")
async def create_category(

    category_name: str = Form(...),

    description: str = Form(""),

    db: Session = Depends(get_db)

):

    category = CategoryCreate(

        category_name=category_name,

        description=description

    )

    CategoryService.create(

        db,

        category

    )

    return RedirectResponse(

        "/categories",

        status_code=303

    )
