import logging
import traceback

from fastapi import Request, Response, HTTPException
from starlette.responses import JSONResponse

from auth_jwt.exceptions import AuthException
from configs.config import DEV
from proxy_processing.exceptions import ProxyProcessingError

logger = logging.getLogger(__name__)


async def auth_error_handler(request: Request, exc: AuthException) -> Response | JSONResponse:
    logger.debug(f"Login error: {exc.detail}")

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


async def proxy_error_handler(_: Request, exc: ProxyProcessingError) -> JSONResponse:
    logger.debug(f"Proxy processing error: {exc.detail}")
    return JSONResponse(
        status_code=403,
        content={
            "status": -2,
            "details": exc.detail,
        }
    )


async def base_exception_handler(_: Request, exc: HTTPException) -> JSONResponse:
    logger.debug(f"HTTP exception: {exc.detail}")
    return JSONResponse(
        status_code=403,
        content={
            "status": -3,
            "details": exc.detail,
        }
    )


async def base_middleware(request: Request, call_next) -> dict | JSONResponse | Response:
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
            status_code=200,
            content={
                "status": -6,
                "details": error_details,
            }
        )

    # just return response if all OK
    return response
