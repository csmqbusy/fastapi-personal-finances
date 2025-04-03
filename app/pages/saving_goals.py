import aiohttp
from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates

from app.api.v1.routes.saving_goals_routes import saving_goals_get_all
from app.core.config import settings
from app.schemas.saving_goals_schemas import GoalStatus

router = APIRouter()
templates = Jinja2Templates(directory="./templates")


@router.get("/goals/")
async def saving_goals_page(
    request: Request,
    goals=Depends(saving_goals_get_all),
):
    goal_statuses = [i for i in GoalStatus]

    return templates.TemplateResponse(
        name="goals_main.html",
        context={
            "request": request,
            "title": "Saving goals",
            "goals": goals,
            "goal_statuses": goal_statuses,
            "goals_get_url": f"{settings.api.prefix_v1}/goals/",
            "goal_details_funcname": "saving_goal_details_page",
            "goal_get_details_url_prefix": "/pages/goals/",
        },
    )


@router.get("/goals/create/")
async def saving_goal_create_page(
    request: Request,
):
    return templates.TemplateResponse(
        name="goals_create.html",
        context={
            "request": request,
            "title": "Saving goals",
            "api_create_url": f"{settings.api.prefix_v1}/goals/",
            "success_redirect_url": "/pages/goals/",
        },
    )


@router.get("/goals/{goal_id}")
async def saving_goal_details_page(
    request: Request,
    goal_id: int,
):
    async with aiohttp.ClientSession() as session:
        url = f"http://0.0.0.0:8000{settings.api.prefix_v1}/goals/{goal_id}/"
        async with session.get(url, cookies=request.cookies) as resp:
            goal_info = await resp.json()

        url = f"http://0.0.0.0:8000{settings.api.prefix_v1}/goals/progress/{goal_id}/"
        async with session.get(url, cookies=request.cookies) as resp:
            goal_progress = await resp.json()

    return templates.TemplateResponse(
        name="goal_details.html",
        context={
            "request": request,
            "goal_info": goal_info,
            "goal_progress": goal_progress,
            "title": "Saving goal details",
            "goal_delete_url": f"{settings.api.prefix_v1}/goals/{goal_id}/",
            "api_update_goal_url": f"{settings.api.prefix_v1}/goals/{goal_id}/",
            "success_redirect_url": "/pages/goals/",
        },
    )
