from fastapi import FastAPI, Request
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import Response

from app.tools.engine import create_tables
from app.tools.home import home
from .routes.status.index import status_router
from .routes.page import page_router
from .routes.auth.index import auth_router
from .routes.notes.index import notes_router
from .tools.auth_middleware import auth_middleware
from .tools.minify_middleware import MinifyMiddleware

app = FastAPI(
    title="main",
    docs_url="/docs/",
    redoc_url=None
)

@app.middleware("http")
async def middleware(request: Request, call_next):
    return await auth_middleware(request, call_next)

app.add_middleware(MinifyMiddleware)

app.add_middleware(
    GZipMiddleware,
    minimum_size=0,
    compresslevel=9
)

create_tables()

app.include_router(
    auth_router,
    prefix="/auth",
    tags=["auth"],
    include_in_schema=False
)

app.include_router(
    notes_router,
    prefix="/notes",
    tags=["notes"]
)

app.include_router(
    status_router,
    prefix="/status",
    tags=["status"]
)

app.include_router(
    page_router,
    prefix="",
    tags=["page"],
    include_in_schema=False
)

@app.exception_handler(RequestValidationError)
async def request_validation_exception_handler(request: Request, exc: RequestValidationError):
    reason = None
    for error in exc.errors():
        if "ctx" in error and "reason" in error["ctx"]:
            reason = error["ctx"]["reason"]
            break
    error_html = home.get_template("error/index.html").render(
        request=request,
        reason=reason
    )
    return Response(content=error_html, media_type="text/html", status_code=422)