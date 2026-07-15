from fastapi import APIRouter
from fastapi import Depends
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.responses import RedirectResponse
from fastapi.responses import FileResponse
from fastapi.templating import Jinja2Templates

from sqlalchemy.orm import Session

from app.config.database import get_db
from app.settings.service import CompanyService

from app.auth.dependencies import login_required

import os
import subprocess
from datetime import datetime

router = APIRouter(dependencies=[Depends(login_required)])

templates = Jinja2Templates(directory="app/templates")

BACKUP_FOLDER = "/opt/ads-erp/backups"


def admin_only(request: Request) -> bool:
    return request.session.get("user", {}).get("role_code") == "ADMIN"


def backup_path(filename: str) -> str:
    """Resolve a backup filename while preventing directory traversal."""
    if not filename or filename != os.path.basename(filename):
        raise ValueError("Invalid backup filename")
    folder = os.path.realpath(BACKUP_FOLDER)
    path = os.path.realpath(os.path.join(folder, filename))
    if os.path.dirname(path) != folder:
        raise ValueError("Invalid backup filename")
    return path


@router.get("/settings/company", response_class=HTMLResponse)
async def company_settings(request: Request, db: Session = Depends(get_db)):

    company = CompanyService.get(db)

    return templates.TemplateResponse(
        request=request, name="settings/company.html", context={"company": company}
    )


# ----------------------------------------------------
# Backup Screen
# ----------------------------------------------------


@router.get("/settings/backup", response_class=HTMLResponse)
async def backup_screen(request: Request):
    print("===================================")
    print("SESSION =", request.session)
    print("ROLE    =", request.session.get("role_code"))
    print("USER    =", request.session.get("user"))
    print("===================================")
    if request.session.get("user", {}).get("role_code") != "ADMIN":

        return RedirectResponse(url="/dashboard", status_code=303)

    os.makedirs(BACKUP_FOLDER, exist_ok=True)

    backups = sorted(
        (name for name in os.listdir(BACKUP_FOLDER) if os.path.isfile(backup_path(name))),
        reverse=True,
    )

    return templates.TemplateResponse(
        request=request, name="settings/backup.html", context={"backups": backups}
    )


# ----------------------------------------------------
# Run Backup
# ----------------------------------------------------


@router.get("/settings/backup/run")
async def run_backup(request: Request):

    if request.session.get("user", {}).get("role_code") != "ADMIN":

        return RedirectResponse(url="/dashboard", status_code=303)

    os.makedirs(BACKUP_FOLDER, exist_ok=True)

    filename = f"ads_erp_" f"{datetime.now().strftime('%Y%m%d_%H%M%S')}" f".dump"

    try:
        filepath = backup_path(filename)
    except ValueError:
        return RedirectResponse(url="/settings/backup", status_code=303)

    subprocess.run(
    [
        "/usr/bin/pg_dump",
        "-U",
        "ads_erp",
        "-h",
        "localhost",
        "-Fc",
        "ads_erp_db",
        "-f",
        filepath
    ],
    env={
        **os.environ,
        "PGPASSWORD": "Akshat#0950"
    },
    check=True
)

    return RedirectResponse(url="/settings/backup", status_code=303)


# ----------------------------------------------------
# Download Backup
# ----------------------------------------------------


@router.get("/settings/backup/download/{filename}")
async def download_backup(filename: str, request: Request):

    if request.session.get("user", {}).get("role_code") != "ADMIN":

        return RedirectResponse(url="/dashboard", status_code=303)

    try:
        filepath = backup_path(filename)
    except ValueError:
        return RedirectResponse(url="/settings/backup", status_code=303)

    if not os.path.isfile(filepath):
        return RedirectResponse(url="/settings/backup", status_code=303)

    return FileResponse(
        path=filepath, filename=filename, media_type="application/octet-stream"
    )


# ----------------------------------------------------
# Delete Backup
# ----------------------------------------------------


@router.get("/settings/backup/delete/{filename}")
async def delete_backup(filename: str, request: Request):

    if request.session.get("user", {}).get("role_code") != "ADMIN":

        return RedirectResponse(url="/dashboard", status_code=303)

    try:
        filepath = backup_path(filename)
    except ValueError:
        return RedirectResponse(url="/settings/backup", status_code=303)

    if os.path.isfile(filepath):

        os.remove(filepath)

    return RedirectResponse(url="/settings/backup", status_code=303)


# ----------------------------------------------------
# Delete All Backups
# ----------------------------------------------------


@router.post("/settings/backup/delete-all")
async def delete_all_backups(request: Request):
    if not admin_only(request):
        return RedirectResponse(url="/dashboard", status_code=303)

    os.makedirs(BACKUP_FOLDER, exist_ok=True)

    for filename in os.listdir(BACKUP_FOLDER):
        try:
            filepath = backup_path(filename)
        except ValueError:
            continue
        if os.path.isfile(filepath):
            os.remove(filepath)

    return RedirectResponse(url="/settings/backup", status_code=303)
