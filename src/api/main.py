from fastapi import FastAPI, Path, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from src.api.schemas import (
    AskIn,
    AskOut,
    ErrorOut,
    HealthOut,
    PointListOut,
    PointOut,
)
from src.domain.errors import InvalidQuestion, LLMUnavailable, PointNotFound
from src.domain.models import StatusPonto, TipoResiduo
from src.domain.ports import LLMPort, PointRepository
from src.domain.services import AskService, PointService
from src.infra.factory import build_llm, build_repository


def error_response(
    status_code: int,
    codigo: str,
    mensagem: str,
    detalhes: list[str] | None = None,
) -> JSONResponse:
    body = ErrorOut(codigo=codigo, mensagem=mensagem, detalhes=detalhes or [])
    return JSONResponse(status_code=status_code, content=body.model_dump())


def create_app(
    repository: PointRepository | None = None,
    llm: LLMPort | None = None,
) -> FastAPI:
    if repository is None:
        repository = build_repository()
    if llm is None:
        llm = build_llm()
    points = PointService(repository)
    asker = AskService(repository, llm)

    app = FastAPI(title="Guia de Descarte Correto - CitizenTech", version="1.0.0")

    @app.exception_handler(PointNotFound)
    async def handle_not_found(request: Request, exc: PointNotFound) -> JSONResponse:
        return error_response(404, "nao_encontrado", str(exc))

    @app.exception_handler(InvalidQuestion)
    async def handle_invalid_question(
        request: Request, exc: InvalidQuestion
    ) -> JSONResponse:
        return error_response(400, "requisicao_invalida", str(exc))

    @app.exception_handler(LLMUnavailable)
    async def handle_llm_unavailable(
        request: Request, exc: LLMUnavailable
    ) -> JSONResponse:
        return error_response(
            503, "servico_indisponivel", "O modelo de linguagem esta indisponivel"
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        errors = exc.errors()
        details = [f"{'.'.join(str(p) for p in e['loc'])}: {e['msg']}" for e in errors]
        if any(e["type"] == "json_invalid" for e in errors):
            return error_response(
                400, "requisicao_invalida", "Corpo da requisicao malformado", details
            )
        return error_response(
            422, "entrada_invalida", "Parametro ou campo invalido", details
        )

    @app.get("/health", response_model=HealthOut, tags=["operacao"])
    def health() -> HealthOut:
        return HealthOut()

    @app.get("/points", response_model=PointListOut, tags=["pontos"])
    def list_points(
        limit: int = Query(10, ge=1, le=50),
        offset: int = Query(0, ge=0),
        tipo: TipoResiduo | None = None,
        status: StatusPonto | None = None,
    ) -> PointListOut:
        return PointListOut.model_validate(points.list(limit, offset, tipo, status))

    @app.get("/points/{id}", response_model=PointOut, tags=["pontos"])
    def get_point(id: int = Path(ge=1)) -> PointOut:
        return PointOut.model_validate(points.get(id))

    @app.post("/ask", response_model=AskOut, tags=["ia"])
    def ask(body: AskIn) -> AskOut:
        return AskOut.model_validate(asker.ask(body.pergunta))

    return app


app = create_app()