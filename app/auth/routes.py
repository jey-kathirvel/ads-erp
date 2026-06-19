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

router = APIRouter()

templates = Jinja2Templates(
    directory="app/templates"
)


@router.get(
    "/login",
    response_class=HTMLResponse
)
async def login_page(
    request: Request
):

    return templates.TemplateResponse(

        request=request,

        name="auth/login.html",

        context={
            "message": ""
        }

    )


@router.post("/login")
async def login(

    request: Request,

    email: str = Form(...),

    password: str = Form(...),

    db: Session = Depends(get_db)

):

    user = UserService.authenticate(

        db,

        email,

        password

    )

    if user is None:

        return templates.TemplateResponse(

            request=request,

            name="auth/login.html",

            context={

                "message": "Invalid Email or Password"

            }

        )

    request.session["user"] = user.email

    request.session["name"] = user.full_name

    return RedirectResponse(

        "/dashboard",

        status_code=303

    )


@router.get("/logout")
async def logout(request: Request):

    request.session.clear()

    return RedirectResponse(

        url="/login?logout=1",

        status_code=303

    )