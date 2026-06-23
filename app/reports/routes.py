from fastapi.responses import Response

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate
from reportlab.platypus import Table
from reportlab.platypus import TableStyle
from reportlab.platypus import Paragraph
from reportlab.platypus import Spacer
from app.suppliers.models import Supplier
from reportlab.lib.styles import getSampleStyleSheet

from io import BytesIO
from fastapi import APIRouter
from fastapi import Depends
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.config.database import get_db

from app.billing.service import BillingService
from io import BytesIO

from fastapi.responses import Response

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image,
)

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from app.purchase.service import PurchaseService
from app.inventory.service import InventoryService
from app.customers.models import Customer

from datetime import datetime

from app.auth.dependencies import login_required

router = APIRouter(
    dependencies=[Depends(login_required)]
)

templates = Jinja2Templates(
    directory="app/templates"
)

# --------------------------------------------------
# Sales Report
# --------------------------------------------------
def add_page_number(canvas, doc):

    canvas.saveState()

    canvas.setFont(
        "DejaVuSans",
        9
    )

    canvas.drawRightString(
        800,
        20,
        f"Page {canvas.getPageNumber()}"
    )

    canvas.restoreState()
@router.get(
    "/reports/sales",
    response_class=HTMLResponse
)
async def sales_report(
    request: Request,
    customer_id: str = "",
    from_date: str = "",
    to_date: str = "",
    user=Depends(login_required),
    db: Session = Depends(get_db),
):

    if isinstance(user, RedirectResponse):
        return user

    invoices = BillingService.get_all(db)

    # -------------------------------
    # Date Filters
    # -------------------------------

    if from_date:

        from_dt = datetime.strptime(
            from_date,
            "%Y-%m-%d"
        ).date()

        invoices = [
            invoice
            for invoice in invoices
            if invoice.invoice_date >= from_dt
        ]

    if to_date:

        to_dt = datetime.strptime(
            to_date,
            "%Y-%m-%d"
        ).date()

        invoices = [
            invoice
            for invoice in invoices
            if invoice.invoice_date <= to_dt
        ]

    # -------------------------------
    # Customer Filter
    # -------------------------------

    selected_customer_id = None

    if customer_id and customer_id.isdigit():

        selected_customer_id = int(customer_id)

        invoices = [
            invoice
            for invoice in invoices
            if invoice.customer_id == selected_customer_id
        ]

    # -------------------------------
    # Summary
    # -------------------------------

    total_sales = sum(
        float(invoice.grand_total or 0)
        for invoice in invoices
    )

    total_invoices = len(invoices)

    avg_invoice = (
        total_sales / total_invoices
        if total_invoices else 0
    )

    customers = (
        db.query(Customer)
        .order_by(Customer.customer_name)
        .all()
    )

    return templates.TemplateResponse(
        request=request,
        name="reports/sales.html",
        context={
            "invoices": invoices,
            "customers": customers,
            "customer_id": selected_customer_id,
            "from_date": from_date,
            "to_date": to_date,
            "total_sales": total_sales,
            "total_invoices": total_invoices,
            "avg_invoice": avg_invoice,
        },
    )


# --------------------------------------------------
# Sales Report PDF
# --------------------------------------------------

