from datetime import date

from pydantic import BaseModel, ConfigDict, Field

from src.domain.models import StatusPonto, TipoResiduo


class PointOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    endereco: str
    tipos_aceitos: list[TipoResiduo]
    horario: str
    status: StatusPonto
    atualizado_em: date


class PointListOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    items: list[PointOut]
    total: int
    limit: int
    offset: int


class AskIn(BaseModel):
    pergunta: str = Field(min_length=1, max_length=300)


class AskOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    resposta: str
    pontos_citados: list[int]
    recusada: bool


class HealthOut(BaseModel):
    status: str = "ok"


class ErrorOut(BaseModel):
    codigo: str
    mensagem: str
    detalhes: list[str] = []