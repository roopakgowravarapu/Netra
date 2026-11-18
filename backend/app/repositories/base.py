"""Base repository interface defining standard CRUD operations."""

from typing import Generic, List, Optional, TypeVar
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)
ID = TypeVar("ID")


class BaseRepository(Generic[T, ID]):
    """Abstract base repository contract."""

    def get_by_id(self, entity_id: ID) -> Optional[T]:
        raise NotImplementedError

    def get_all(self) -> List[T]:
        raise NotImplementedError

    def save(self, entity: T) -> T:
        raise NotImplementedError

    def delete(self, entity_id: ID) -> bool:
        raise NotImplementedError

    def clear(self) -> None:
        raise NotImplementedError
