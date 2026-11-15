import re
import unicodedata
from dataclasses import dataclass

from src.domain.errors import InvalidQuestion, PointNotFound
from src.domain.models import Point, PointPage, StatusPonto, TipoResiduo
from src.domain.ports import LLMPort, PointRepository

REFUSAL_MESSAGE = (
    "Posso ajudar apenas com perguntas sobre descarte de residuos e pontos de coleta."
)
NOT_FOUND_MESSAGE = "Nao encontrei ponto de coleta aberto para esse tipo de residuo."
UNVERIFIED_MESSAGE = (
    "Nao consegui confirmar um ponto de coleta valido para responder. "
    "Consulte a lista de pontos."
)

TIPO_KEYWORDS = {
    TipoResiduo.PILHAS: ("pilha", "bateria"),
    TipoResiduo.OLEO: ("oleo",),
    TipoResiduo.MOVEIS: ("movel", "moveis", "sofa", "armario", "colchao", "cama"),
    TipoResiduo.ENTULHO: ("entulho", "obra", "tijolo", "concreto"),
    TipoResiduo.ELETRONICOS: (
        "eletronic",
        "celular",
        "computador",
        "notebook",
        "televis",
        "tv",
        "cabo",
    ),
    TipoResiduo.RECICLAVEIS: (
        "recicl",
        "papel",
        "papelao",
        "plastico",
        "vidro",
        "metal",
        "lata",
        "garrafa",
    ),
}

GENERAL_KEYWORDS = (
    "descart",
    "lixo",
    "residuo",
    "coleta",
    "ecoponto",
    "ponto",
    "cooperativa",
    "jogar",
)


def sanitize_question(text: str) -> str:
    cleaned = re.sub(r"[\[\]{}<>`]", " ", text)
    cleaned = re.sub(r"[\x00-\x1f\x7f]", " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    if not cleaned:
        raise InvalidQuestion("pergunta vazia")
    return cleaned


def _tokens(text: str) -> list[str]:
    base = unicodedata.normalize("NFKD", text.lower())
    base = "".join(c for c in base if not unicodedata.combining(c))
    return re.findall(r"[a-z0-9]+", base)


def _starts_with_any(tokens: list[str], keywords: tuple[str, ...]) -> bool:
    return any(token.startswith(keyword) for token in tokens for keyword in keywords)


def detect_tipos(tokens: list[str]) -> list[TipoResiduo]:
    return [
        tipo for tipo, words in TIPO_KEYWORDS.items() if _starts_with_any(tokens, words)
    ]


def build_prompt(question: str, points: list[Point]) -> str:
    lines = [
        f"[ID {p.id}] {p.nome} | {p.endereco} | "
        f"aceita: {', '.join(t.value for t in p.tipos_aceitos)} | "
        f"horario: {p.horario}"
        for p in points
    ]
    return (
        "Voce e um assistente de descarte de residuos de uma prefeitura. "
        "Responda em portugues, em ate 3 frases, usando somente os pontos "
        "listados abaixo. Cite cada ponto usado no formato [ID numero], "
        "copiando o numero da lista. Se nenhum ponto servir, diga que nao "
        "encontrou. Nao invente enderecos nem horarios.\n\n"
        "PONTOS:\n" + "\n".join(lines) + "\n\nPERGUNTA DO CIDADAO:\n" + question
    )


@dataclass(frozen=True)
class AskResult:
    resposta: str
    pontos_citados: tuple[int, ...]
    recusada: bool


class PointService:
    def __init__(self, repository: PointRepository):
        self._repository = repository

    def get(self, point_id: int) -> Point:
        point = self._repository.get(point_id)
        if point is None:
            raise PointNotFound(point_id)
        return point

    def list(
        self,
        limit: int,
        offset: int,
        tipo: TipoResiduo | None,
        status: StatusPonto | None,
    ) -> PointPage:
        return self._repository.list(limit, offset, tipo, status)


class AskService:
    def __init__(self, repository: PointRepository, llm: LLMPort, max_points: int = 5):
        self._repository = repository
        self._llm = llm
        self._max_points = max_points

    def ask(self, pergunta: str) -> AskResult:
        question = sanitize_question(pergunta)
        tokens = _tokens(question)
        tipos = detect_tipos(tokens)
        if not tipos and not _starts_with_any(tokens, GENERAL_KEYWORDS):
            return AskResult(REFUSAL_MESSAGE, (), True)
        points = self._retrieve(tipos)
        if not points:
            return AskResult(NOT_FOUND_MESSAGE, (), False)
        answer = self._llm.generate(build_prompt(question, points))
        return self._apply_guardrail(answer, points)

    def _retrieve(self, tipos: list[TipoResiduo]) -> list[Point]:
        page = self._repository.list(50, 0, None, StatusPonto.ABERTO)
        matches = [
            p for p in page.items if not tipos or any(t in p.tipos_aceitos for t in tipos)
        ]
        return matches[: self._max_points]

    @staticmethod
    def _apply_guardrail(answer: str, points: list[Point]) -> AskResult:
        cited = [int(i) for i in re.findall(r"\[ID (\d+)\]", answer)]
        allowed = {p.id for p in points}
        if not cited or any(i not in allowed for i in cited):
            return AskResult(UNVERIFIED_MESSAGE, (), False)
        return AskResult(answer.strip(), tuple(dict.fromkeys(cited)), False)