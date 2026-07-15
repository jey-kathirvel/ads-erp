from sqlalchemy import func

from fastapi import APIRouter
from fastapi import Depends
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.config.database import get_db

from app.customers.models import Customer
from app.products.models import Product
from app.billing.models import Invoice
from app.inventory.models import StockTransaction
from app.custom_gst.models import CustomGSTInvoice
from app.finance_tools.models import FinanceExpense, FinanceIncome
from app.hrm.models import Employee
from app.incidents.models import Incident

from app.auth.dependencies import login_required


from fastapi import Depends

from app.auth.dependencies import login_required

router = APIRouter(dependencies=[Depends(login_required)])

templates = Jinja2Templates(directory="app/templates")


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(
    request: Request, user=Depends(login_required), db: Session = Depends(get_db)
):

    # ------------------------------------
    # Redirect to Login if session expired
    # ------------------------------------

    if isinstance(user, RedirectResponse):

        return user

    # ------------------------------------
    # Dashboard Counts
    # ------------------------------------

    customer_count = db.query(Customer).count()

    product_count = db.query(Product).count()

    invoice_count = db.query(Invoice).count()

    low_stock = (
        db.query(Product).filter(Product.current_stock <= Product.minimum_stock).count()
    )

    out_of_stock = db.query(Product).filter(Product.current_stock <= 0).count()

    # ------------------------------------
    # Inventory Value
    # ------------------------------------

    inventory_value = (
        db.query(func.sum(Product.current_stock * Product.purchase_price)).scalar()
    ) or 0

    # ------------------------------------
    # Recent Invoices
    # ------------------------------------

    recent_invoices = db.query(Invoice).order_by(Invoice.id.desc()).limit(10).all()

    # ------------------------------------
    # Recent Stock Transactions
    # ------------------------------------

    recent_transactions = (
        db.query(StockTransaction).order_by(StockTransaction.id.desc()).limit(10).all()
    )

    # ------------------------------------
    # Current Stock Quantity
    # ------------------------------------

    total_stock_qty = (db.query(func.sum(Product.current_stock)).scalar()) or 0

    # ------------------------------------
    # Migrated Tools Snapshot
    # ------------------------------------

    employee_count = db.query(Employee).filter(Employee.is_active.is_(True)).count()
    open_incidents = db.query(Incident).filter(Incident.status.notin_(["Closed", "Resolved"])).count()
    custom_gst_count = db.query(CustomGSTInvoice).count()
    finance_income = db.query(func.coalesce(func.sum(FinanceIncome.amount), 0)).filter(FinanceIncome.is_active.is_(True)).scalar()
    finance_expense = db.query(func.coalesce(func.sum(FinanceExpense.total_amount), 0)).filter(FinanceExpense.is_active.is_(True)).scalar()

    activity_values = [invoice_count, custom_gst_count, employee_count, open_incidents]
    activity_peak = max(activity_values + [1])
    activity_bars = [max(8, round(value / activity_peak * 100)) if value else 4 for value in activity_values]

    return templates.TemplateResponse(
        request=request,
        name="dashboard/index.html",
        context={
            "customer_count": customer_count,
            "product_count": product_count,
            "invoice_count": invoice_count,
            "low_stock": low_stock,
            "out_of_stock": out_of_stock,
            "inventory_value": float(inventory_value),
            "total_stock_qty": float(total_stock_qty),
            "recent_invoices": recent_invoices,
            "recent_transactions": recent_transactions,
            "employee_count": employee_count,
            "open_incidents": open_incidents,
            "custom_gst_count": custom_gst_count,
            "finance_income": float(finance_income or 0),
            "finance_expense": float(finance_expense or 0),
            "finance_balance": float((finance_income or 0) - (finance_expense or 0)),
            "activity_bars": activity_bars,
            "user": user,
        },
    )
