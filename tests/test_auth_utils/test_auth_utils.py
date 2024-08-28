import random
import pytest
from jwt import InvalidAlgorithmError, DecodeError, InvalidSignatureError

from src.auth_jwt.utils import check_pwd, hash_pwd, decode_jwt, encode_jwt


##############################
# tests jwt utils
##############################

wrong_jwt = ("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
             ".eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ"
             ".SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c")


def test_hash_check_pwd_good(passwords):
    for password in passwords:
        hashed: str = hash_pwd(password)

        assert check_pwd(password, hashed)


def test_hash_check_pwd_bad(passwords):
    for password in passwords:
        hashed: str = hash_pwd(password + str(random.randint(0, 99999)))

        assert not check_pwd(password, hashed)


def test_jwt_good(passwords):
    for password in passwords:
        jwt: str = encode_jwt({"password": hash_pwd(password)})

        payload: dict[str, str] = decode_jwt(jwt)

        assert check_pwd(password, payload["password"])


@pytest.mark.parametrize(
    "bad_jwt, expected",
    [
        ("bad_token", pytest.raises(DecodeError)),
        (wrong_jwt, pytest.raises(InvalidAlgorithmError))
    ]
)
def test_jwt_bad(bad_jwt, expected):
    with expected:
        decode_jwt(bad_jwt)
