from fastapi import APIRouter, Request
from app.tools.home import home
import os
from fastapi.responses import FileResponse, Response

page_router = APIRouter()

def not_found(request: Request):
    html_string = home.get_template("templates/404.html").render(request=request)
    return Response(content=html_string, media_type="text/html", status_code=404)

@page_router.get("{path:path}")
def page(request: Request, path: str):
    if path.startswith("/templates/"):
        return not_found(request)

    if path.endswith("/") and os.path.exists(f"app/home{path}index.html") and os.path.isfile(f"app/home{path}index.html"):
        html_string = home.get_template(f"{path}index.html").render(request=request)
        return Response(content=html_string, media_type="text/html")
    
    if not path.endswith(".html") and os.path.exists(f"app/home{path}") and os.path.isfile(f"app/home{path}"):
        return FileResponse(
            f"app/home{path}",  
            headers={
                "Cache-Control": "public, max-age=3600"
            }
        )
    
    return not_found(request)
