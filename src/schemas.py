from abc import abstractmethod
from typing import Any
from pydantic import BaseModel as PydanticBaseModel


class SBase(PydanticBaseModel):
    """Abstract base class of all pydantic models"""

    @abstractmethod
    def __repr__(self) -> str:
        pass


class SResponseAPI(SBase):
    """
    Status: int
        0 - OK
        <0 - error
    data: Any = None
    details: Any = None
    """

    status: int  # 0 for OK, < 0 for errors
    data: Any = None
    details: Any = None

    def __repr__(self) -> str:
        return str(self.model_dump())

