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
from app.users.routes import router as users_router
from app.roles.routes import router as roles_router
from app.permissions.routes import router as permission_router
from app.settings.routes import router as settings_router
from app.booking.routes import router as booking_router
from app.hrm.routes import router as hrm_router
from app.custom_gst.routes import router as custom_gst_router
from app.incidents.routes import router as incidents_router
from app.finance_tools.routes import router as finance_tools_router

api_router = APIRouter()

# Dashboard
api_router.include_router(dashboard_router, tags=["Dashboard"])

# Customers
api_router.include_router(customer_router, tags=["Customers"])

# Products
api_router.include_router(product_router, tags=["Products"])

# Categories
api_router.include_router(category_router, tags=["Categories"])

# Billing
api_router.include_router(billing_router, tags=["Billing"])

# Inventory
api_router.include_router(inventory_router, tags=["Inventory"])

# Suppliers
api_router.include_router(supplier_router, tags=["Suppliers"])

# Purchase
api_router.include_router(purchase_router, tags=["Purchase"])


# Accounts
api_router.include_router(accounts_router, tags=["Accounts"])

# Supplier Payments
api_router.include_router(supplier_payment_router, tags=["Supplier Payments"])

# Company
api_router.include_router(company_router, tags=["Company"])

# Settings
api_router.include_router(settings_router, tags=["Settings"])

# Authentication
api_router.include_router(auth_router, tags=["Authentication"])

# Users
api_router.include_router(users_router, tags=["Users"])

# Roles
api_router.include_router(roles_router, tags=["Roles"])

# Permissions
api_router.include_router(permission_router, tags=["Permissions"])

# Booking
api_router.include_router(booking_router, tags=["Booking"])

# Human Resources
api_router.include_router(hrm_router, tags=["HRM"])

# Custom GST Billing
api_router.include_router(custom_gst_router, tags=["Custom GST Billing"])

# Incidents Tracking
api_router.include_router(incidents_router, tags=["Incidents Tracking"])

# Credit & Debit Finance
api_router.include_router(finance_tools_router, tags=["Credit & Debit"])

# Reports
api_router.include_router(reports_router, tags=["Reports"])
