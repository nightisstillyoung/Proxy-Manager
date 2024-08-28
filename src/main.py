import traceback
import logging
from fastapi import FastAPI, Request, Response
from starlette.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from configs.config import DEV, website_config
from proxy_processing.exceptions import ProxyProcessingError
from proxy_processing.router import router as proxy_router
from pages.router import router as page_router
from auth_jwt.router import router as jwt_router
from auth_jwt.exceptions import AuthException
from log import logger_setup

app = FastAPI(
    title="Proxy Manager",
    version="0.1.1"
)

logger = logging.getLogger(__name__)

# settings handlers for console and file
logger.addHandler(logger_setup.file_handler)
logger.addHandler(logger_setup.console_handler)

# setup config
logging.basicConfig(**logger_setup.log_conf)


@app.exception_handler(AuthException)
async def auth_error_handler(request: Request, exc: AuthException):
    if not request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return Response(status_code=302, headers={"Location": "/login"})
    else:
        return JSONResponse(
            status_code=403,
            content={
                "status": -1,
                "details": exc.detail,
            }
        )


@app.exception_handler(ProxyProcessingError)
async def proxy_error_handler(request: Request, exc: ProxyProcessingError):
    if not request.headers.get("accept") == "application/json":
        return Response(status_code=302, headers={"Location": "/login"})
    else:
        return JSONResponse(
            status_code=403,
            content={
                "status": -2,
                "details": exc.detail,
            }
        )


@app.middleware("http")
async def error_handling_middleware(request: Request, call_next) -> dict | JSONResponse | Response:
    """
    Handles errors and makes them compatible for api
    -1 - light error
    -6 - uncaught error

    Lower status means harder error
    """

    try:
        # calls endpoint function
        response = await call_next(request)
    except Exception as e:
        print("ERROR")
        logger.exception("Error")

        # if development
        if DEV:
            raise e

        # get traceback
        error_details = traceback.format_exc()
        return JSONResponse(
            status_code=500,
            content={
                "status": -6,
                "details": error_details,
            }
        )

    # just return response if all OK
    return response


# CORS
origins = [
    *website_config['cors_origins']
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# routers
app.include_router(proxy_router)
app.include_router(page_router)
app.include_router(jwt_router)

# static
app.mount("/static", StaticFiles(directory="frontend/static"), name="static")
app.mount("/js", StaticFiles(directory="frontend/js"), name="js")
app.mount("/styles", StaticFiles(directory="frontend/styles"), name="styles")
app.mount("/vendor", StaticFiles(directory="frontend/vendor"), name="vendor")
