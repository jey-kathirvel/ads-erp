from fastapi import APIRouter
from fastapi import Depends
from fastapi import Form
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.config.database import get_db

from app.billing.schemas import InvoiceCreate
from app.billing.service import BillingService
from app.billing.item_service import InvoiceItemService

from app.customers.service import CustomerService
from app.billing.models import Invoice
from app.products.service import ProductService
from app.inventory.service import InventoryService
from app.accounts.service import AutoPostingService
from app.billing.item_models import InvoiceItem
from app.auth.dependencies import login_required
from app.company.service import CompanyService

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
# New Billing Screen
# ----------------------------------------------------

@router.get(
    "/billing",
    response_class=HTMLResponse
)
async def billing_page(

    request: Request,

    user=Depends(login_required),

    db: Session = Depends(get_db)

):

    # ------------------------------------
    # Redirect to Login if session expired
    # ------------------------------------

    if isinstance(user, RedirectResponse):

        return user

    customers = CustomerService.get_all(db)

    products = ProductService.get_all(db)

    return templates.TemplateResponse(

        request=request,

        name="billing/create.html",

        context={

            "customers": customers,

            "products": products

        }

    )


# ----------------------------------------------------
# Save Invoice
# ----------------------------------------------------

@router.post("/billing/save")
async def save_invoice(

    customer_id: int | None = Form(None),

    manual_customer_name: str = Form(""),

    subtotal: float = Form(...),

    discount: float = Form(0),

    taxable_amount: float = Form(...),

    cgst: float = Form(...),

    sgst: float = Form(...),

    igst: float = Form(0),

    grand_total: float = Form(...),

payment_mode: str = Form(...),

payment_status: str = Form("Paid"),

remarks: str = Form(""),

    product_id: list[int] = Form(...),

    qty: list[float] = Form(...),

    rate: list[float] = Form(...),

    gst: list[float] = Form(...),

    total: list[float] = Form(...),

    db: Session = Depends(get_db)

):


    # ------------------------------------
    # Customer Handling
    # ------------------------------------

    final_customer_id = None

    if customer_id:

        final_customer_id = customer_id

    elif manual_customer_name.strip():

        customer = CustomerService.create_walkin_customer(
            db,
            manual_customer_name.strip()
        )

        final_customer_id = customer.id

    else:

        guest = CustomerService.get_guest_customer(db)

        final_customer_id = guest.id

    invoice = InvoiceCreate(

        customer_id=final_customer_id,

        subtotal=subtotal,

        discount=discount,

        taxable_amount=taxable_amount,

        cgst=cgst,

        sgst=sgst,

        igst=igst,

        grand_total=grand_total,

        payment_mode=payment_mode,

        payment_status=payment_status,

        remarks=remarks

    )
    saved_invoice = BillingService.create(

        db,

        invoice

    )

    # -------------------------
    # Auto Accounting Entry
    # -------------------------

    AutoPostingService.post_sales(

        db,

        saved_invoice

    )

    # -------------------------
    # Save Items & Inventory
    # -------------------------

    for i in range(len(product_id)):

        InvoiceItemService.create(

            db=db,

            invoice_id=saved_invoice.id,

            product_id=product_id[i],

            qty=qty[i],

            rate=rate[i],

            gst_percentage=gst[i],

            total=total[i]

        )

        product = ProductService.get_by_id(

            db,

            product_id[i]

        )

        balance = 0

        if product:

            balance = float(product.current_stock or 0) - float(qty[i])

        InventoryService.create(

            db=db,

            transaction_no=saved_invoice.invoice_no,

            transaction_type="SALE",

            product_id=product_id[i],

            reference_id=saved_invoice.id,

            qty=qty[i],

            balance_qty=balance,

            remarks="GST Invoice"

        )

        ProductService.update_stock(

            db,

            product_id[i],

            qty[i]

        )

    return RedirectResponse(

        url=f"/billing/view/{saved_invoice.id}",

        status_code=303

    )


# ----------------------------------------------------
# Invoice List
# ----------------------------------------------------

# ----------------------------------------------------
# Invoice List
# ----------------------------------------------------

