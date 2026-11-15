from dataclasses import dataclass
from datetime import date
from enum import Enum


class TipoResiduo(str, Enum):
    PILHAS = "pilhas"
    OLEO = "oleo"
    MOVEIS = "moveis"
    ENTULHO = "entulho"
    ELETRONICOS = "eletronicos"
    RECICLAVEIS = "reciclaveis"


class StatusPonto(str, Enum):
    ABERTO = "aberto"
    FECHADO = "fechado"
    MANUTENCAO = "manutencao"


@dataclass(frozen=True)
class Point:
    id: int
    nome: str
    endereco: str
    tipos_aceitos: tuple[TipoResiduo, ...]
    horario: str
    status: StatusPonto
    atualizado_em: date


@dataclass(frozen=True)
class PointPage:
    items: tuple[Point, ...]
    total: int
    limit: int
    offset: int