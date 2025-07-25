import email
import os
from typing import Literal
from urllib.parse import parse_qs, urlparse
import aiohttp
from fastapi import APIRouter, Form, Query, Request, Response
from fastapi.responses import RedirectResponse
from firebase_admin import auth
from pydantic import EmailStr, BaseModel, Json
from app.tools.send_email import send_email
from app.tools.home import home

auth_router = APIRouter()

class PageData(BaseModel):
    email: EmailStr
    too_many_requests: bool

class AuthFormRequest(BaseModel):
    email: EmailStr

@auth_router.post("/form/")
async def login(request: Request, auth_form: AuthFormRequest = Form(...)) -> Response:
    email = auth_form.email
    too_many_requests = False
    
    action_code_settings = auth.ActionCodeSettings(
        url=f"{request.headers.get("origin")}/auth/link/"
    )
    
    link = ""

    try:
        link = auth.generate_sign_in_with_email_link(
            email=email,
            action_code_settings=action_code_settings
        )
    except Exception as e:
        print("ERROR", e)
        too_many_requests = True
    
    if too_many_requests == True:
        html = home.get_template("auth/form/index.html").render(
            request=request,
            email=email,
            too_many_requests=too_many_requests
        )
        return Response(content=html, media_type="text/html")

    parsed_url = urlparse(link)
    oob_code = parse_qs(parsed_url.query)["oobCode"][0]
    link = request.headers.get("origin", "") + "/auth/link/?email=" + email + "&oobCode=" + oob_code

    email_response = await send_email(email, "Login Link", link)

    if email_response != True:
        too_many_requests = True

    html = home.get_template("auth/form/index.html").render(
        request=request,
        email=email,
        too_many_requests=too_many_requests
    )

    return Response(content=html, media_type="text/html")

class LinkData(BaseModel):
    idToken: str
    refreshToken: str
    expiresIn: str

@auth_router.get("/link/")
async def link(request: Request, email: EmailStr = Query(...), oobCode: str = Query(...)) -> Response:
    data: LinkData = LinkData(
        idToken="",
        refreshToken="",
        expiresIn=""
    )
    
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithEmailLink?key={os.getenv("FIREBASE_WEB_API_KEY")}",
            headers={"Content-Type": "application/json"},
            json={"email": email, "oobCode": oobCode}
        ) as response:
            if response.status != 200:
                return RedirectResponse(url="/auth/form/", status_code=303)

            response_data = await response.json()
            data = LinkData(
                idToken=response_data["idToken"],
                refreshToken=response_data["refreshToken"],
                expiresIn=response_data["expiresIn"]
            )

    new_login_html = home.get_template("continue/index.html").render(
        request=request,
        message="You have been logged in successfully. Your email is " + email + ".",
        url="/"
    )
    response = Response(content=new_login_html, media_type="text/html")
    response.set_cookie(
        key="idToken",
        value=data.idToken,
        expires=int(data.expiresIn),
        httponly=True,
        secure=True,
        samesite="strict"
    )
    response.set_cookie(
        key="refreshToken",
        value=data.refreshToken,
        httponly=True,
        secure=True,
        samesite="strict",
        expires=31536000
    )
    return response

class LogoutRequest(BaseModel):
    logout: Literal["Logout from All Devices", "Logout from This Device"]

@auth_router.post("/logout/")
async def logout(request: Request, logoutForm: LogoutRequest = Form(...)) -> Response:
    response = RedirectResponse(url="/auth/form/", status_code=303)
    if logoutForm.logout == "Logout from All Devices":
        try:
            id_token = request.cookies.get("idToken")
            decoded_token = auth.verify_id_token(id_token)
            uid = decoded_token["uid"]
            auth.revoke_refresh_tokens(uid)
        except Exception as e:
            print("ERROR", e)
    
    response.delete_cookie(key="idToken")
    response.delete_cookie(key="refreshToken")
    return response
