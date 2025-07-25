import os
import aiohttp
from fastapi import Request, Response
from firebase_admin import auth
from fastapi.responses import RedirectResponse

from app.tools.home import home

async def refresh_tokens(refresh_token: str) -> tuple[str, str, int] | None:
    """Refresh Firebase tokens and return new id_token and refresh_token"""
    if not refresh_token:
        return None
        
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://securetoken.googleapis.com/v1/token?key=" + os.getenv("FIREBASE_WEB_API_KEY", ""),
                headers={"Content-Type": "application/json"},
                json={
                    "grant_type": "refresh_token",
                    "refresh_token": refresh_token
                }
            ) as response:
                if response.status == 200:
                    body = await response.json()
                    return body["id_token"], body["refresh_token"], int(body["expires_in"])
                return None
    except Exception as e:
        print("ERROR", e)
        return None

OPEN_PATHS = [
    "/favicon.ico",
    "/main.css",
    "/noto.ttf",
    "/auth/link/",
    "/continue/index.css",
    "/auth/logout/",
    "/error/index.css"
]

SEC_FETCH_SITE_ALLOWED = [
    "same-origin",
    "same-site",
    "none"
]

async def auth_middleware(request: Request, call_next):
    auth_state = None
    if request.url.path in OPEN_PATHS:
        return await call_next(request)
    
    if request.headers.get("Sec-Fetch-Site") in SEC_FETCH_SITE_ALLOWED:
        if request.url.path == "/continue/":
            return RedirectResponse(url=request.headers.get("origin", "") + "/")
    
    # Check Sec-Fetch-Site
    if request.headers.get("Sec-Fetch-Site") not in SEC_FETCH_SITE_ALLOWED:
        continue_url = request.url
        if continue_url.path == "/continue/":
            continue_url = "/"
        continue_html = home.get_template("continue/index.html").render(
            request=request,
            url=continue_url
        )
        return Response(content=continue_html, media_type="text/html")
    
    # Read Cookie idToken and refreshToken
    id_token = request.cookies.get("idToken")
    refresh_token = request.cookies.get("refreshToken")
    
    # Check if we're on an auth page
    is_auth_page = request.url.path.startswith("/auth/")
    
    # If no tokens exist, redirect to auth form
    if not id_token and not refresh_token:
        if is_auth_page:
            return await call_next(request)
        else:
            return RedirectResponse(url="/auth/form/")
    
    # Try to verify the current id_token
    if id_token:
        try:
            auth_state = auth.verify_id_token(id_token)
            if is_auth_page:
                return RedirectResponse(url="/", status_code=303)
            else:
                request.state.auth = auth_state
                return await call_next(request)
        except Exception as e:
            print("ERROR", e)
            # Token is invalid, try to refresh
            pass
    
    # Try to refresh tokens
    if refresh_token:
        new_tokens = await refresh_tokens(refresh_token)
        if new_tokens:
            new_id_token, new_refresh_token, new_expires_in = new_tokens
            
            # Create response based on whether we're on an auth page
            if is_auth_page:
                response = RedirectResponse(url="/", status_code=303)
            else:
                request.state.auth = auth.verify_id_token(new_id_token)
                response = await call_next(request)
                response.set_cookie(
                    key="idToken",
                    value=new_id_token,
                    httponly=True,
                    secure=True,
                    samesite="strict",
                    expires=new_expires_in
                )
                response.set_cookie(
                    key="refreshToken",
                    value=new_refresh_token,
                    httponly=True,
                    secure=True,
                    samesite="strict",
                    expires=31536000
                )
            return response
        else:
            response = RedirectResponse(url="/auth/form/", status_code=303)
            response.delete_cookie(key="idToken")
            response.delete_cookie(key="refreshToken")
            return response
    
    # All authentication failed, redirect to auth form
    if is_auth_page:
        return await call_next(request)
    else:
        return RedirectResponse(url="/auth/form/")