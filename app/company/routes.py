from fastapi import APIRouter
from fastapi import Depends
from fastapi import Form
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.config.database import get_db

from app.company.schemas import CompanySettingCreate
from app.company.service import CompanyService
from app.auth.dependencies import login_required

router = APIRouter()

templates = Jinja2Templates(
    directory="app/templates"
)


@router.get(
    "/settings/company",
    response_class=HTMLResponse
)
async def company_profile(

    request: Request,

    user=Depends(login_required),

    db: Session = Depends(get_db)

):

    # ------------------------------------
    # Redirect to Login if session expired
    # ------------------------------------

    if isinstance(user, RedirectResponse):

        return user
    company = CompanyService.get(db)

    return templates.TemplateResponse(

        request=request,

        name="company/profile.html",

        context={

            "company": company

        }

    )


@router.post(
    "/settings/company"
)
async def save_company(

    company_name: str = Form(...),

    gstin: str = Form(""),

    address: str = Form(""),

    city: str = Form(""),

    state: str = Form(""),

    pincode: str = Form(""),

    mobile: str = Form(""),

    email: str = Form(""),

    website: str = Form(""),

    invoice_prefix: str = Form("INV"),

    purchase_prefix: str = Form("PUR"),

    currency: str = Form("INR"),

    logo: str = Form(""),

    db: Session = Depends(get_db)

):

    company = CompanySettingCreate(

        company_name=company_name,

        gstin=gstin,

        address=address,

        city=city,

        state=state,

        pincode=pincode,

        mobile=mobile,

        email=email,

        website=website,

        invoice_prefix=invoice_prefix,

        purchase_prefix=purchase_prefix,

        currency=currency,

        logo=logo

    )

    CompanyService.save(

        db,

        company

    )

    return RedirectResponse(

        url="/settings/company",

        status_code=303

    )