from datetime import datetime
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.auth.dependencies import login_required
from app.config.database import get_db
from app.incidents.models import Incident, IncidentAttachment, IncidentComment, IncidentHistory
from app.users.models import User

router = APIRouter(prefix="/incidents", dependencies=[Depends(login_required)])
templates = Jinja2Templates(directory="app/templates")
UPLOAD_DIR = Path("app/static/uploads/incidents")
STATUSES = ["Open", "Assigned", "In Progress", "Pending", "Resolved", "Reopen"]
PRIORITIES = ["Low", "Medium", "High", "Critical"]
CATEGORIES = ["Maintenance", "Electrical", "Plumbing", "Housekeeping", "Reception", "IT", "Guest Complaint", "Security", "Laundry", "Other"]
ALLOWED_IMAGES = {".jpg", ".jpeg", ".png", ".webp"}


def session_user(request: Request):
    user = request.session.get("user", {})
    return user.get("id"), user.get("full_name") or user.get("name") or user.get("email") or "ADS ERP User"


def incident_or_404(db: Session, incident_id: int):
    incident = db.get(Incident, incident_id)
    if not incident:
        raise HTTPException(404, "Incident not found")
    return incident


async def save_photos(db: Session, incident: Incident, photos: list[UploadFile], user_id: int | None):
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    for photo in photos:
        if not photo.filename:
            continue
        extension = Path(photo.filename).suffix.lower()
        if extension not in ALLOWED_IMAGES:
            continue
        content = await photo.read()
        if not content or len(content) > 10 * 1024 * 1024:
            continue
        file_name = f"{datetime.now():%Y%m%d%H%M%S}_{uuid4().hex}{extension}"
        (UPLOAD_DIR / file_name).write_bytes(content)
        db.add(IncidentAttachment(incident_id=incident.id, file_name=file_name, original_name=photo.filename,
            file_size=len(content), mime_type=photo.content_type, uploaded_by=user_id))


@router.get("", response_class=HTMLResponse)
async def dashboard(request: Request, db: Session = Depends(get_db)):
    counts = dict(db.query(Incident.status, func.count(Incident.id)).group_by(Incident.status).all())
    recent = db.query(Incident).order_by(Incident.id.desc()).limit(10).all()
    return templates.TemplateResponse(request=request, name="incidents/dashboard.html", context={"counts": counts, "recent": recent})


@router.get("/list", response_class=HTMLResponse)
async def incident_list(request: Request, search: str = "", status: str = "", db: Session = Depends(get_db)):
    query = db.query(Incident)
    if search.strip():
        term = f"%{search.strip()}%"
        query = query.filter(or_(Incident.case_no.ilike(term), Incident.subject.ilike(term), Incident.room_no.ilike(term)))
    if status in STATUSES:
        query = query.filter(Incident.status == status)
    return templates.TemplateResponse(request=request, name="incidents/list.html", context={"incidents": query.order_by(Incident.id.desc()).all(), "search": search, "selected_status": status, "statuses": STATUSES})


@router.get("/new", response_class=HTMLResponse)
async def create_page(request: Request):
    return templates.TemplateResponse(request=request, name="incidents/form.html", context={"incident": None, "categories": CATEGORIES, "priorities": PRIORITIES})


@router.get("/{incident_id}/edit", response_class=HTMLResponse)
async def edit_page(incident_id: int, request: Request, db: Session = Depends(get_db)):
    return templates.TemplateResponse(request=request, name="incidents/form.html", context={"incident": incident_or_404(db, incident_id), "categories": CATEGORIES, "priorities": PRIORITIES})


@router.post("/save")
async def save_incident(request: Request, incident_id: int | None = Form(None), subject: str = Form(...), description: str = Form(""),
    category: str = Form("Other"), priority: str = Form("Medium"), room_no: str = Form(""), hotel_area: str = Form(""),
    guest_name: str = Form(""), guest_mobile: str = Form(""), photos: list[UploadFile] = File(default=[]), db: Session = Depends(get_db)):
    user_id, user_name = session_user(request)
    if incident_id:
        incident = incident_or_404(db, incident_id)
    else:
        last = db.query(Incident.case_no).order_by(Incident.id.desc()).first()
        sequence = int(last[0].split("-")[-1]) + 1 if last else 1
        incident = Incident(case_no=f"INC-{datetime.now().year}-{sequence:06d}", status="Open", created_by=user_id, created_by_name=user_name)
        db.add(incident); db.flush()
        db.add(IncidentHistory(incident_id=incident.id, old_status=None, new_status="Open", changed_by=user_id, changed_by_name=user_name, remarks="Incident created"))
    incident.subject = subject.strip(); incident.description = description.strip() or None
    incident.category = category if category in CATEGORIES else "Other"; incident.priority = priority if priority in PRIORITIES else "Medium"
    incident.room_no = room_no.strip() or None; incident.hotel_area = hotel_area.strip() or None
    incident.guest_name = guest_name.strip() or None; incident.guest_mobile = guest_mobile.strip() or None
    await save_photos(db, incident, photos, user_id)
    db.commit()
    return RedirectResponse(f"/incidents/{incident.id}", status_code=303)


