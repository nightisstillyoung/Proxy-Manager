from abc import abstractmethod
from sqlalchemy.orm import as_declarative


@as_declarative()
class BaseModel:
    """Base model"""

    @abstractmethod
    def __repr__(self):
        pass
