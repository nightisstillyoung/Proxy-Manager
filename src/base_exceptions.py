from fastapi import HTTPException
from abc import ABC


class BaseAppError(HTTPException, ABC):
    """All controlled exceptions should be inherited from it"""
    ...











