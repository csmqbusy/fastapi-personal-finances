import base64
from datetime import date

import aiohttp
from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates

from app.api.v1.routes.spendings_routes import (
    spendings_categories_get,
    spendings_get_all,
    spendings_summary_chart_get,
    spendings_summary_get,
)
from app.core.config import settings
from app.schemas.transaction_category_schemas import TransactionsOnDeleteActions

router = APIRouter()
templates = Jinja2Templates(directory="./templates")


@router.get("/spendings/")
async def spendings_page(
    request: Request,
    spendings=Depends(spendings_summary_get),
):
    return templates.TemplateResponse(
        name="spendings_main.html",
        context={
            "request": request,
            "title": "spendings",
            "summary": spendings,
        },
    )


@router.get("/spendings/create/")
async def spendings_create_page(
    request: Request,
    categories=Depends(spendings_categories_get),
):
    return templates.TemplateResponse(
        name="transaction_create.html",
        context={
            "request": request,
            "transaction_name": "spending",
            "user_categories": categories,
            "api_create_url": f"{settings.api.prefix_v1}/spendings/",
            "success_redirect_url": "/pages/spendings/",
        },
    )


@router.get("/spendings/categories/create/")
async def spendings_category_create_page(
    request: Request,
):
    return templates.TemplateResponse(
        name="tx_category_create.html",
        context={
            "request": request,
            "title": "Create category",
            "tx_type_multiple": "spendings",
            "api_create_url": f"{settings.api.prefix_v1}/spendings/categories/",
            "success_redirect_url": "/pages/spendings/",
        },
    )


@router.get("/spendings/detail/{transaction_id}/")
async def spending_get_page(
    request: Request,
    transaction_id: int,
    categories=Depends(spendings_categories_get),
):
    async with aiohttp.ClientSession() as session:
        url = f"http://0.0.0.0:8000{settings.api.prefix_v1}/spendings/{transaction_id}/"
        async with session.get(url, cookies=request.cookies) as resp:
            spending_info = await resp.json()

    return templates.TemplateResponse(
        name="transaction_info.html",
        context={
            "request": request,
            "transaction_info": spending_info,
            "user_categories": categories,
            "title": "Spending info",
            "transaction_type": "spending",
            "tx_type_multiple": "spendings",
            "transactions_get_url": f"{settings.api.prefix_v1}/spendings/",
            "tx_delete_url": f"{settings.api.prefix_v1}/spendings/{transaction_id}/",
            "api_update_tx_url": f"{settings.api.prefix_v1}/spendings/{transaction_id}/",
            "success_redirect_url": "/pages/spendings/",
        },
    )


@router.get("/spendings/all/")
async def spendings_get_all_page(
    request: Request,
    all_spendings=Depends(spendings_get_all),
):
    return templates.TemplateResponse(
        name="transactions_all.html",
        context={
            "request": request,
            "transactions": all_spendings,
            "title": "All spendings",
            "tx_type_multiple": "spendings",
            "page_size": 20,
            "transactions_get_url": f"{settings.api.prefix_v1}/spendings/",
            "tx_get_details_funcname": "spending_get_page",
            "tx_get_details_url_prefix": "/pages/spendings/detail/",
        },
    )


@router.get("/spendings/categories/")
async def spending_categories_page(
    request: Request,
    categories=Depends(spendings_categories_get),
):
    on_delete_actions = [str(i) for i in TransactionsOnDeleteActions]

    return templates.TemplateResponse(
        name="tx_categories.html",
        context={
            "request": request,
            "categories": categories,
            "title": "Spendings categories",
            "categories_type": "spendings",
            "api_update_tx_category_url": f"{settings.api.prefix_v1}/spendings/categories/",
            "api_delete_tx_category_url": f"{settings.api.prefix_v1}/spendings/categories/",
            "on_delete_actions": on_delete_actions,
        },
    )


@router.get("/spendings/summary/full/")
async def spending_summary_full(
    request: Request,
    summary=Depends(spendings_summary_get),
    chart=Depends(spendings_summary_chart_get),
):
    chart_base64 = base64.b64encode(chart.body).decode("utf-8")
    return templates.TemplateResponse(
        name="summary_full.html",
        context={
            "request": request,
            "title": "Spendings summary",
            "time_interval": "All time",
            "summary": summary,
            "chart": chart_base64,
            "chart_width": "500",
            "get_summary_url": f"{settings.api.prefix_v1}/spendings/summary/",
            "get_summary_chart_url": f"{settings.api.prefix_v1}/spendings/summary/chart/",
        },
    )


@router.get("/spendings/summary/annual/")
async def spending_summary_annual(
    request: Request,
):
    year = date.today().year

    async with aiohttp.ClientSession() as session:
        url_prefix = (
            f"http://0.0.0.0:8000{settings.api.prefix_v1}/spendings/summary"
        )
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
            "title": "Spendings summary",
            "time_interval": "Annual",
            "tx_type_multiple": "spendings",
            "summary": summary,
            "chart": chart_base64,
            "chart_width": "700",
            "get_summary_prefix": f"{settings.api.prefix_v1}/spendings/summary",
        },
    )


@router.get("/spendings/summary/monthly/")
async def spending_summary_monthly(
    request: Request,
):
    year = date.today().year
    month = date.today().month

    async with aiohttp.ClientSession() as session:
        url_prefix = (
            f"http://0.0.0.0:8000{settings.api.prefix_v1}/spendings/summary"
        )
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
            "title": "Spendings summary",
            "time_interval": "Monthly",
            "tx_type_multiple": "spendings",
            "summary": summary,
            "chart": chart_base64,
            "chart_width": "700",
            "get_summary_prefix": f"{settings.api.prefix_v1}/spendings/summary",
        },
    )
