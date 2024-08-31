import logging
from fastapi import APIRouter, Depends, Response

from auth_jwt.models import UserModel
from auth_jwt.schemas import ChangePasswordScheme
from auth_jwt.dependencies import validate_auth_user, check_auth
from auth_jwt.exceptions import ChangePasswordError
from auth_jwt.repository import AuthRepo
from auth_jwt.utils import check_pwd
from configs.config import jwt_config
from base_schemas import SResponseAPI

router: APIRouter = APIRouter(prefix="/jwt", tags=["JWT"])

logger = logging.getLogger(__name__)


@router.post("/issue")
async def issue_jwt(response: Response, jwt_token: str = Depends(validate_auth_user)):
    """Login"""
    response.status_code = 303
    response.headers["Location"] = "/"

    exp: int | float = jwt_config["expire_hours"] * 60 * 60 if jwt_config["expire_hours"] > 0 else None

    response.set_cookie("auth", jwt_token, expires=exp)


@router.get("/delete")
async def delete_jwt(response: Response):
    """Logout"""
    response.status_code = 303
    response.headers["Location"] = "/login"

    response.delete_cookie("auth")


@router.patch(
    "/change-password",
    response_model=SResponseAPI,
    response_model_exclude_unset=True
)
async def change_password(
        change_data: ChangePasswordScheme,
        user: UserModel = Depends(check_auth)
):
    """Change password"""

    # check user's password with passed old_password
    if not check_pwd(change_data.password, user.password):
        raise ChangePasswordError()

    await AuthRepo.set_new_password(change_data.new_password, user.id)

    return {"status": 0, "data": None}
