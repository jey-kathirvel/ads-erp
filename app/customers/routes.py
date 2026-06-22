from fastapi import APIRouter
from fastapi import Depends
from fastapi import Form
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.customers.schemas import CustomerCreate
from app.customers.service import CustomerService
from app.auth.dependencies import login_required

from fastapi import Depends

from app.auth.dependencies import login_required

router = APIRouter(dependencies=[Depends(login_required)])


templates = Jinja2Templates(directory="app/templates")


# -------------------------------
# Customer List
# -------------------------------


@router.get("/customers", response_class=HTMLResponse)
async def customer_list(
    request: Request, user=Depends(login_required), db: Session = Depends(get_db)
):

    # --------------------------------
    # Login Validation
    # --------------------------------

    if isinstance(user, RedirectResponse):

        return user

    customers = CustomerService.get_all(db)

    return templates.TemplateResponse(
        request=request, name="customers/list.html", context={"customers": customers}
    )


# -------------------------------
# Create Customer Page
# -------------------------------


@router.get("/customers/create", response_class=HTMLResponse)
async def customer_create_page(request: Request):

    return templates.TemplateResponse(request=request, name="customers/create.html")


# -------------------------------
# Save Customer
# -------------------------------


@router.post("/customers/create")
async def customer_create(
    customer_name: str = Form(...),
    contact_person: str = Form(""),
    mobile: str = Form(""),
    email: str = Form(""),
    gstin: str = Form(""),
    address1: str = Form(""),
    address2: str = Form(""),
    city: str = Form(""),
    state: str = Form(""),
    pincode: str = Form(""),
    credit_limit: float = Form(0),
    opening_balance: float = Form(0),
    db: Session = Depends(get_db),
):

    customer = CustomerCreate(
        customer_name=customer_name,
        contact_person=contact_person,
        mobile=mobile,
        email=email if email else None,
        gstin=gstin,
        address1=address1,
        address2=address2,
        city=city,
        state=state,
        pincode=pincode,
        credit_limit=credit_limit,
        opening_balance=opening_balance,
    )

    CustomerService.create(db, customer)

    return RedirectResponse("/customers", status_code=303)


# -------------------------------
# View Customer
# -------------------------------


@router.get("/customers/{customer_id}", response_class=HTMLResponse)
async def view_customer(
    customer_id: int, request: Request, db: Session = Depends(get_db)
):

    customer = CustomerService.get_by_id(db, customer_id)

    return templates.TemplateResponse(
        request=request, name="customers/view.html", context={"customer": customer}
    )


# -------------------------------
# Edit Customer Page
# -------------------------------


@router.get("/customers/{customer_id}/edit", response_class=HTMLResponse)
async def edit_customer_page(
    customer_id: int, request: Request, db: Session = Depends(get_db)
):

    customer = CustomerService.get_by_id(db, customer_id)

    return templates.TemplateResponse(
        request=request, name="customers/edit.html", context={"customer": customer}
    )


# -------------------------------
# Update Customer
# -------------------------------


@router.post("/customers/{customer_id}/edit")
async def update_customer(
    customer_id: int,
    customer_name: str = Form(...),
    contact_person: str = Form(""),
    mobile: str = Form(""),
    email: str = Form(""),
    gstin: str = Form(""),
    address1: str = Form(""),
    address2: str = Form(""),
    city: str = Form(""),
    state: str = Form(""),
    pincode: str = Form(""),
    credit_limit: float = Form(0),
    opening_balance: float = Form(0),
    db: Session = Depends(get_db),
):

    customer = CustomerCreate(
        customer_name=customer_name,
        contact_person=contact_person,
        mobile=mobile,
        email=email if email else None,
        gstin=gstin,
        address1=address1,
        address2=address2,
        city=city,
        state=state,
        pincode=pincode,
        credit_limit=credit_limit,
        opening_balance=opening_balance,
    )

    CustomerService.update(db, customer_id, customer)

    return RedirectResponse("/customers", status_code=303)


# -------------------------------
# Delete Customer
# -------------------------------


@router.get("/customers/{customer_id}/delete")
async def delete_customer(customer_id: int, db: Session = Depends(get_db)):

    CustomerService.delete(db, customer_id)

    return RedirectResponse("/customers", status_code=303)
