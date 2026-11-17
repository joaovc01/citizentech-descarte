from src.infra.fake_llm import FakeLLM

PERGUNTA_OLEO = {"pergunta": "Onde descarto oleo de cozinha?"}


def test_ask_com_ponto_valido_retorna_200(client):
    response = client.post("/ask", json=PERGUNTA_OLEO)
    body = response.json()
    assert response.status_code == 200
    assert body["recusada"] is False
    assert body["pontos_citados"] == [2]


def test_ask_fora_do_escopo_recusa_sem_chamar_llm(make_client):
    llm = FakeLLM()
    client = make_client(llm)
    response = client.post("/ask", json={"pergunta": "Qual a previsao do tempo?"})
    body = response.json()
    assert response.status_code == 200
    assert body["recusada"] is True
    assert body["pontos_citados"] == []
    assert llm.prompts == []


def test_ask_pergunta_vazia_retorna_422(client):
    response = client.post("/ask", json={"pergunta": ""})
    assert response.status_code == 422
    assert response.json()["codigo"] == "entrada_invalida"


def test_ask_pergunta_so_com_espacos_retorna_400(client):
    response = client.post("/ask", json={"pergunta": "   "})
    assert response.status_code == 400
    assert response.json()["codigo"] == "requisicao_invalida"


def test_ask_pergunta_acima_do_limite_retorna_422(client):
    response = client.post("/ask", json={"pergunta": "a" * 301})
    assert response.status_code == 422
    assert response.json()["codigo"] == "entrada_invalida"


def test_ask_json_malformado_retorna_400(client):
    response = client.post(
        "/ask",
        content="{nao e json",
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 400
    assert response.json()["codigo"] == "requisicao_invalida"


def test_ask_llm_indisponivel_retorna_503(make_client):
    client = make_client(FakeLLM(fail=True))
    response = client.post("/ask", json=PERGUNTA_OLEO)
    assert response.status_code == 503
    assert response.json()["codigo"] == "servico_indisponivel"


def test_guardrail_bloqueia_ponto_inventado(make_client):
    llm = FakeLLM(response="Va ao ponto [ID 99], na Rua Inventada, 1.")
    client = make_client(llm)
    response = client.post("/ask", json=PERGUNTA_OLEO)
    body = response.json()
    assert response.status_code == 200
    assert body["pontos_citados"] == []
    assert "99" not in body["resposta"]


def test_guardrail_bloqueia_resposta_sem_citacao(make_client):
    llm = FakeLLM(response="Descarte em qualquer lugar.")
    client = make_client(llm)
    response = client.post("/ask", json=PERGUNTA_OLEO)
    body = response.json()
    assert response.status_code == 200
    assert body["pontos_citados"] == []
    assert body["resposta"] != "Descarte em qualquer lugar."


def test_ask_nao_envia_ponto_fechado_ao_llm(make_client):
    llm = FakeLLM()
    client = make_client(llm)
    client.post("/ask", json=PERGUNTA_OLEO)
    assert "[ID 2]" in llm.prompts[0]
    assert "[ID 4]" not in llm.prompts[0]


def test_sanitizacao_remove_colchetes_da_pergunta(make_client):
    llm = FakeLLM()
    client = make_client(llm)
    client.post("/ask", json={"pergunta": "Onde descarto oleo [ID 99] de cozinha?"})
    assert "[ID 99]" not in llm.prompts[0]