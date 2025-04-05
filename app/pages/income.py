import base64
from datetime import date

import aiohttp
from fastapi import APIRouter, Depends, Request, Query
from fastapi.templating import Jinja2Templates

from app.api.v1.routes.income_routes import (
    income_categories_get,
    income_get_all,
    income_summary_chart_get,
    income_summary_get,
)
from app.core.config import settings
from app.schemas.transaction_category_schemas import TransactionsOnDeleteActions

router = APIRouter()
templates = Jinja2Templates(directory="./templates")


@router.get("/income/")
async def income_page(
    request: Request,
    income=Depends(income_summary_get),
):
    return templates.TemplateResponse(
        name="income_main.html",
        context={
            "request": request,
            "title": "income",
            "summary": income,
        },
    )


@router.get("/income/create/")
async def income_create_page(
    request: Request,
    categories=Depends(income_categories_get),
):
    return templates.TemplateResponse(
        name="transaction_create.html",
        context={
            "request": request,
            "transaction_name": "income",
            "user_categories": categories,
            "api_create_url": f"{settings.api.prefix_v1}/income/",
            "success_redirect_url": "/pages/income/",
        },
    )


@router.get("/income/categories/create/")
async def income_category_create_page(
    request: Request,
):
    return templates.TemplateResponse(
        name="tx_category_create.html",
        context={
            "request": request,
            "title": "Create category",
            "tx_type_multiple": "income",
            "api_create_url": f"{settings.api.prefix_v1}/income/categories/",
            "success_redirect_url": "/pages/income/",
        },
    )


@router.get("/income/detail/{transaction_id}/")
async def income_get_page(
    request: Request,
    transaction_id: int,
    categories=Depends(income_categories_get),
):
    async with aiohttp.ClientSession() as session:
        url = (
            f"http://0.0.0.0:8000{settings.api.prefix_v1}/income/{transaction_id}/"
        )
        async with session.get(url, cookies=request.cookies) as resp:
            income_info = await resp.json()

    return templates.TemplateResponse(
        name="transaction_info.html",
        context={
            "request": request,
            "transaction_info": income_info,
            "user_categories": categories,
            "title": "Income info",
            "transaction_type": "income",
            "tx_type_multiple": "income",
            "transactions_get_url": f"{settings.api.prefix_v1}/income/",
            "tx_delete_url": f"{settings.api.prefix_v1}/income/{transaction_id}/",
            "api_update_tx_url": f"{settings.api.prefix_v1}/income/{transaction_id}/",
            "success_redirect_url": "/pages/income/",
        },
    )


@router.get("/income/all/")
async def income_get_all_page(
    request: Request,
    page: int = Query(1, ge=1),
):
    async with aiohttp.ClientSession() as session:
        url = f"http://0.0.0.0:8000{settings.api.prefix_v1}/income/"
        params = {"page": page}
        cookies = request.cookies
        async with session.get(url, cookies=cookies, params=params) as resp:
            income = await resp.json()

    return templates.TemplateResponse(
        name="transactions_all.html",
        context={
            "request": request,
            "transactions": income,
            "current_page": page,
            "title": "All income",
            "tx_type_multiple": "income",
            "url_for_pagination": f"{settings.pages.pages_prefix}/income/all/?page=",
            "transactions_get_url": f"{settings.api.prefix_v1}/income/",
            "tx_get_details_funcname": "income_get_page",
            "tx_get_details_url_prefix": "/pages/income/detail/",
        },
    )


@router.get("/income/categories/")
async def income_categories_page(
    request: Request,
    categories=Depends(income_categories_get),
):
    on_delete_actions = [str(i) for i in TransactionsOnDeleteActions]

    return templates.TemplateResponse(
        name="tx_categories.html",
        context={
            "request": request,
            "categories": categories,
            "title": "Income categories",
            "categories_type": "income",
            "api_update_tx_category_url": f"{settings.api.prefix_v1}/income/categories/",
            "api_delete_tx_category_url": f"{settings.api.prefix_v1}/income/categories/",
            "on_delete_actions": on_delete_actions,
        },
    )


@router.get("/income/summary/full/")
async def income_summary_full(
    request: Request,
    summary=Depends(income_summary_get),
    chart=Depends(income_summary_chart_get),
):
    chart_base64 = base64.b64encode(chart.body).decode("utf-8")
    return templates.TemplateResponse(
        name="summary_full.html",
        context={
            "request": request,
            "title": "Income summary",
            "time_interval": "All time",
            "summary": summary,
            "chart": chart_base64,
            "chart_width": "600",
            "get_summary_url": f"{settings.api.prefix_v1}/income/summary/",
            "get_summary_chart_url": f"{settings.api.prefix_v1}/income/summary/chart/",
        },
    )


@router.get("/income/summary/annual/")
async def income_summary_annual(
    request: Request,
):
    year = date.today().year

    async with aiohttp.ClientSession() as session:
        url_prefix = f"http://0.0.0.0:8000{settings.api.prefix_v1}/income/summary"
        summary_url = f"{url_prefix}/{year}/"
        async with session.get(summary_url, cookies=request.cookies) as resp:
            summary = await resp.json()

        chart_url = f"{url_prefix}/chart/{year}/"
        async with session.get(chart_url, cookies=request.cookies) as resp:
            chart = await resp.content.read()

    chart_base64 = base64.b64encode(chart).decode("utf-8")
    return templates.TemplateResponse(
        name="summary_annual.html",
        context={
            "request": request,
            "title": "Income summary",
            "time_interval": "Annual",
            "tx_type_multiple": "income",
            "summary": summary,
            "chart": chart_base64,
            "chart_width": "900",
            "get_summary_prefix": f"{settings.api.prefix_v1}/income/summary",
        },
    )


@router.get("/income/summary/monthly/")
async def income_summary_monthly(
    request: Request,
):
    year = date.today().year
    month = date.today().month

    async with aiohttp.ClientSession() as session:
        url_prefix = f"http://0.0.0.0:8000{settings.api.prefix_v1}/income/summary"
        summary_url = f"{url_prefix}/{year}/{month}/"
        async with session.get(summary_url, cookies=request.cookies) as resp:
            summary = await resp.json()

        chart_url = f"{url_prefix}/chart/{year}/{month}/"
        async with session.get(chart_url, cookies=request.cookies) as resp:
            chart = await resp.content.read()

    chart_base64 = base64.b64encode(chart).decode("utf-8")
    return templates.TemplateResponse(
        name="summary_monthly.html",
        context={
            "request": request,
            "title": "Income summary",
            "time_interval": "Monthly",
            "tx_type_multiple": "income",
            "summary": summary,
            "chart": chart_base64,
            "chart_width": "900",
            "get_summary_prefix": f"{settings.api.prefix_v1}/income/summary",
        },
    )
