import httpx
import pytest

from src.domain.errors import LLMUnavailable
from src.domain.services import NOT_FOUND_MESSAGE, AskService
from src.infra import factory
from src.infra.fake_llm import FakeLLM
from src.infra.json_repository import JsonPointRepository
from src.infra.ollama_llm import OllamaAdapter

URL = "http://ollama.local"


def make_response(status, payload):
    return httpx.Response(status, json=payload, request=httpx.Request("POST", URL))


def fake_post(response=None, error=None):
    def post(url, json=None, timeout=None):
        if error is not None:
            raise error
        return response

    return post


def test_ollama_retorna_o_texto_da_resposta(monkeypatch):
    monkeypatch.setattr(httpx, "post", fake_post(make_response(200, {"response": "ola"})))
    assert OllamaAdapter(URL, "modelo").generate("oi") == "ola"


def test_ollama_envia_modelo_prompt_e_stream_false(monkeypatch):
    sent = {}

    def post(url, json=None, timeout=None):
        sent.update(url=url, json=json, timeout=timeout)
        return make_response(200, {"response": "ok"})

    monkeypatch.setattr(httpx, "post", post)
    OllamaAdapter(URL + "/", "llama", timeout=5).generate("pergunta")
    assert sent["url"] == f"{URL}/api/generate"
    assert sent["json"] == {"model": "llama", "prompt": "pergunta", "stream": False}
    assert sent["timeout"] == 5


@pytest.mark.parametrize(
    "failure",
    [
        {"error": httpx.ConnectError("sem conexao")},
        {"error": httpx.ReadTimeout("timeout")},
        {"response": make_response(500, {"erro": "interno"})},
        {"response": make_response(200, {"outro": "campo"})},
    ],
)
def test_ollama_converte_falhas_em_llm_unavailable(monkeypatch, failure):
    monkeypatch.setattr(httpx, "post", fake_post(**failure))
    with pytest.raises(LLMUnavailable):
        OllamaAdapter(URL, "modelo").generate("oi")


def test_factory_usa_fake_por_padrao(monkeypatch):
    monkeypatch.delenv("LLM_PROVIDER", raising=False)
    assert isinstance(factory.build_llm(), FakeLLM)


def test_factory_troca_para_ollama_so_com_configuracao(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "ollama")
    assert isinstance(factory.build_llm(), OllamaAdapter)


def test_factory_rejeita_provider_desconhecido(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "outro")
    with pytest.raises(ValueError):
        factory.build_llm()


def test_fake_llm_sem_id_no_prompt_responde_nao_encontrei():
    assert "Nao encontrei" in FakeLLM().generate("sem ponto algum")


def test_ask_sem_ponto_aberto_responde_sem_chamar_llm(tmp_path):
    empty = tmp_path / "points.json"
    empty.write_text("[]", encoding="utf-8")
    llm = FakeLLM()
    result = AskService(JsonPointRepository(empty), llm).ask("Onde descarto oleo?")
    assert result.resposta == NOT_FOUND_MESSAGE
    assert result.recusada is False
    assert result.pontos_citados == ()
    assert llm.prompts == []