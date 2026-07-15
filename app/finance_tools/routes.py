from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import extract, func, or_
from sqlalchemy.orm import Session

from app.auth.dependencies import login_required
from app.config.database import get_db
from app.finance_tools.models import FinanceCategory, FinanceExpense, FinanceIncome, FinanceQuotation, FinanceQuotationItem, FinanceVendor

router = APIRouter(prefix="/finance-tools", dependencies=[Depends(login_required)])
templates = Jinja2Templates(directory="app/templates")
UPLOAD_DIR = Path("app/static/uploads/finance")
PAYMENT_MODES = ["Cash", "UPI", "Bank Transfer", "Card", "Cheque"]
INCOME_CATEGORIES = ["Room Revenue", "Food & Beverage", "Advance", "Service", "Other"]


def user(request):
    data = request.session.get("user", {})
    return data.get("id"), data.get("name") or data.get("email") or "ADS ERP User"


def money(value):
    return Decimal(str(value or 0)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


async def upload(file: UploadFile | None, folder: str):
    if not file or not file.filename:
        return None
    content = await file.read()
    if not content or len(content) > 15 * 1024 * 1024:
        return None
    suffix = Path(file.filename).suffix.lower()
    if suffix not in {".jpg", ".jpeg", ".png", ".webp", ".pdf"}:
        return None
    path = UPLOAD_DIR / folder; path.mkdir(parents=True, exist_ok=True)
    name = f"{uuid4().hex}{suffix}"; (path / name).write_bytes(content)
    return f"{folder}/{name}"


def remove_file(name):
    if name:
        path = UPLOAD_DIR / Path(name).name if "/" not in name else UPLOAD_DIR / name
        if path.is_file(): path.unlink()


@router.get("", response_class=HTMLResponse)
async def dashboard(request: Request, db: Session = Depends(get_db)):
    income = db.query(func.coalesce(func.sum(FinanceIncome.amount), 0)).filter(FinanceIncome.is_active.is_(True)).scalar()
    expense = db.query(func.coalesce(func.sum(FinanceExpense.total_amount), 0)).filter(FinanceExpense.is_active.is_(True)).scalar()
    return templates.TemplateResponse(request=request, name="finance/dashboard.html", context={"income": income, "expense": expense, "balance": money(income)-money(expense), "recent_income": db.query(FinanceIncome).filter_by(is_active=True).order_by(FinanceIncome.id.desc()).limit(5).all(), "recent_expenses": db.query(FinanceExpense).filter_by(is_active=True).order_by(FinanceExpense.id.desc()).limit(5).all()})


@router.get("/income", response_class=HTMLResponse)
async def income_list(request: Request, search: str = "", db: Session = Depends(get_db)):
    q=db.query(FinanceIncome).filter_by(is_active=True)
    if search: q=q.filter(or_(FinanceIncome.received_from.ilike(f"%{search}%"), FinanceIncome.reference_no.ilike(f"%{search}%")))
    return templates.TemplateResponse(request=request,name="finance/income_list.html",context={"rows":q.order_by(FinanceIncome.income_date.desc()).all(),"search":search})


@router.get("/income/new", response_class=HTMLResponse)
async def income_new(request: Request): return templates.TemplateResponse(request=request,name="finance/income_form.html",context={"row":None,"categories":INCOME_CATEGORIES,"modes":PAYMENT_MODES})


@router.get("/income/{item_id}/edit", response_class=HTMLResponse)
async def income_edit(item_id:int,request:Request,db:Session=Depends(get_db)): return templates.TemplateResponse(request=request,name="finance/income_form.html",context={"row":db.get(FinanceIncome,item_id),"categories":INCOME_CATEGORIES,"modes":PAYMENT_MODES})


@router.post("/income/save")
async def income_save(request:Request,item_id:int|None=Form(None),income_date:date=Form(...),category:str=Form(...),amount:Decimal=Form(...),payment_mode:str=Form(...),reference_no:str=Form(""),received_from:str=Form(...),description:str=Form(""),attachment:UploadFile|None=File(None),db:Session=Depends(get_db)):
    row=db.get(FinanceIncome,item_id) if item_id else FinanceIncome(); uid,uname=user(request)
    if not item_id: row.created_by=uid; row.created_by_name=uname; db.add(row)
    row.income_date=income_date; row.category=category; row.amount=money(amount); row.payment_mode=payment_mode; row.reference_no=reference_no.strip() or None; row.received_from=received_from.strip(); row.description=description.strip() or None
    new_file=await upload(attachment,"income")
    if new_file: remove_file(row.attachment); row.attachment=new_file
    db.commit(); return RedirectResponse("/finance-tools/income",303)


@router.post("/income/{item_id}/delete")
async def income_delete(item_id:int,db:Session=Depends(get_db)):
    row=db.get(FinanceIncome,item_id)
    if row: row.is_active=False; db.commit()
    return RedirectResponse("/finance-tools/income",303)


@router.get("/expenses",response_class=HTMLResponse)
async def expenses(request:Request,search:str="",db:Session=Depends(get_db)):
    q=db.query(FinanceExpense).filter_by(is_active=True)
    if search:q=q.filter(or_(FinanceExpense.bill_number.ilike(f"%{search}%"),FinanceExpense.description.ilike(f"%{search}%")))
    return templates.TemplateResponse(request=request,name="finance/expense_list.html",context={"rows":q.order_by(FinanceExpense.expense_date.desc()).all(),"search":search})


async def expense_form_context(request,db,row=None): return templates.TemplateResponse(request=request,name="finance/expense_form.html",context={"row":row,"categories":db.query(FinanceCategory).filter_by(is_active=True).order_by(FinanceCategory.name).all(),"vendors":db.query(FinanceVendor).filter_by(is_active=True).order_by(FinanceVendor.name).all(),"modes":PAYMENT_MODES})


@router.get("/expenses/new",response_class=HTMLResponse)
async def expense_new(request:Request,db:Session=Depends(get_db)): return await expense_form_context(request,db)


@router.get("/expenses/{item_id}/edit",response_class=HTMLResponse)
async def expense_edit(item_id:int,request:Request,db:Session=Depends(get_db)): return await expense_form_context(request,db,db.get(FinanceExpense,item_id))


@router.post("/expenses/save")
async def expense_save(request:Request,item_id:int|None=Form(None),expense_date:date=Form(...),category_id:int=Form(...),vendor_id:int|None=Form(None),amount:Decimal=Form(...),gst_percentage:Decimal=Form(0),payment_mode:str=Form(...),bill_number:str=Form(""),description:str=Form(""),status:str=Form("Paid"),attachment:UploadFile|None=File(None),db:Session=Depends(get_db)):
    row=db.get(FinanceExpense,item_id) if item_id else FinanceExpense(); uid,uname=user(request); base=money(amount); gst=money(base*money(gst_percentage)/Decimal(100))
    if not item_id: row.created_by=uid; row.created_by_name=uname; db.add(row)
    row.expense_date=expense_date; row.category_id=category_id; row.vendor_id=vendor_id; row.amount=base; row.gst_percentage=money(gst_percentage); row.gst_amount=gst; row.total_amount=base+gst; row.payment_mode=payment_mode; row.bill_number=bill_number.strip() or None; row.description=description.strip() or None; row.status=status
    new_file=await upload(attachment,"expenses")
    if new_file: remove_file(row.attachment); row.attachment=new_file
    db.commit(); return RedirectResponse("/finance-tools/expenses",303)


@router.post("/expenses/{item_id}/delete")
async def expense_delete(item_id:int,db:Session=Depends(get_db)):
    row=db.get(FinanceExpense,item_id)
    if row: row.is_active=False; db.commit()
    return RedirectResponse("/finance-tools/expenses",303)


@router.get("/vendors",response_class=HTMLResponse)
async def vendors(request:Request,db:Session=Depends(get_db)): return templates.TemplateResponse(request=request,name="finance/vendors.html",context={"rows":db.query(FinanceVendor).filter_by(is_active=True).order_by(FinanceVendor.name).all()})


@router.post("/vendors/save")
async def vendor_save(item_id:int|None=Form(None),name:str=Form(...),mobile:str=Form(""),email:str=Form(""),gstin:str=Form(""),address:str=Form(""),notes:str=Form(""),db:Session=Depends(get_db)):
    row=db.get(FinanceVendor,item_id) if item_id else FinanceVendor(); row.name=name.strip(); row.mobile=mobile.strip() or None; row.email=email.strip() or None; row.gstin=gstin.strip().upper() or None; row.address=address.strip() or None; row.notes=notes.strip() or None
    if not item_id:db.add(row)
    db.commit(); return RedirectResponse("/finance-tools/vendors",303)


@router.post("/vendors/{item_id}/delete")
async def vendor_delete(item_id:int,db:Session=Depends(get_db)):
    row=db.get(FinanceVendor,item_id)
    if row:row.is_active=False;db.commit()
    return RedirectResponse("/finance-tools/vendors",303)


@router.get("/categories",response_class=HTMLResponse)
async def categories(request:Request,db:Session=Depends(get_db)): return templates.TemplateResponse(request=request,name="finance/categories.html",context={"rows":db.query(FinanceCategory).filter_by(is_active=True).order_by(FinanceCategory.display_order,FinanceCategory.name).all()})


@router.post("/categories/save")
async def category_save(item_id:int|None=Form(None),name:str=Form(...),description:str=Form(""),color:str=Form("#2563eb"),icon:str=Form("fas fa-receipt"),display_order:int=Form(1),db:Session=Depends(get_db)):
    row=db.get(FinanceCategory,item_id) if item_id else FinanceCategory(); row.name=name.strip(); row.description=description.strip() or None; row.color=color; row.icon=icon; row.display_order=display_order
    if not item_id:db.add(row)
    db.commit(); return RedirectResponse("/finance-tools/categories",303)


@router.post("/categories/{item_id}/delete")
async def category_delete(item_id:int,db:Session=Depends(get_db)):
    row=db.get(FinanceCategory,item_id)
    if row:row.is_active=False;db.commit()
    return RedirectResponse("/finance-tools/categories",303)


@router.get("/quotations",response_class=HTMLResponse)
async def quotations(request:Request,db:Session=Depends(get_db)): return templates.TemplateResponse(request=request,name="finance/quotations.html",context={"rows":db.query(FinanceQuotation).filter_by(is_active=True).order_by(FinanceQuotation.id.desc()).all()})


@router.get("/quotations/new",response_class=HTMLResponse)
async def quotation_new(request:Request): return templates.TemplateResponse(request=request,name="finance/quotation_form.html",context={"row":None})


@router.get("/quotations/{item_id}/edit",response_class=HTMLResponse)
async def quotation_edit(item_id:int,request:Request,db:Session=Depends(get_db)): return templates.TemplateResponse(request=request,name="finance/quotation_form.html",context={"row":db.get(FinanceQuotation,item_id)})


@router.post("/quotations/save")
async def quotation_save(request:Request,item_id:int|None=Form(None),vendor_name:str=Form(...),vendor_gst:str=Form(""),vendor_phone:str=Form(""),vendor_email:str=Form(""),quotation_date:date=Form(...),expiry_date:date|None=Form(None),grand_total:Decimal=Form(...),status:str=Form("Pending"),remarks:str=Form(""),attachment:UploadFile|None=File(None),db:Session=Depends(get_db)):
    row=db.get(FinanceQuotation,item_id) if item_id else FinanceQuotation(quotation_no="PENDING"); uid,uname=user(request)
    if not item_id:row.created_by=uid;row.created_by_name=uname;db.add(row);db.flush();row.quotation_no=f"QT-{row.id:06d}"
    row.vendor_name=vendor_name.strip();row.vendor_gst=vendor_gst.strip() or None;row.vendor_phone=vendor_phone.strip() or None;row.vendor_email=vendor_email.strip() or None;row.quotation_date=quotation_date;row.expiry_date=expiry_date;row.subtotal=money(grand_total);row.tax_amount=0;row.grand_total=money(grand_total);row.status=status;row.remarks=remarks.strip() or None
    new_file=await upload(attachment,"quotations")
    if new_file:remove_file(row.attachment);row.attachment=new_file
    db.commit();return RedirectResponse("/finance-tools/quotations",303)


@router.post("/quotations/{item_id}/delete")
async def quotation_delete(item_id:int,db:Session=Depends(get_db)):
    row=db.get(FinanceQuotation,item_id)
    if row:row.is_active=False;db.commit()
    return RedirectResponse("/finance-tools/quotations",303)


@router.get("/reports",response_class=HTMLResponse)
async def reports(request:Request,from_date:date|None=None,to_date:date|None=None,db:Session=Depends(get_db)):
    iq=db.query(FinanceIncome).filter_by(is_active=True);eq=db.query(FinanceExpense).filter_by(is_active=True)
    if from_date:iq=iq.filter(FinanceIncome.income_date>=from_date);eq=eq.filter(FinanceExpense.expense_date>=from_date)
    if to_date:iq=iq.filter(FinanceIncome.income_date<=to_date);eq=eq.filter(FinanceExpense.expense_date<=to_date)
    income=money(iq.with_entities(func.coalesce(func.sum(FinanceIncome.amount),0)).scalar());expense=money(eq.with_entities(func.coalesce(func.sum(FinanceExpense.total_amount),0)).scalar())
    monthly_i=db.query(extract('year',FinanceIncome.income_date),extract('month',FinanceIncome.income_date),func.sum(FinanceIncome.amount)).filter(FinanceIncome.is_active.is_(True)).group_by(extract('year',FinanceIncome.income_date),extract('month',FinanceIncome.income_date)).all()
    cats=db.query(FinanceCategory.name,func.sum(FinanceExpense.total_amount)).join(FinanceExpense).filter(FinanceExpense.is_active.is_(True)).group_by(FinanceCategory.name).all()
    vendors=db.query(FinanceVendor.name,func.sum(FinanceExpense.total_amount)).join(FinanceExpense).filter(FinanceExpense.is_active.is_(True)).group_by(FinanceVendor.name).all()
    return templates.TemplateResponse(request=request,name="finance/reports.html",context={"income":income,"expense":expense,"balance":income-expense,"monthly":monthly_i,"categories":cats,"vendors":vendors,"from_date":from_date,"to_date":to_date})