@router.get("/reports/sales/pdf")
async def sales_report_pdf(
    customer_id: str = "",
    from_date: str = "",
    to_date: str = "",
    db: Session = Depends(get_db),
):

    pdfmetrics.registerFont(
        TTFont(
            "DejaVuSans",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
        )
    )

    invoices = BillingService.get_all(db)

    # -------------------------
    # Date Filters
    # -------------------------

    if from_date:

        from_dt = datetime.strptime(
            from_date,
            "%Y-%m-%d"
        ).date()

        invoices = [
            x for x in invoices
            if x.invoice_date >= from_dt
        ]

    if to_date:

        to_dt = datetime.strptime(
            to_date,
            "%Y-%m-%d"
        ).date()

        invoices = [
            x for x in invoices
            if x.invoice_date <= to_dt
        ]

    # -------------------------
    # Customer Filter
    # -------------------------

    customer_name = "All Customers"

    if customer_id and customer_id.isdigit():

        customer_id_int = int(customer_id)

        invoices = [
            x for x in invoices
            if x.customer_id == customer_id_int
        ]

        customer = (
            db.query(Customer)
            .filter(Customer.id == customer_id_int)
            .first()
        )

        if customer:
            customer_name = customer.customer_name

    total_sales = sum(
        float(x.grand_total or 0)
        for x in invoices
    )

    # -------------------------
    # PDF
    # -------------------------

    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        leftMargin=20,
        rightMargin=20,
        topMargin=20,
        bottomMargin=30,
    )

    styles = getSampleStyleSheet()

    elements = []

    # -------------------------
    # Logo
    # -------------------------

    try:

        logo = Image(
            "app/static/uploads/logo/logo.png",
            width=60,
            height=60
        )

        elements.append(logo)

    except Exception:
        pass

    # -------------------------
    # Company Header
    # -------------------------

    elements.append(
        Paragraph(
            "<b>ADS ERP</b>",
            styles["Title"]
        )
    )

    elements.append(
        Paragraph(
            "Sales Report",
            styles["Title"]
        )
    )

    elements.append(
        Spacer(1, 10)
    )

    # -------------------------
    # Filters Table
    # -------------------------

    filter_data = [
        ["From Date", from_date or "-"],
        ["To Date", to_date or "-"],
        ["Customer", customer_name],
        [
            "Generated On",
            datetime.now().strftime(
                "%d-%m-%Y %I:%M %p"
            ),
        ],
    ]

    filter_table = Table(
        filter_data,
        colWidths=[120, 300]
    )

    filter_table.setStyle(
        TableStyle([
            ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ("FONTNAME", (0, 0), (-1, -1), "DejaVuSans"),
            ("BACKGROUND", (0, 0), (0, -1),
             colors.lightgrey),
        ])
    )

    elements.append(filter_table)

    elements.append(
        Spacer(1, 20)
    )

    # -------------------------
    # Sales Table
    # -------------------------

    data = [[
        "Invoice No",
        "Date",
        "Customer",
        "Status",
        "Amount (₹)"
    ]]

    for invoice in invoices:

        data.append([
            invoice.invoice_no,
            invoice.invoice_date.strftime(
                "%d-%m-%Y"
            ),
            (
                invoice.customer.customer_name
                if invoice.customer
                else "-"
            ),
            invoice.payment_status,
            f"Rs. {float(invoice.grand_total):,.2f}",
        ])

    data.append([
        "",
        "",
        "",
        "GRAND TOTAL",
        f"Rs. {total_sales:,.2f}"
    ])

    table = Table(
        data,
        colWidths=[
            120,
            120,
            250,
            120,
            120,
        ]
    )

    table.setStyle(
        TableStyle([

            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                colors.HexColor("#0d3b66")
            ),

            (
                "TEXTCOLOR",
                (0, 0),
                (-1, 0),
                colors.white
            ),

            (
                "FONTNAME",
                (0, 0),
                (-1, -1),
                "DejaVuSans"
            ),

            (
                "GRID",
                (0, 0),
                (-1, -1),
                1,
                colors.black
            ),

            (
                "BACKGROUND",
                (0, -1),
                (-1, -1),
                colors.HexColor("#f2f2f2")
            ),

            (
                "FONTNAME",
                (0, -1),
                (-1, -1),
                "DejaVuSans"
            ),

        ])
    )

    elements.append(table)

    elements.append(
        Spacer(1, 20)
    )

    # -------------------------
    # Footer
    # -------------------------

    elements.append(
        Paragraph(
            f"<b>Total Sales :</b> Rs. {total_sales:,.2f}",
            styles["Heading3"]
        )
    )
#test
    elements.append(
        Paragraph(
            "Generated by ADS ERP",
            styles["Normal"]
        )
    )

    doc.build(
        elements,
        onFirstPage=add_page_number,
        onLaterPages=add_page_number,
    )

    pdf = buffer.getvalue()

    buffer.close()

    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={
            "Content-Disposition":
            "inline; filename=sales_report.pdf"
        },
    )
