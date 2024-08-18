import logging
from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
from starlette.responses import HTMLResponse

from auth.dependencies import auth_data_dependency
from proxy_processing.repository import get_alive, count_rows
from tasks.manager import async_celery_manager

logger = logging.getLogger(__name__)

router = APIRouter(
    tags=["pages"]
)

templates = Jinja2Templates(directory="frontend/templates")


@router.get("/", response_class=HTMLResponse)
async def index(request: Request, _: str = Depends(auth_data_dependency)):
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


@router.get("/advanced/search/")
async def advanced_search(request: Request, _: str = Depends(auth_data_dependency)):
    context: dict = {"total_proxies": await count_rows()}

    return templates.TemplateResponse(
        request=request,
        name="advanced_search.html",
        context=context
    )
