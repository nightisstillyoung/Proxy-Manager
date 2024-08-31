import traceback
import logging
from fastapi import FastAPI, Request, Response, HTTPException
from starlette.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from configs.config import DEV, website_config
from handlers import auth_error_handler, proxy_error_handler, base_exception_handler, base_middleware
from proxy_processing.exceptions import ProxyProcessingError
from proxy_processing.router import router as proxy_router
from pages.router import router as page_router
from auth_jwt.router import router as jwt_router
from auth_jwt.exceptions import AuthException
from log import logger_setup



# setup logger
logger = logging.getLogger(__name__)

# settings handlers for console and file
logger.addHandler(logger_setup.file_handler)
logger.addHandler(logger_setup.console_handler)

# setup config
logging.basicConfig(**logger_setup.log_conf)



app = FastAPI(
    title="Proxy Manager",
    version="0.1.2"
)

# add exception handlers
app.add_exception_handler(AuthException, auth_error_handler)
app.add_exception_handler(ProxyProcessingError, proxy_error_handler)
app.add_exception_handler(HTTPException, base_exception_handler)

# add middleware
app.add_middleware("http", base_middleware)


# CORS
origins = [
    *website_config['cors_origins']
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# routers
app.include_router(proxy_router)
app.include_router(page_router)
app.include_router(jwt_router)

# static content
app.mount("/static", StaticFiles(directory="frontend/static"), name="static")
app.mount("/js", StaticFiles(directory="frontend/js"), name="js")
app.mount("/styles", StaticFiles(directory="frontend/styles"), name="styles")
app.mount("/vendor", StaticFiles(directory="frontend/vendor"), name="vendor")
