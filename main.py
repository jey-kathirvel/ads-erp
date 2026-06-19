from fastapi import FastAPI
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from app.routes.router import api_router

app = FastAPI(
    title="ADS ERP",
    version="0.3.0"
)
app.add_middleware(

    SessionMiddleware,

    secret_key="ads-erp-secret-key"

)
app.mount(
    "/static",
    StaticFiles(directory="app/static"),
    name="static"
)

templates = Jinja2Templates(
    directory="app/templates"
)

app.include_router(api_router)


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):

    return templates.TemplateResponse(
        request=request,
        name="index.html"
    )


@app.get("/health")
async def health():

    return {
        "application": "ADS ERP",
        "version": "0.3.0",
        "status": "running"
    }
