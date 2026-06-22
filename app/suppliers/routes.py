from fastapi import APIRouter
from fastapi import Depends
from fastapi import Form
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.config.database import get_db

from app.suppliers.schemas import SupplierCreate
from app.suppliers.service import SupplierService
from app.suppliers.ledger_service import SupplierLedgerService

from app.purchase.service import PurchaseService
from app.auth.dependencies import login_required

from fastapi import Depends

from app.auth.dependencies import login_required

router = APIRouter(dependencies=[Depends(login_required)])


templates = Jinja2Templates(directory="app/templates")


# ----------------------------------------------------
# Supplier List
# ----------------------------------------------------


@router.get("/suppliers", response_class=HTMLResponse)
async def supplier_list(
    request: Request, user=Depends(login_required), db: Session = Depends(get_db)
):

    # ------------------------------------
    # Redirect to Login if session expired
    # ------------------------------------

    if isinstance(user, RedirectResponse):

        return user

    suppliers = SupplierService.get_all(db)

    return templates.TemplateResponse(
        request=request, name="suppliers/list.html", context={"suppliers": suppliers}
    )


# ----------------------------------------------------
# Create Supplier Page
# ----------------------------------------------------


@router.get("/suppliers/create", response_class=HTMLResponse)
async def create_supplier_page(request: Request):

    return templates.TemplateResponse(request=request, name="suppliers/create.html")


# ----------------------------------------------------
# Edit Supplier Page
# ----------------------------------------------------


@router.get("/suppliers/{supplier_id}/edit", response_class=HTMLResponse)
async def edit_supplier_page(
    supplier_id: int, request: Request, db: Session = Depends(get_db)
):

    supplier = SupplierService.get_by_id(db, supplier_id)

    if supplier is None:

        return RedirectResponse("/suppliers", status_code=303)

    return templates.TemplateResponse(
        request=request, name="suppliers/edit.html", context={"supplier": supplier}
    )


# ----------------------------------------------------
# Save Supplier
# ----------------------------------------------------


@router.post("/suppliers/create")
async def create_supplier(
    supplier_name: str = Form(...),
    contact_person: str = Form(""),
    mobile: str = Form(""),
    email: str = Form(""),
    gstin: str = Form(""),
    address1: str = Form(""),
    address2: str = Form(""),
    city: str = Form(""),
    state: str = Form(""),
    pincode: str = Form(""),
    opening_balance: float = Form(0),
    db: Session = Depends(get_db),
):

    supplier = SupplierCreate(
        supplier_name=supplier_name,
        contact_person=contact_person,
        mobile=mobile,
        email=email,
        gstin=gstin,
        address1=address1,
        address2=address2,
        city=city,
        state=state,
        pincode=pincode,
        opening_balance=opening_balance,
    )

    SupplierService.create(db, supplier)

    return RedirectResponse(url="/suppliers", status_code=303)


# ----------------------------------------------------
# Update Supplier
# ----------------------------------------------------


@router.post("/suppliers/{supplier_id}/edit")
async def update_supplier(
    supplier_id: int,
    supplier_name: str = Form(...),
    contact_person: str = Form(""),
    mobile: str = Form(""),
    email: str = Form(""),
    gstin: str = Form(""),
    address1: str = Form(""),
    address2: str = Form(""),
    city: str = Form(""),
    state: str = Form(""),
    pincode: str = Form(""),
    opening_balance: float = Form(0),
    db: Session = Depends(get_db),
):

    supplier = SupplierCreate(
        supplier_name=supplier_name,
        contact_person=contact_person,
        mobile=mobile,
        email=email,
        gstin=gstin,
        address1=address1,
        address2=address2,
        city=city,
        state=state,
        pincode=pincode,
        opening_balance=opening_balance,
    )

    SupplierService.update(db, supplier_id, supplier)

    return RedirectResponse(url="/suppliers", status_code=303)


# ----------------------------------------------------
# Supplier Ledger
# ----------------------------------------------------


@router.get("/suppliers/{supplier_id}/ledger", response_class=HTMLResponse)
async def supplier_ledger(
    supplier_id: int, request: Request, db: Session = Depends(get_db)
):

    summary = SupplierLedgerService.get_supplier_summary(db, supplier_id)

    purchases = [
        purchase
        for purchase in PurchaseService.get_all(db)
        if purchase.supplier_id == supplier_id
    ]

    return templates.TemplateResponse(
        request=request,
        name="suppliers/ledger.html",
        context={"summary": summary, "purchases": purchases},
    )


# ----------------------------------------------------
# Outstanding Report
# ----------------------------------------------------


@router.get("/suppliers/outstanding", response_class=HTMLResponse)
async def outstanding_report(request: Request, db: Session = Depends(get_db)):

    suppliers = SupplierLedgerService.get_all_outstanding(db)

    return templates.TemplateResponse(
        request=request,
        name="suppliers/outstanding.html",
        context={"suppliers": suppliers},
    )
