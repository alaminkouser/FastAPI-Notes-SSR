from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.requests import Request
from fastapi.responses import Response
import minify_html

class MinifyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)

        TYPES = ["text/html", "text/css", "text/javascript"]
        
        if response.headers.get("content-type", "").split(";")[0] in TYPES:
            try:
                body_iterator = getattr(response, "body_iterator", None)
                if body_iterator:
                    body_chunks = []
                    async for chunk in body_iterator:
                        body_chunks.append(chunk)
                    
                    body = b"".join(body_chunks)
                    html_content = body.decode("utf-8")
                    
                    minified_html = minify_html.minify(
                        html_content,
                        keep_closing_tags=True,
                        minify_css=True,
                        minify_js=True
                    )
                    
                    headers = dict(response.headers)
                    headers.pop("content-length", None)
                    
                    media_type = response.headers.get("content-type", "").split(";")[0]

                    new_response = Response(
                        content=minified_html,
                        status_code=response.status_code,
                        media_type=media_type
                    )
                    
                    for header_name, header_value in response.headers.items():
                        if header_name.lower() == "set-cookie":
                            new_response.headers.append(header_name, header_value)
                        if header_name.lower() == "cache-control":
                            new_response.headers.append(header_name, header_value)
                    
                    response = new_response
            except Exception as _e:
                pass

        return response