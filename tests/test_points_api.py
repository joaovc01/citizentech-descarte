def test_health_retorna_ok(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_get_point_existente_retorna_200(client):
    response = client.get("/points/1")
    body = response.json()
    assert response.status_code == 200
    assert body["id"] == 1
    assert body["nome"] == "Ecoponto Vila Nova"
    assert body["status"] == "aberto"


def test_get_point_inexistente_retorna_404_padronizado(client):
    response = client.get("/points/9999")
    body = response.json()
    assert response.status_code == 404
    assert body["codigo"] == "nao_encontrado"
    assert "9999" in body["mensagem"]


def test_get_point_id_invalido_retorna_422(client):
    response = client.get("/points/0")
    assert response.status_code == 422
    assert response.json()["codigo"] == "entrada_invalida"


def test_listagem_pagina_com_limit_e_offset(client):
    response = client.get("/points", params={"limit": 2, "offset": 2})
    body = response.json()
    assert response.status_code == 200
    assert [p["id"] for p in body["items"]] == [3, 4]
    assert body["total"] == 8
    assert body["limit"] == 2
    assert body["offset"] == 2


def test_listagem_filtra_por_tipo_e_status(client):
    response = client.get("/points", params={"tipo": "oleo", "status": "aberto"})
    body = response.json()
    assert response.status_code == 200
    assert [p["id"] for p in body["items"]] == [2, 7, 8]
    assert body["total"] == 3


def test_listagem_tipo_invalido_retorna_422(client):
    response = client.get("/points", params={"tipo": "xyz"})
    assert response.status_code == 422
    assert response.json()["codigo"] == "entrada_invalida"


def test_listagem_limit_fora_do_intervalo_retorna_422(client):
    assert client.get("/points", params={"limit": 0}).status_code == 422
    assert client.get("/points", params={"limit": 51}).status_code == 422