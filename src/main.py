import traceback
import logging
from fastapi import FastAPI, Request, HTTPException, Response
from starlette.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from auth.exceptions import AuthError
from configs.config import DEV, website_config
from proxy_processing.router import router as proxy_router
from pages.router import router as page_router
from auth.router import router as auth_router
from log import logger_setup


app = FastAPI(
    title="Share proxies",
    version="0.1.0"
)


logger = logging.getLogger(__name__)

# settings handlers for console and file
logger.addHandler(logger_setup.file_handler)
logger.addHandler(logger_setup.console_handler)

# setup config
logging.basicConfig(**logger_setup.log_conf)



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
    except AuthError:
        # redirects if it was not ajax request
        if not request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return Response(status_code=302, headers={"Location": "/login"})
        else:
            return JSONResponse(
                status_code=403,
                content={
                    "status": -1,
                    "details": "You are not logged in or session expired. Please reload the page.",
                }
            )

    except HTTPException as e:
        # if it's not code error we pass it through
        raise e
    except Exception as e:
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
app.include_router(auth_router)

# static
app.mount("/static", StaticFiles(directory="frontend/static"), name="static")
app.mount("/js", StaticFiles(directory="frontend/js"), name="js")
app.mount("/styles", StaticFiles(directory="frontend/styles"), name="styles")
app.mount("/vendor", StaticFiles(directory="frontend/vendor"), name="vendor")
