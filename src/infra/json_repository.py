import json
from datetime import date
from pathlib import Path

from src.domain.models import Point, PointPage, StatusPonto, TipoResiduo
from src.domain.ports import PointRepository


class JsonPointRepository(PointRepository):
    def __init__(self, path: str | Path):
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
        self._points = tuple(self._build(item) for item in raw)

    @staticmethod
    def _build(item: dict) -> Point:
        return Point(
            id=item["id"],
            nome=item["nome"],
            endereco=item["endereco"],
            tipos_aceitos=tuple(TipoResiduo(t) for t in item["tipos_aceitos"]),
            horario=item["horario"],
            status=StatusPonto(item["status"]),
            atualizado_em=date.fromisoformat(item["atualizado_em"]),
        )

    def get(self, point_id: int) -> Point | None:
        for point in self._points:
            if point.id == point_id:
                return point
        return None

    def list(
        self,
        limit: int,
        offset: int,
        tipo: TipoResiduo | None,
        status: StatusPonto | None,
    ) -> PointPage:
        filtered = [
            p
            for p in self._points
            if (tipo is None or tipo in p.tipos_aceitos)
            and (status is None or p.status == status)
        ]
        page = tuple(filtered[offset : offset + limit])
        return PointPage(items=page, total=len(filtered), limit=limit, offset=offset)