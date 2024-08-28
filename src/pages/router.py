import logging
from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
from starlette.responses import HTMLResponse
from random import randint

from configs.config import DEV
from proxy_processing.repository import get_alive, count_rows, get_min_max_latency
from tasks.manager import async_celery_manager
from auth_jwt.dependencies import check_auth

logger = logging.getLogger(__name__)

router = APIRouter(
    tags=["pages"]
)

templates = Jinja2Templates(directory="frontend/templates")


@router.get("/", response_class=HTMLResponse)
async def index(request: Request, _: str = Depends(check_auth)):
    context: dict = {"proxies": [str(proxy) for proxy in await get_alive()]}

    # progress used for progressbar
    context.update(await async_celery_manager.get_progress())
    logger.debug(f"Set context for /index.html\n {context=}")

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context=context
    )


@router.get("/login")
def login(request: Request):
    context: dict = {}

    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context=context
    )


@router.get("/change-password")
def change_password(request: Request, _: str = Depends(check_auth)):
    context: dict = {}

    return templates.TemplateResponse(
        request=request,
        name="change_password.html",
        context=context
    )


@router.get("/advanced/search/")
async def advanced_search(request: Request, _: str = Depends(check_auth)):
    context: dict = {"total_proxies": await count_rows()}

    context.update(await get_min_max_latency())

    context["latency_max"] = round(context["latency_max"] if context["latency_max"] else 999, 3)
    context["latency_min"] = round(context["latency_min"] if context["latency_min"] else 0, 3)

    return templates.TemplateResponse(
        request=request,
        name="advanced_search.html",
        context=context
    )
