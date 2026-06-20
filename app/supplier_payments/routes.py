from fastapi import APIRouter
from fastapi import Depends
from fastapi import Form
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.config.database import get_db

from app.suppliers.service import SupplierService

from app.supplier_payments.schemas import SupplierPaymentCreate
from app.supplier_payments.service import SupplierPaymentService

from app.accounts.service import PaymentPostingService
from app.auth.dependencies import login_required


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
# Payment Entry
# ----------------------------------------------------

@router.get(
    "/supplier-payments",
    response_class=HTMLResponse
)
async def payment_page(

    request: Request,

    db: Session = Depends(get_db)

):

    suppliers = SupplierService.get_all(db)

    return templates.TemplateResponse(

        request=request,

        name="supplier_payments/create.html",

        context={

            "suppliers": suppliers

        }

    )


# ----------------------------------------------------
# Save Payment
# ----------------------------------------------------

@router.post("/supplier-payments/save")
async def save_payment(

    supplier_id: int = Form(...),

    payment_mode: str = Form(...),

    amount: float = Form(...),

    remarks: str = Form(""),

    db: Session = Depends(get_db)

):

    payment = SupplierPaymentCreate(

        supplier_id=supplier_id,

        payment_mode=payment_mode,

        amount=amount,

        remarks=remarks

    )

    saved = SupplierPaymentService.create(

        db,

        payment

    )

    PaymentPostingService.supplier_payment(

        db,

        saved

    )

    return RedirectResponse(

        "/supplier-payments/list",

        status_code=303

    )


# ----------------------------------------------------
# Payment List
# ----------------------------------------------------

@router.get(
    "/supplier-payments/list",
    response_class=HTMLResponse
)
async def payment_list(

    request: Request,

    db: Session = Depends(get_db)

):

    payments = SupplierPaymentService.get_all(db)

    return templates.TemplateResponse(

        request=request,

        name="supplier_payments/list.html",

        context={

            "payments": payments

        }

    )


# ----------------------------------------------------
# Payment View
# ----------------------------------------------------

@router.get(
    "/supplier-payments/view/{payment_id}",
    response_class=HTMLResponse
)
async def payment_view(

    payment_id: int,

    request: Request,

    db: Session = Depends(get_db)

):

    payment = SupplierPaymentService.get_by_id(

        db,

        payment_id

    )

    return templates.TemplateResponse(

        request=request,

        name="supplier_payments/view.html",

        context={

            "payment": payment

        }

    )