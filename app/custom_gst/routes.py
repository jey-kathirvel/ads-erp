import csv
import io
from datetime import date
from decimal import Decimal, ROUND_HALF_UP

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response, StreamingResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.auth.dependencies import login_required
from app.config.database import get_db
from app.custom_gst.models import CustomGSTInvoice

router = APIRouter(prefix="/custom-gst", dependencies=[Depends(login_required)])
templates = Jinja2Templates(directory="app/templates")
MONEY = Decimal("0.01")


def money(value) -> Decimal:
    return Decimal(str(value or 0)).quantize(MONEY, rounding=ROUND_HALF_UP)


def invoice_or_404(db: Session, invoice_id: int) -> CustomGSTInvoice:
    invoice = db.get(CustomGSTInvoice, invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return invoice


def date_range(query, from_date: date | None, to_date: date | None):
    if from_date:
        query = query.filter(func.date(CustomGSTInvoice.created_at) >= from_date)
    if to_date:
        query = query.filter(func.date(CustomGSTInvoice.created_at) <= to_date)
    return query


@router.get("", response_class=HTMLResponse)
async def dashboard(request: Request, db: Session = Depends(get_db)):
    total_invoices, total_revenue = db.query(
        func.count(CustomGSTInvoice.id), func.coalesce(func.sum(CustomGSTInvoice.total_amount), 0)
    ).one()
    recent = db.query(CustomGSTInvoice).order_by(CustomGSTInvoice.id.desc()).limit(10).all()
    return templates.TemplateResponse(request=request, name="custom_gst/dashboard.html", context={
        "total_invoices": total_invoices, "total_revenue": total_revenue, "invoices": recent,
    })


@router.get("/new", response_class=HTMLResponse)
async def new_invoice(request: Request, db: Session = Depends(get_db)):
    last_id = db.query(func.max(CustomGSTInvoice.id)).scalar() or 0
    invoice_no = f"ARS-{date.today().year}-{last_id + 1:04d}"
    return templates.TemplateResponse(request=request, name="custom_gst/form.html", context={"invoice_no": invoice_no})


@router.post("/save")
async def save_invoice(
    invoice_no: str = Form(...), customer_name: str = Form(...), mobile: str = Form(""),
    customer_address: str = Form(""), customer_gstin: str = Form(""), room_type: str = Form(...),
    checkin_date: date = Form(...), checkout_date: date = Form(...), room_charge: Decimal = Form(0),
    extra_charge: Decimal = Form(0), gst_percent: Decimal = Form(0), db: Session = Depends(get_db),
):
    if checkout_date < checkin_date:
        return RedirectResponse("/custom-gst/new?error=dates", status_code=303)
    subtotal = money(room_charge) + money(extra_charge)
    gst_amount = money(subtotal * money(gst_percent) / Decimal("100"))
    invoice = CustomGSTInvoice(
        invoice_no=invoice_no.strip(), customer_name=customer_name.strip(), mobile=mobile.strip() or None,
        customer_address=customer_address.strip() or None, customer_gstin=customer_gstin.strip().upper() or None,
        room_type=room_type.strip(), checkin_date=checkin_date, checkout_date=checkout_date,
        room_charge=money(room_charge), extra_charge=money(extra_charge), gst_percent=money(gst_percent),
        gst_amount=gst_amount, total_amount=money(subtotal + gst_amount),
    )
    db.add(invoice)
    db.commit()
    db.refresh(invoice)
    return RedirectResponse(f"/custom-gst/invoices/{invoice.id}", status_code=303)


@router.get("/invoices", response_class=HTMLResponse)
async def invoices(request: Request, search: str = "", db: Session = Depends(get_db)):
    query = db.query(CustomGSTInvoice)
    if search.strip():
        term = f"%{search.strip()}%"
        query = query.filter(or_(CustomGSTInvoice.customer_name.ilike(term), CustomGSTInvoice.mobile.ilike(term), CustomGSTInvoice.invoice_no.ilike(term)))
    rows = query.order_by(CustomGSTInvoice.id.desc()).all()
    return templates.TemplateResponse(request=request, name="custom_gst/invoices.html", context={"invoices": rows, "search": search})


@router.get("/invoices/{invoice_id}", response_class=HTMLResponse)
async def view_invoice(invoice_id: int, request: Request, db: Session = Depends(get_db)):
    invoice = invoice_or_404(db, invoice_id)
    nights = max(1, (invoice.checkout_date - invoice.checkin_date).days)
    return templates.TemplateResponse(request=request, name="custom_gst/view.html", context={"invoice": invoice, "nights": nights})


@router.post("/invoices/{invoice_id}/delete")
async def delete_invoice(invoice_id: int, db: Session = Depends(get_db)):
    db.delete(invoice_or_404(db, invoice_id))
    db.commit()
    return RedirectResponse("/custom-gst/invoices", status_code=303)


@router.get("/reports", response_class=HTMLResponse)
async def reports(request: Request, from_date: date | None = None, to_date: date | None = None, db: Session = Depends(get_db)):
    today = date.today()
    today_query = db.query(CustomGSTInvoice).filter(func.date(CustomGSTInvoice.created_at) == today)
    month_query = db.query(CustomGSTInvoice).filter(func.extract("month", CustomGSTInvoice.created_at) == today.month, func.extract("year", CustomGSTInvoice.created_at) == today.year)
    room_revenue = db.query(CustomGSTInvoice.room_type, func.count(CustomGSTInvoice.id), func.sum(CustomGSTInvoice.total_amount)).group_by(CustomGSTInvoice.room_type).order_by(func.sum(CustomGSTInvoice.total_amount).desc()).all()
    report_rows = []
    if from_date or to_date:
        report_rows = date_range(db.query(CustomGSTInvoice), from_date, to_date).order_by(CustomGSTInvoice.created_at.desc()).all()
    return templates.TemplateResponse(request=request, name="custom_gst/reports.html", context={
        "today_revenue": sum((x.total_amount for x in today_query.all()), Decimal(0)),
        "month_revenue": sum((x.total_amount for x in month_query.all()), Decimal(0)),
        "gst_collected": db.query(func.coalesce(func.sum(CustomGSTInvoice.gst_amount), 0)).scalar(),
        "today_invoices": today_query.count(), "month_invoices": month_query.count(),
        "room_revenue": room_revenue, "report_rows": report_rows, "from_date": from_date, "to_date": to_date,
    })


@router.get("/reports/csv")
async def export_csv(from_date: date | None = None, to_date: date | None = None, db: Session = Depends(get_db)):
    rows = date_range(db.query(CustomGSTInvoice), from_date, to_date).order_by(CustomGSTInvoice.created_at.desc()).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Invoice No", "Date", "Guest", "Room Type", "GST Amount", "Total Amount"])
    for row in rows:
        writer.writerow([row.invoice_no, row.created_at.strftime("%d-%m-%Y"), row.customer_name, row.room_type, row.gst_amount, row.total_amount])
    return Response(content="\ufeff" + output.getvalue(), media_type="text/csv", headers={"Content-Disposition": 'attachment; filename="custom_gst_report.csv"'})


@router.get("/invoices/{invoice_id}/pdf")
async def invoice_pdf(invoice_id: int, db: Session = Depends(get_db)):
    invoice = invoice_or_404(db, invoice_id)
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
    except ImportError as exc:
        raise HTTPException(status_code=503, detail="PDF support is not installed") from exc
    stream = io.BytesIO()
    pdf = canvas.Canvas(stream, pagesize=A4)
    width, height = A4
    y = height - 55
    pdf.setTitle(invoice.invoice_no)
    pdf.setFont("Helvetica-Bold", 20); pdf.drawCentredString(width / 2, y, "AKSHAT ROYAL STAY"); y -= 22
    pdf.setFont("Helvetica-Bold", 13); pdf.drawCentredString(width / 2, y, "GST TAX INVOICE"); y -= 18
    pdf.setFont("Helvetica", 9); pdf.drawCentredString(width / 2, y, "82, Kamaraj Bazaar, Bodinayakanur, Theni District, Tamil Nadu - 625513"); y -= 14
    pdf.drawCentredString(width / 2, y, "GSTIN: 33AIMPJ3818M1ZZ"); y -= 30
    lines = [
        ("Invoice No", invoice.invoice_no), ("Invoice Date", invoice.created_at.strftime("%d-%m-%Y")),
        ("Guest Name", invoice.customer_name), ("Mobile", invoice.mobile or "-"),
        ("Customer GSTIN", invoice.customer_gstin or "-"), ("Stay", f"{invoice.checkin_date:%d-%m-%Y} to {invoice.checkout_date:%d-%m-%Y}"),
        ("Room Type", invoice.room_type), ("Room Charges", f"INR {invoice.room_charge:,.2f}"),
        ("Additional Charges", f"INR {invoice.extra_charge:,.2f}"), ("CGST", f"INR {invoice.gst_amount / 2:,.2f}"),
        ("SGST", f"INR {invoice.gst_amount / 2:,.2f}"), ("GRAND TOTAL", f"INR {invoice.total_amount:,.2f}"),
    ]
    for label, value in lines:
        pdf.setFont("Helvetica-Bold", 10); pdf.drawString(55, y, f"{label}:")
        pdf.setFont("Helvetica", 10); pdf.drawString(175, y, str(value)); y -= 22
    pdf.setFont("Helvetica", 9); pdf.drawCentredString(width / 2, 65, "Thank you for staying at Akshat Royal Stay.")
    pdf.save(); stream.seek(0)
    return StreamingResponse(stream, media_type="application/pdf", headers={"Content-Disposition": f'attachment; filename="{invoice.invoice_no}.pdf"'})
