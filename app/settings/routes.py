from fastapi import APIRouter
from fastapi import Depends
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.settings.service import CompanyService

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


@router.get(
    "/settings/company",
    response_class=HTMLResponse
)
async def company_settings(

    request: Request,

    db: Session = Depends(get_db)

):

    company = CompanyService.get(db)

    return templates.TemplateResponse(

        request=request,

        name="settings/company.html",

        context={

            "company": company

        }

    )
