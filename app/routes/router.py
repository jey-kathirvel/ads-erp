from fastapi import APIRouter

from app.dashboard.routes import router as dashboard_router
from app.customers.routes import router as customer_router
from app.products.routes import router as product_router
from app.categories.routes import router as category_router
from app.billing.routes import router as billing_router
from app.inventory.routes import router as inventory_router
from app.suppliers.routes import router as supplier_router
from app.purchase.routes import router as purchase_router
from app.reports.routes import router as reports_router
from app.accounts.routes import router as accounts_router
from app.supplier_payments.routes import router as supplier_payment_router
from app.company.routes import router as company_router
from app.auth.routes import router as auth_router


api_router = APIRouter()

# Dashboard
api_router.include_router(
    dashboard_router,
    tags=["Dashboard"]
)

# Customers
api_router.include_router(
    customer_router,
    tags=["Customers"]
)

# Products
api_router.include_router(
    product_router,
    tags=["Products"]
)

# Categories
api_router.include_router(
    category_router,
    tags=["Categories"]
)

# Billing
api_router.include_router(
    billing_router,
    tags=["Billing"]
)

# Inventory
api_router.include_router(
    inventory_router,
    tags=["Inventory"]
)

# Suppliers
api_router.include_router(
    supplier_router,
    tags=["Suppliers"]
)

#Purchase
api_router.include_router(

    purchase_router,

    tags=["Purchase"]

)

#Reports
api_router.include_router(

    reports_router,

    tags=["Reports"]

)
#Accounts
api_router.include_router(

    accounts_router,

    tags=["Accounts"]

)
#SupplierPayments
api_router.include_router(

    supplier_payment_router,

    tags=["Supplier Payments"]

)
#company
api_router.include_router(

    company_router,

    tags=["Company"]

)
#Authentication
api_router.include_router(

    auth_router,

    tags=["Authentication"]

)