@router.get(
    "/billing/list",
    response_class=HTMLResponse
)
async def invoice_list(
    request: Request,
    from_date: str | None = None,
    to_date: str | None = None,
    payment_status: str | None = None,
    payment_mode: str | None = None,
    db: Session = Depends(get_db)
):
    print("===================================")
    print("FROM DATE :", from_date)
    print("TO DATE   :", to_date)
    print("STATUS    :", payment_status)
    print("MODE      :", payment_mode)
    print("===================================")

    query = db.query(Invoice)

    # ------------------------------------
    # Date Filter
    # ------------------------------------

    if from_date:

        query = query.filter(
            Invoice.invoice_date >= from_date
        )

    if to_date:

        query = query.filter(
            Invoice.invoice_date <= to_date
        )

    # ------------------------------------
    # Payment Status Filter
    # ------------------------------------

    if payment_status:

        query = query.filter(
            Invoice.payment_status == payment_status
        )

    # ------------------------------------
    # Payment Mode Filter
    # ------------------------------------

    if payment_mode:

        query = query.filter(
            Invoice.payment_mode == payment_mode
        )

    invoices = (

        query

        .order_by(

            Invoice.id.desc()

        )

        .all()

    )

    return templates.TemplateResponse(

        request=request,

        name="billing/list.html",

        context={

            "invoices": invoices,

            "from_date": from_date,

            "to_date": to_date,

            "payment_status": payment_status,

            "payment_mode": payment_mode

        }

    )


# ----------------------------------------------------
# Invoice View
# ----------------------------------------------------

@router.get(
    "/billing/view/{invoice_id}",
    response_class=HTMLResponse
)
async def view_invoice(

    invoice_id: int,

    request: Request,

    db: Session = Depends(get_db)

):

    invoice = BillingService.get_by_id(

        db,

        invoice_id

    )

    items = BillingService.get_items(

        db,

        invoice_id

    )
    company = CompanyService.get(

    db

    )
    return templates.TemplateResponse(

        request=request,

        name="billing/view.html",

    context={

    "invoice": invoice,

    "items": items,

    "company": company

    }

    )
# ----------------------------------------------------
# Edit Invoice
# ----------------------------------------------------

@router.get(
    "/billing/{invoice_id}/edit",
    response_class=HTMLResponse
)
async def edit_invoice(

    invoice_id: int,

    request: Request,

    db: Session = Depends(get_db)

):

    invoice = BillingService.get_by_id(

        db,

        invoice_id

    )

    if invoice is None:

        return RedirectResponse(

            "/billing/list",

            status_code=303

        )

    customers = CustomerService.get_all(db)

    products = ProductService.get_all(db)

    items = BillingService.get_items(

        db,

        invoice_id

    )

    return templates.TemplateResponse(

        request=request,

        name="billing/edit.html",

        context={

            "invoice": invoice,

            "customers": customers,

            "products": products,

            "items": items

        }

    )


@router.post(
    "/billing/{invoice_id}/edit"
)
async def update_invoice(

    invoice_id: int,

    customer_id: int = Form(...),

    subtotal: float = Form(...),

    discount: float = Form(0),

    taxable_amount: float = Form(...),

    cgst: float = Form(...),

    sgst: float = Form(...),

    igst: float = Form(0),

    grand_total: float = Form(...),

payment_mode: str = Form(...),

payment_status: str = Form("Paid"),

remarks: str = Form(""),

    product_id: list[int] = Form(...),

    qty: list[float] = Form(...),

    rate: list[float] = Form(...),

    gst: list[float] = Form(...),

    total: list[float] = Form(...),

    db: Session = Depends(get_db)

):

    invoice = InvoiceCreate(

        customer_id=customer_id,

        subtotal=subtotal,

        discount=discount,

        taxable_amount=taxable_amount,

        cgst=cgst,

        sgst=sgst,

        igst=igst,

        grand_total=grand_total,

payment_mode=payment_mode,

payment_status=payment_status,

remarks=remarks

    )

    BillingService.update(

    db=db,

    invoice_id=invoice_id,

    data=invoice,

    product_id=product_id,

    qty=qty,

    rate=rate,

    gst=gst,

    total=total

)

    return RedirectResponse(

        url=f"/billing/view/{invoice_id}",

        status_code=303

    )
# ----------------------------------------------------
# Delete Invoice
# ----------------------------------------------------

@router.get(
    "/billing/{invoice_id}/delete"
)
async def delete_invoice(

    invoice_id: int,

    db: Session = Depends(get_db)

):

    BillingService.delete(

        db,

        invoice_id

    )

    return RedirectResponse(

        url="/billing/list",

        status_code=303

    )
# ----------------------------------------------------
# Print Invoice
# ----------------------------------------------------

@router.get(
    "/billing/print/{invoice_id}",
    response_class=HTMLResponse
)
async def print_invoice(

    invoice_id: int,

    request: Request,

    db: Session = Depends(get_db)

):
    
    invoice = BillingService.get_by_id(

        db,

        invoice_id

    )

    items = BillingService.get_items(

        db,

        invoice_id

    )
    company = CompanyService.get(

    db

    )
    return templates.TemplateResponse(

        request=request,

        name="billing/view.html",

    context={

    "invoice": invoice,

    "items": items,

    "company": company

    }

    )