from fastapi import APIRouter
from fastapi import Depends
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.inventory.service import InventoryService
from app.auth.dependencies import login_required

from fastapi import Depends

from app.auth.dependencies import login_required

router = APIRouter(dependencies=[Depends(login_required)])


templates = Jinja2Templates(directory="app/templates")


# ----------------------------------------------------
# Inventory Ledger
# ----------------------------------------------------


@router.get("/inventory", response_class=HTMLResponse)
async def inventory_list(
    request: Request, user=Depends(login_required), db: Session = Depends(get_db)
):

    # ------------------------------------
    # Redirect to Login if session expired
    # ------------------------------------

    if isinstance(user, RedirectResponse):

        return user

    stocks = InventoryService.get_all(db)

    return templates.TemplateResponse(
        request=request, name="inventory/list.html", context={"stocks": stocks}
    )


# ----------------------------------------------------
# Current Stock
# ----------------------------------------------------


@router.get("/inventory/current-stock", response_class=HTMLResponse)
async def current_stock(request: Request, db: Session = Depends(get_db)):

    products = InventoryService.get_current_stock(db)

    return templates.TemplateResponse(
        request=request,
        name="inventory/current_stock.html",
        context={"products": products},
    )


# ----------------------------------------------------
# Low Stock Report
# ----------------------------------------------------


@router.get("/inventory/low-stock", response_class=HTMLResponse)
async def low_stock(request: Request, db: Session = Depends(get_db)):

    products = InventoryService.get_low_stock(db)

    return templates.TemplateResponse(
        request=request,
        name="inventory/current_stock.html",
        context={"products": products, "page_title": "Low Stock Report"},
    )


# ----------------------------------------------------
# Inventory Dashboard
# ----------------------------------------------------


@router.get("/inventory/dashboard", response_class=HTMLResponse)
async def inventory_dashboard(request: Request, db: Session = Depends(get_db)):

    products = InventoryService.get_current_stock(db)

    low_stock = InventoryService.get_low_stock(db)

    total_products = len(products)

    out_of_stock = len([p for p in products if float(p.current_stock or 0) <= 0])

    return templates.TemplateResponse(
        request=request,
        name="inventory/dashboard.html",
        context={
            "products": products,
            "total_products": total_products,
            "low_stock_count": len(low_stock),
            "out_of_stock": out_of_stock,
        },
    )
