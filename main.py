from fastapi import FastAPI
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from app.routes.router import api_router
from app.access_control.middleware import UserUrlAccessMiddleware
from app.config.database import engine
from app.hrm.models import Attendance, Employee, LeaveRequest

app = FastAPI(title="ADS ERP", version="0.5.1")

# ----------------------------------------------------
# Session Middleware
# ----------------------------------------------------

app.add_middleware(
    UserUrlAccessMiddleware
)

app.add_middleware(
    SessionMiddleware,
    secret_key="ads-erp-secret-key",
    max_age=60 * 60 * 8,
    same_site="lax",
    https_only=True,
)

# ----------------------------------------------------
# Static Files
# ----------------------------------------------------

app.mount("/static", StaticFiles(directory="app/static"), name="static")

# ----------------------------------------------------
# Templates
# ----------------------------------------------------

templates = Jinja2Templates(directory="app/templates")

# ----------------------------------------------------
# Template Globals
# ----------------------------------------------------


def current_user(request: Request):

    return request.session.get("user", {})


templates.env.globals["current_user"] = current_user

# ----------------------------------------------------
# Routes
# ----------------------------------------------------

app.include_router(api_router)


@app.on_event("startup")
def ensure_hrm_tables():
    """Create HRM tables on existing deployments without touching ERP data."""
    Employee.metadata.create_all(
        bind=engine,
        tables=[Employee.__table__, Attendance.__table__, LeaveRequest.__table__],
        checkfirst=True,
    )

# ----------------------------------------------------
# Home
# ----------------------------------------------------


@app.get(
    "/",
    response_class=HTMLResponse
)
async def index(
    request: Request
):

    if request.session.get("user"):

        return RedirectResponse(
            url="/dashboard",
            status_code=303
        )

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={}
    )


# ----------------------------------------------------
# Health
# ----------------------------------------------------


@app.get("/health")
async def health():

    return {"application": "ADS ERP", "version": "0.5.1", "status": "running"}
