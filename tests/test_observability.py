import logging

from src.infra.fake_llm import FakeLLM

LOGGER = "citizentech.api"


def messages(caplog):
    return [r.getMessage() for r in caplog.records if r.name == LOGGER]


def test_cada_requisicao_registra_status_e_latencia(client, caplog):
    with caplog.at_level(logging.INFO, logger=LOGGER):
        client.get("/points/1")
    assert any(
        "event=request" in m and "status=200" in m and "latency_ms=" in m
        for m in messages(caplog)
    )


def test_erro_404_tambem_e_registrado(client, caplog):
    with caplog.at_level(logging.INFO, logger=LOGGER):
        client.get("/points/9999")
    assert any("status=404" in m for m in messages(caplog))


def test_ask_registra_recusa_sem_expor_a_pergunta(client, caplog):
    with caplog.at_level(logging.INFO, logger=LOGGER):
        client.post("/ask", json={"pergunta": "Qual a previsao do tempo?"})
    logs = messages(caplog)
    assert any("event=ask" in m and "recusada=True" in m for m in logs)
    assert not any("previsao" in m for m in logs)


def test_ask_registra_bloqueio_do_guardrail(make_client, caplog):
    client = make_client(FakeLLM(response="Va ao ponto [ID 99]."))
    with caplog.at_level(logging.INFO, logger=LOGGER):
        client.post("/ask", json={"pergunta": "Onde descarto oleo de cozinha?"})
    assert any("bloqueada_pelo_guardrail=True" in m for m in messages(caplog))


def test_llm_indisponivel_gera_aviso_no_log(make_client, caplog):
    client = make_client(FakeLLM(fail=True))
    with caplog.at_level(logging.WARNING, logger=LOGGER):
        client.post("/ask", json={"pergunta": "Onde descarto oleo de cozinha?"})
    assert any(
        r.levelno == logging.WARNING and "event=llm_indisponivel" in r.getMessage()
        for r in caplog.records
    )