import csv, io, json
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response, StreamingResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import func, or_
from sqlalchemy.orm import Session
from app.auth.dependencies import login_required
from app.booking.models import Booking, BookingPayment, RoomType
from app.config.database import get_db
from app.custom_gst.email_service import send_invoice_email
from app.custom_gst.models import CustomGSTInvoice
from app.custom_gst.pdf_service import build_invoice_pdf

router=APIRouter(prefix="/custom-gst",dependencies=[Depends(login_required)])
templates=Jinja2Templates(directory="app/templates"); MONEY=Decimal("0.01")
def money(v): return Decimal(str(v or 0)).quantize(MONEY,rounding=ROUND_HALF_UP)
def invoice_totals(room_charge, extra_charge, discount, gst_percent, amount_paid):
    taxable=max(Decimal(0),money(room_charge)+money(extra_charge)-money(discount))
    gst=money(taxable*money(gst_percent)/100)
    total=money(taxable+gst)
    paid=min(max(Decimal(0),money(amount_paid)),total)
    return taxable,gst,total,paid,money(total-paid)
def invoice_or_404(db,id):
    row=db.get(CustomGSTInvoice,id)
    if not row: raise HTTPException(404,"Invoice not found")
    return row
def next_invoice_no(db):
    today=date.today(); fy_start=today.year if today.month>=4 else today.year-1; prefix=f"ARS/{fy_start}-{str(fy_start+1)[-2:]}/"; last=db.query(CustomGSTInvoice).filter(CustomGSTInvoice.invoice_no.like(prefix+"%" )).order_by(CustomGSTInvoice.id.desc()).first(); seq=int(last.invoice_no.rsplit("/",1)[-1])+1 if last else 1; return f"{prefix}{seq:04d}"
def date_range(q,frm,to):
    if frm:q=q.filter(CustomGSTInvoice.invoice_date>=frm)
    if to:q=q.filter(CustomGSTInvoice.invoice_date<=to)
    return q

@router.get("",response_class=HTMLResponse)
async def dashboard(request:Request,db:Session=Depends(get_db)):
    count,total=db.query(func.count(CustomGSTInvoice.id),func.coalesce(func.sum(CustomGSTInvoice.total_amount),0)).one(); recent=db.query(CustomGSTInvoice).order_by(CustomGSTInvoice.id.desc()).limit(10).all(); return templates.TemplateResponse(request=request,name="custom_gst/dashboard.html",context={"total_invoices":count,"total_revenue":total,"invoices":recent})

@router.get("/api/booking-lookup")
async def booking_lookup(q:str,db:Session=Depends(get_db)):
    term=q.strip()
    if len(term)<5: raise HTTPException(400,"Enter a 10-digit mobile number or last 5 booking characters")
    query=db.query(Booking).filter(Booking.status.in_(("CONFIRMED","CHECKED_IN","CHECKED_OUT")))
    if term.isdigit() and len(term)>=10: query=query.filter(Booking.mobile==term[-10:])
    else: query=query.filter(Booking.booking_no.ilike(f"%{term[-5:]}"))
    b=query.order_by(Booking.created_at.desc(),Booking.id.desc()).first()
    if not b: raise HTTPException(404,"No confirmed booking found")
    rt=db.get(RoomType,b.room_type_id); pay=db.query(BookingPayment).filter(BookingPayment.booking_id==b.id).order_by(BookingPayment.id.desc()).first()
    return {"booking_id":b.id,"booking_no":b.booking_no,"customer_name":b.guest_name,"mobile":b.mobile or "","customer_email":b.email or "","room_type":rt.name if rt else f"Room type {b.room_type_id}","number_of_rooms":b.number_of_rooms,"checkin_date":b.check_in_at.date().isoformat(),"checkout_date":b.check_out_at.date().isoformat(),"room_charge":float(b.subtotal_amount),"gst_percent":float(b.gst_percent),"amount_paid":float(b.advance_amount),"payment_mode":b.payment_mode or "","payment_reference":pay.provider_payment_id if pay else "","booking_total":float(b.total_amount)}

@router.get("/new",response_class=HTMLResponse)
async def new_invoice(request:Request,db:Session=Depends(get_db)):
    return templates.TemplateResponse(request=request,name="custom_gst/form.html",context={"invoice_no":next_invoice_no(db),"invoice":None,"today":date.today().isoformat()})

