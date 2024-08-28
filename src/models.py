from abc import abstractmethod
from typing import Annotated

from sqlalchemy.orm import as_declarative, mapped_column


int_primary_key = Annotated[int, mapped_column(primary_key=True)]


@as_declarative()
class BaseModel:
    """Base model"""

    @abstractmethod
    def __repr__(self):
        pass