@router.get("/reports/purchase/pdf")
async def purchase_report_pdf(
    supplier_id: str = "",
    from_date: str = "",
    to_date: str = "",
    db: Session = Depends(get_db),
):

    from app.purchase.models import Purchase

    purchases = PurchaseService.get_all(db)

    if from_date:
        from_dt = datetime.strptime(
            from_date,
            "%Y-%m-%d"
        ).date()

        purchases = [
            p for p in purchases
            if p.purchase_date >= from_dt
        ]

    if to_date:
        to_dt = datetime.strptime(
            to_date,
            "%Y-%m-%d"
        ).date()

        purchases = [
            p for p in purchases
            if p.purchase_date <= to_dt
        ]

    if supplier_id:
        purchases = [
            p for p in purchases
            if str(p.supplier_id) == supplier_id
        ]

    total_purchase = sum(
        float(p.grand_total or 0)
        for p in purchases
    )

    supplier_name = "All Suppliers"

    if supplier_id:

        supplier = (
            db.query(Supplier)
            .filter(Supplier.id == int(supplier_id))
            .first()
        )

        if supplier:
            supplier_name = supplier.supplier_name

    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        leftMargin=20,
        rightMargin=20,
        topMargin=20,
        bottomMargin=20,
    )

    styles = getSampleStyleSheet()

    elements = []

    logo_path = "app/static/uploads/logo/logo.png"

    try:

        logo = Image(
            logo_path,
            width=50,
            height=50
        )

        logo.hAlign = "CENTER"

        elements.append(logo)

    except:
        pass

    title = Paragraph(
        "<b>ADS ERP</b>",
        styles["Title"]
    )

    elements.append(title)

    elements.append(
        Spacer(1, 10)
    )

    report_title = Paragraph(
        "<b>Purchase Report</b>",
        styles["Heading1"]
    )

    elements.append(report_title)

    elements.append(
        Spacer(1, 10)
    )

    generated_on = datetime.now().strftime(
        "%d-%m-%Y %I:%M %p"
    )

    filter_data = [
        ["From Date", from_date or "-"],
        ["To Date", to_date or "-"],
        ["Supplier", supplier_name],
        ["Generated On", generated_on],
    ]

    filter_table = Table(
        filter_data,
        colWidths=[140, 350]
    )

    filter_table.setStyle(
        TableStyle([
            ("GRID", (0,0), (-1,-1), 1, colors.black),
            ("FONTNAME", (0,0), (0,-1), "Helvetica-Bold"),
        ])
    )

    elements.append(filter_table)

    elements.append(
        Spacer(1, 20)
    )

    table_data = [[
        "Purchase No",
        "Date",
        "Supplier",
        "Payment Mode",
        "Amount (₹)"
    ]]

    for purchase in purchases:

        table_data.append([
            purchase.purchase_no,
            purchase.purchase_date.strftime("%d-%m-%Y"),
            purchase.supplier.supplier_name
            if purchase.supplier else "-",
            purchase.payment_mode or "-",
            f"₹ {float(purchase.grand_total):,.2f}"
        ])

    table_data.append([
        "",
        "",
        "",
        "GRAND TOTAL",
        f"₹ {total_purchase:,.2f}"
    ])

    report_table = Table(
        table_data,
        colWidths=[120, 120, 250, 120, 120]
    )

    report_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#15406A")),
            ("TEXTCOLOR", (0,0), (-1,0), colors.white),
            ("GRID", (0,0), (-1,-1), 1, colors.black),
            ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
            ("FONTNAME", (3,-1), (4,-1), "Helvetica-Bold"),
        ])
    )

    elements.append(report_table)

    elements.append(
        Spacer(1, 20)
    )

    elements.append(
        Paragraph(
            f"<b>Total Purchase : ₹ {total_purchase:,.2f}</b>",
            styles["Heading2"]
        )
    )

    elements.append(
        Paragraph(
            "Generated by ADS ERP",
            styles["Normal"]
        )
    )

    doc.build(elements)

    pdf = buffer.getvalue()

    buffer.close()

    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={
            "Content-Disposition":
            "inline; filename=purchase_report.pdf"
        },
    )
# --------------------------------------------------
# Purchase Report
# --------------------------------------------------

@router.get(
    "/reports/purchase",
    response_class=HTMLResponse
)
async def purchase_report(
    request: Request,
    supplier_id: str = "",
    from_date: str = "",
    to_date: str = "",
    db: Session = Depends(get_db),
):

    from app.purchase.models import Purchase
    from app.suppliers.models import Supplier

    purchases = PurchaseService.get_all(db)

    if from_date:
        from_dt = datetime.strptime(
            from_date,
            "%Y-%m-%d"
        ).date()

        purchases = [
            p for p in purchases
            if p.purchase_date >= from_dt
        ]

    if to_date:
        to_dt = datetime.strptime(
            to_date,
            "%Y-%m-%d"
        ).date()

        purchases = [
            p for p in purchases
            if p.purchase_date <= to_dt
        ]

    if supplier_id:
        purchases = [
            p for p in purchases
            if str(p.supplier_id) == supplier_id
        ]

    total_purchase = sum(
        float(p.grand_total or 0)
        for p in purchases
    )

    total_bills = len(purchases)

    avg_purchase = (
        total_purchase / total_bills
        if total_bills else 0
    )

    suppliers = (
        db.query(Supplier)
        .order_by(Supplier.supplier_name)
        .all()
    )

    return templates.TemplateResponse(
        request=request,
        name="reports/purchase.html",
        context={
            "purchases": purchases,
            "suppliers": suppliers,
            "supplier_id": supplier_id,
            "from_date": from_date,
            "to_date": to_date,
            "total_purchase": total_purchase,
            "total_bills": total_bills,
            "avg_purchase": avg_purchase,
        }
    )


# --------------------------------------------------
# Inventory Report
# --------------------------------------------------

@router.get(
    "/reports/inventory",
    response_class=HTMLResponse
)
async def inventory_report(
    request: Request,
    db: Session = Depends(get_db),
):

    products = InventoryService.get_current_stock(db)

    return templates.TemplateResponse(
        request=request,
        name="reports/inventory.html",
        context={
            "products": products
        }
    )