@router.post("/save")
async def save_invoice(invoice_no:str=Form(...),invoice_date:date=Form(...),booking_id:int|None=Form(None),booking_no:str=Form(""),customer_name:str=Form(...),mobile:str=Form(""),customer_email:str=Form(""),customer_address:str=Form(""),customer_gstin:str=Form(""),room_type:str=Form(...),number_of_rooms:int=Form(1),checkin_date:date=Form(...),checkout_date:date=Form(...),room_charge:Decimal=Form(0),additional_descriptions:list[str]=Form([]),additional_amounts:list[Decimal]=Form([]),discount_amount:Decimal=Form(0),gst_percent:Decimal=Form(5),payment_mode:str=Form(""),payment_reference:str=Form(""),amount_paid:Decimal=Form(0),notes:str=Form(""),db:Session=Depends(get_db)):
    if checkout_date<checkin_date: raise HTTPException(400,"Check-out cannot be before check-in")
    extra_items=[{"description":d.strip() or "Additional charge","amount":float(money(a))} for d,a in zip(additional_descriptions,additional_amounts) if money(a)>0]
    extra=sum((money(x["amount"]) for x in extra_items),Decimal(0)); taxable,gst,total,paid,balance=invoice_totals(room_charge,extra,discount_amount,gst_percent,amount_paid)
    row=CustomGSTInvoice(booking_id=booking_id,booking_no=booking_no.strip() or None,invoice_no=invoice_no.strip(),invoice_date=invoice_date,customer_name=customer_name.strip(),mobile=mobile.strip() or None,customer_email=customer_email.strip().lower() or None,customer_address=customer_address.strip() or None,customer_gstin=customer_gstin.strip().upper() or None,room_type=room_type.strip(),number_of_rooms=max(1,number_of_rooms),checkin_date=checkin_date,checkout_date=checkout_date,room_charge=money(room_charge),extra_charge=extra,additional_items_json=json.dumps(extra_items),discount_amount=money(discount_amount),gst_percent=money(gst_percent),gst_amount=gst,total_amount=total,payment_mode=payment_mode.strip() or None,payment_reference=payment_reference.strip() or None,amount_paid=paid,balance_amount=balance,notes=notes.strip() or None)
    db.add(row); db.commit(); db.refresh(row); return RedirectResponse(f"/custom-gst/invoices/{row.id}",303)

@router.get("/invoices",response_class=HTMLResponse)
async def invoices(request:Request,search:str="",db:Session=Depends(get_db)):
    q=db.query(CustomGSTInvoice)
    if search.strip():
        t=f"%{search.strip()}%"; q=q.filter(or_(CustomGSTInvoice.customer_name.ilike(t),CustomGSTInvoice.mobile.ilike(t),CustomGSTInvoice.invoice_no.ilike(t),CustomGSTInvoice.booking_no.ilike(t)))
    return templates.TemplateResponse(request=request,name="custom_gst/invoices.html",context={"invoices":q.order_by(CustomGSTInvoice.id.desc()).all(),"search":search})

@router.get("/invoices/{invoice_id}",response_class=HTMLResponse)
async def view_invoice(invoice_id:int,request:Request,db:Session=Depends(get_db)):
    row=invoice_or_404(db,invoice_id); return templates.TemplateResponse(request=request,name="custom_gst/view.html",context={"invoice":row,"items":json.loads(row.additional_items_json or "[]"),"nights":max(1,(row.checkout_date-row.checkin_date).days)})

@router.get("/invoices/{invoice_id}/pdf")
async def invoice_pdf(invoice_id:int,db:Session=Depends(get_db)):
    row=invoice_or_404(db,invoice_id); filename=row.invoice_no.replace("/","-"); return StreamingResponse(io.BytesIO(build_invoice_pdf(row)),media_type="application/pdf",headers={"Content-Disposition":f'attachment; filename="{filename}.pdf"'})

@router.post("/invoices/{invoice_id}/email")
async def email_invoice(invoice_id:int,db:Session=Depends(get_db)):
    row=invoice_or_404(db,invoice_id)
    if not row.customer_email: return RedirectResponse(f"/custom-gst/invoices/{invoice_id}?email=missing",303)
    ok=send_invoice_email(row); return RedirectResponse(f"/custom-gst/invoices/{invoice_id}?email={'sent' if ok else 'failed'}",303)

@router.post("/invoices/{invoice_id}/delete")
async def delete_invoice(invoice_id:int,db:Session=Depends(get_db)):
    db.delete(invoice_or_404(db,invoice_id));db.commit();return RedirectResponse("/custom-gst/invoices",303)

@router.get("/reports",response_class=HTMLResponse)
async def reports(request:Request,from_date:date|None=None,to_date:date|None=None,db:Session=Depends(get_db)):
    rows=date_range(db.query(CustomGSTInvoice),from_date,to_date).order_by(CustomGSTInvoice.id.desc()).all(); today=date.today(); return templates.TemplateResponse(request=request,name="custom_gst/reports.html",context={"today_revenue":sum((x.total_amount for x in rows if x.invoice_date==today),Decimal(0)),"month_revenue":sum((x.total_amount for x in rows if x.invoice_date.month==today.month and x.invoice_date.year==today.year),Decimal(0)),"gst_collected":sum((x.gst_amount for x in rows),Decimal(0)),"today_invoices":sum(1 for x in rows if x.invoice_date==today),"month_invoices":sum(1 for x in rows if x.invoice_date.month==today.month and x.invoice_date.year==today.year),"room_revenue":[],"report_rows":rows if from_date or to_date else [],"from_date":from_date,"to_date":to_date})

@router.get("/reports/csv")
async def export_csv(from_date:date|None=None,to_date:date|None=None,db:Session=Depends(get_db)):
    rows=date_range(db.query(CustomGSTInvoice),from_date,to_date).order_by(CustomGSTInvoice.id.desc()).all(); out=io.StringIO();w=csv.writer(out);w.writerow(["Invoice","Booking","Date","Guest","GSTIN","Tax","Total","Paid","Balance"])
    for x in rows:w.writerow([x.invoice_no,x.booking_no,x.invoice_date,x.customer_name,x.customer_gstin,x.gst_amount,x.total_amount,x.amount_paid,x.balance_amount])
    return Response("\ufeff"+out.getvalue(),media_type="text/csv",headers={"Content-Disposition":'attachment; filename="hotel_invoice_report.csv"'})
