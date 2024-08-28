############################################################################
# this script inserts default Admin user into database with default password
# DO NOT RUN IT MANUALLY, IT RUNS AUTOMATICALLY FROM DOCKER
############################################################################

import asyncio
import logging
import os

from auth_jwt.auth_schemas import RegisterUsernameScheme
from auth_jwt.repository import AuthRepo

logger = logging.getLogger(__name__)

# check if admin already exists
logger.info("Init database script started")


async def run():
    if os.access(".installed", os.R_OK):  # script runs only at first start
        return

    if await AuthRepo.is_user_exists("admin"):
        logger.warning("Init script started when admin user already exists. Stopping...")
        exit()

    user: RegisterUsernameScheme = RegisterUsernameScheme(username="admin", password="password")

    await AuthRepo.create_user(user)

    logger.info("Admin default account created.")
    logger.warning("BE SURE YOU CHANGE YOUR DEFAULT PASSWORD")
    open(".installed", mode="w").close()


asyncio.run(run())
logger.info("Init database script finished")
