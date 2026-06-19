from fastapi import APIRouter
from fastapi import Depends
from fastapi import Form
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.config.database import get_db

from app.accounts.schemas import AccountCreate
from app.accounts.service import AccountService
from app.accounts.service import LedgerService
from app.auth.dependencies import login_required

router = APIRouter()

templates = Jinja2Templates(
    directory="app/templates"
)


# ----------------------------------------------------
# Chart Of Accounts
# ----------------------------------------------------

@router.get(
    "/accounts",
    response_class=HTMLResponse
)
async def account_list(

    request: Request,

    user=Depends(login_required),

    db: Session = Depends(get_db)

):

    # ------------------------------------
    # Redirect to Login if session expired
    # ------------------------------------

    if isinstance(user, RedirectResponse):

        return user

    accounts = AccountService.get_all(db)

    return templates.TemplateResponse(

        request=request,

        name="accounts/list.html",

        context={

            "accounts": accounts

        }

    )


# ----------------------------------------------------
# Create Account Page
# ----------------------------------------------------

@router.get(
    "/accounts/create",
    response_class=HTMLResponse
)
async def create_account_page(

    request: Request

):

    return templates.TemplateResponse(

        request=request,

        name="accounts/create.html"

    )


# ----------------------------------------------------
# Save Account
# ----------------------------------------------------

@router.post("/accounts/create")
async def create_account(

    account_name: str = Form(...),

    account_group: str = Form(...),

    opening_balance: float = Form(0),

    db: Session = Depends(get_db)

):

    account = AccountCreate(

        account_name=account_name,

        account_group=account_group,

        opening_balance=opening_balance

    )

    AccountService.create(

        db,

        account

    )

    return RedirectResponse(

        "/accounts",

        status_code=303

    )


# ----------------------------------------------------
# Ledger
# ----------------------------------------------------

@router.get(
    "/accounts/{account_id}/ledger",
    response_class=HTMLResponse
)
async def ledger(

    account_id: int,

    request: Request,

    db: Session = Depends(get_db)

):

    account = AccountService.get_by_id(

        db,

        account_id

    )

    entries = LedgerService.get_account_entries(

        db,

        account_id

    )

    return templates.TemplateResponse(

        request=request,

        name="accounts/ledger.html",

        context={

            "account": account,

            "entries": entries

        }

    )