@router.get("/{incident_id}", response_class=HTMLResponse)
async def view_incident(incident_id: int, request: Request, db: Session = Depends(get_db)):
    incident = incident_or_404(db, incident_id)
    users = db.query(User).filter(User.is_active.is_(True)).order_by(User.full_name).all()
    return templates.TemplateResponse(request=request, name="incidents/view.html", context={"incident": incident, "users": users, "statuses": STATUSES})


@router.post("/{incident_id}/status")
async def update_status(incident_id: int, request: Request, status: str = Form(...), db: Session = Depends(get_db)):
    incident = incident_or_404(db, incident_id)
    if status not in STATUSES:
        raise HTTPException(400, "Invalid status")
    user_id, user_name = session_user(request); old = incident.status
    incident.status = status; incident.updated_at = datetime.utcnow()
    if status == "Resolved": incident.resolved_at = datetime.utcnow(); incident.closed_by = user_id
    elif old == "Resolved": incident.resolved_at = None; incident.closed_by = None
    db.add(IncidentHistory(incident_id=incident.id, old_status=old, new_status=status, changed_by=user_id, changed_by_name=user_name, remarks="Status updated"))
    db.commit(); return RedirectResponse(f"/incidents/{incident.id}", status_code=303)


@router.post("/{incident_id}/assign")
async def assign(incident_id: int, request: Request, assigned_to: int = Form(...), db: Session = Depends(get_db)):
    incident = incident_or_404(db, incident_id); assignee = db.get(User, assigned_to)
    if not assignee or not assignee.is_active: raise HTTPException(400, "Invalid assignee")
    user_id, user_name = session_user(request); old = incident.status
    incident.assigned_to = assignee.id; incident.assigned_to_name = assignee.full_name; incident.assigned_at = datetime.utcnow(); incident.status = "Assigned"
    db.add(IncidentHistory(incident_id=incident.id, old_status=old, new_status="Assigned", changed_by=user_id, changed_by_name=user_name, remarks=f"Assigned to {assignee.full_name}"))
    db.commit(); return RedirectResponse(f"/incidents/{incident.id}", status_code=303)


@router.post("/{incident_id}/comments")
async def add_comment(incident_id: int, request: Request, comment: str = Form(...), db: Session = Depends(get_db)):
    incident_or_404(db, incident_id); user_id, user_name = session_user(request)
    if comment.strip(): db.add(IncidentComment(incident_id=incident_id, user_id=user_id, user_name=user_name, comment=comment.strip())); db.commit()
    return RedirectResponse(f"/incidents/{incident_id}", status_code=303)


@router.post("/{incident_id}/attachments/{attachment_id}/delete")
async def delete_attachment(incident_id: int, attachment_id: int, db: Session = Depends(get_db)):
    attachment = db.query(IncidentAttachment).filter_by(id=attachment_id, incident_id=incident_id).first()
    if attachment:
        path = UPLOAD_DIR / attachment.file_name
        if path.is_file(): path.unlink()
        db.delete(attachment); db.commit()
    return RedirectResponse(f"/incidents/{incident_id}", status_code=303)


@router.post("/{incident_id}/delete")
async def delete_incident(incident_id: int, db: Session = Depends(get_db)):
    incident = incident_or_404(db, incident_id)
    for item in incident.attachments:
        path = UPLOAD_DIR / item.file_name
        if path.is_file(): path.unlink()
    db.delete(incident); db.commit(); return RedirectResponse("/incidents/list", status_code=303)


@router.get("/reports/summary", response_class=HTMLResponse)
async def reports(request: Request, db: Session = Depends(get_db)):
    status_report = db.query(Incident.status, func.count(Incident.id)).group_by(Incident.status).order_by(func.count(Incident.id).desc()).all()
    category_report = db.query(Incident.category, func.count(Incident.id)).group_by(Incident.category).order_by(func.count(Incident.id).desc()).all()
    return templates.TemplateResponse(request=request, name="incidents/reports.html", context={"status_report": status_report, "category_report": category_report, "total": db.query(func.count(Incident.id)).scalar()})
