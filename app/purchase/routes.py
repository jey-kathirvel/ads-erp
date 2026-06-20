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
from app.products.service import ProductService

from app.purchase.schemas import PurchaseCreate
from app.purchase.service import PurchaseService
from app.purchase.item_service import PurchaseItemService

from app.accounts.service import AutoPostingService
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
# Purchase Entry
# ----------------------------------------------------

@router.get(
    "/purchase",
    response_class=HTMLResponse
)
async def purchase_page(

    request: Request,

    user=Depends(login_required),

    db: Session = Depends(get_db)

):

    # ------------------------------------
    # Redirect to Login if session expired
    # ------------------------------------

    if isinstance(user, RedirectResponse):

        return user

    suppliers = SupplierService.get_all(db)

    products = ProductService.get_all(db)

    return templates.TemplateResponse(

        request=request,

        name="purchase/create.html",

        context={

            "suppliers": suppliers,

            "products": products

        }

    )


# ----------------------------------------------------
# Save Purchase
# ----------------------------------------------------

@router.post("/purchase/save")
async def save_purchase(

    supplier_id: int = Form(...),

    subtotal: float = Form(...),

    discount: float = Form(0),

    taxable_amount: float = Form(...),

    cgst: float = Form(...),

    sgst: float = Form(...),

    igst: float = Form(0),

    grand_total: float = Form(...),

    payment_mode: str = Form(...),

    remarks: str = Form(""),

    product_id: list[int] = Form(...),

    qty: list[float] = Form(...),

    rate: list[float] = Form(...),

    gst: list[float] = Form(...),

    total: list[float] = Form(...),

    db: Session = Depends(get_db)

):

    purchase = PurchaseCreate(

        supplier_id=supplier_id,

        subtotal=subtotal,

        discount=discount,

        taxable_amount=taxable_amount,

        cgst=cgst,

        sgst=sgst,

        igst=igst,

        grand_total=grand_total,

        payment_mode=payment_mode,

        remarks=remarks

    )

    saved_purchase = PurchaseService.create(

        db,

        purchase

    )

    # ---------------------------------
    # Auto Ledger Posting
    # ---------------------------------

    AutoPostingService.post_purchase(

        db,

        saved_purchase

    )

    # ---------------------------------
    # Save Purchase Items
    # ---------------------------------

    for i in range(len(product_id)):

        PurchaseItemService.create(

            db=db,

            purchase_id=saved_purchase.id,

            product_id=product_id[i],

            qty=qty[i],

            rate=rate[i],

            gst_percentage=gst[i],

            total=total[i]

        )

    return RedirectResponse(

        url=f"/purchase/view/{saved_purchase.id}",

        status_code=303

    )


# ----------------------------------------------------
# Purchase List
# ----------------------------------------------------

@router.get(
    "/purchase/list",
    response_class=HTMLResponse
)
async def purchase_list(

    request: Request,

    db: Session = Depends(get_db)

):

    purchases = PurchaseService.get_all(db)

    return templates.TemplateResponse(

        request=request,

        name="purchase/list.html",

        context={

            "purchases": purchases

        }

    )


# ----------------------------------------------------
# Purchase View
# ----------------------------------------------------

@router.get(
    "/purchase/view/{purchase_id}",
    response_class=HTMLResponse
)
async def purchase_view(

    purchase_id: int,

    request: Request,

    db: Session = Depends(get_db)

):

    purchase = PurchaseService.get_by_id(

        db,

        purchase_id

    )

    items = PurchaseService.get_items(

        db,

        purchase_id

    )

    return templates.TemplateResponse(

        request=request,

        name="purchase/view.html",

        context={

            "purchase": purchase,

            "items": items

        }

    )


# ----------------------------------------------------
# Delete Purchase
# ----------------------------------------------------

@router.get(
    "/purchase/delete/{purchase_id}"
)
async def delete_purchase(

    purchase_id: int,

    db: Session = Depends(get_db)

):

    PurchaseItemService.rollback_stock(

        db,

        purchase_id

    )

    PurchaseItemService.delete_items(

        db,

        purchase_id

    )

    PurchaseService.delete(

        db,

        purchase_id

    )

    return RedirectResponse(

        url="/purchase/list",

        status_code=303

    )


# ----------------------------------------------------
# Purchase Print
# ----------------------------------------------------

@router.get(
    "/purchase/print/{purchase_id}",
    response_class=HTMLResponse
)
async def print_purchase(

    purchase_id: int,

    request: Request,

    db: Session = Depends(get_db)

):

    purchase = PurchaseService.get_by_id(

        db,

        purchase_id

    )

    items = PurchaseService.get_items(

        db,

        purchase_id

    )

    return templates.TemplateResponse(

        request=request,

        name="purchase/view.html",

        context={

            "purchase": purchase,

            "items": items,

            "print_mode": True

        }

    )