from abc import ABC, abstractmethod

from src.domain.models import Point, PointPage, StatusPonto, TipoResiduo


class PointRepository(ABC):
    @abstractmethod
    def get(self, point_id: int) -> Point | None:
        ...

    @abstractmethod
    def list(
        self,
        limit: int,
        offset: int,
        tipo: TipoResiduo | None,
        status: StatusPonto | None,
    ) -> PointPage:
        ...


class LLMPort(ABC):
    @abstractmethod
    def generate(self, prompt: str) -> str:
        ...