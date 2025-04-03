from fastapi import APIRouter, Request
from starlette.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="./templates")


@router.get("/")
async def root_page(request: Request):
    return templates.TemplateResponse(
        name="base.html",
        context={
            "request": request,
            "title": "dohodyaga",
            "sign_in_funcname": "sign_in_page",
            "sign_up_funcname": "sign_up_page",
        },
    )


@router.get("/sign_up/")
async def sign_up_page(request: Request):
    return templates.TemplateResponse(
        name="sign_up.html",
        context={
            "request": request,
            "title": "Sign up",
        },
    )


@router.get("/sign_in/")
async def sign_in_page(request: Request):
    return templates.TemplateResponse(
        name="sign_in.html",
        context={
            "request": request,
            "title": "Sign in",
        },
    )
