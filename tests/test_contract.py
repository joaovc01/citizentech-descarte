from pathlib import Path

import pytest
import yaml
from jsonschema import Draft202012Validator

from src.domain.models import StatusPonto, TipoResiduo
from src.infra.fake_llm import FakeLLM

CONTRACT_FILE = Path(__file__).resolve().parent.parent / "contract" / "openapi.yaml"


@pytest.fixture(scope="module")
def spec():
    return yaml.safe_load(CONTRACT_FILE.read_text(encoding="utf-8"))


@pytest.fixture
def assert_matches_schema(spec):
    def check(payload, schema_name):
        schema = {
            "$ref": f"#/components/schemas/{schema_name}",
            "components": spec["components"],
        }
        Draft202012Validator(schema).validate(payload)

    return check


def documented_statuses(spec, path, method):
    return {int(code) for code in spec["paths"][path][method]["responses"]}


def test_paths_e_metodos_do_codigo_batem_com_o_contrato(spec, client):
    in_code = {path: set(methods) for path, methods in client.app.openapi()["paths"].items()}
    in_contract = {path: set(methods) for path, methods in spec["paths"].items()}
    assert in_code == in_contract


def test_enums_do_codigo_batem_com_o_contrato(spec):
    schemas = spec["components"]["schemas"]
    assert sorted(schemas["TipoResiduo"]["enum"]) == sorted(t.value for t in TipoResiduo)
    assert sorted(schemas["StatusPonto"]["enum"]) == sorted(s.value for s in StatusPonto)


def test_health_respeita_o_schema(client, spec, assert_matches_schema):
    response = client.get("/health")
    assert response.status_code in documented_statuses(spec, "/health", "get")
    assert_matches_schema(response.json(), "Health")


def test_get_point_respeita_o_schema_point(client, spec, assert_matches_schema):
    response = client.get("/points/1")
    assert response.status_code in documented_statuses(spec, "/points/{id}", "get")
    assert_matches_schema(response.json(), "Point")


def test_listagem_respeita_o_schema_point_list(client, spec, assert_matches_schema):
    response = client.get("/points", params={"limit": 3, "offset": 1})
    assert response.status_code in documented_statuses(spec, "/points", "get")
    assert_matches_schema(response.json(), "PointList")


def test_ask_respeita_o_schema_ask_response(client, spec, assert_matches_schema):
    response = client.post("/ask", json={"pergunta": "Onde descarto oleo de cozinha?"})
    assert response.status_code in documented_statuses(spec, "/ask", "post")
    assert_matches_schema(response.json(), "AskResponse")


def test_ask_recusado_respeita_o_schema_ask_response(client, spec, assert_matches_schema):
    response = client.post("/ask", json={"pergunta": "Qual a previsao do tempo?"})
    assert response.status_code in documented_statuses(spec, "/ask", "post")
    assert_matches_schema(response.json(), "AskResponse")


@pytest.mark.parametrize(
    "method, url, kwargs, path, expected",
    [
        ("get", "/points/9999", {}, "/points/{id}", 404),
        ("get", "/points/0", {}, "/points/{id}", 422),
        ("get", "/points?tipo=xyz", {}, "/points", 422),
        ("post", "/ask", {"json": {"pergunta": ""}}, "/ask", 422),
        ("post", "/ask", {"json": {"pergunta": "   "}}, "/ask", 400),
    ],
)
def test_erros_usam_o_corpo_padronizado_e_status_documentado(
    client, spec, assert_matches_schema, method, url, kwargs, path, expected
):
    response = getattr(client, method)(url, **kwargs)
    assert response.status_code == expected
    assert expected in documented_statuses(spec, path, method)
    assert_matches_schema(response.json(), "ErrorResponse")


def test_erro_503_usa_o_corpo_padronizado(make_client, spec, assert_matches_schema):
    client = make_client(FakeLLM(fail=True))
    response = client.post("/ask", json={"pergunta": "Onde descarto oleo de cozinha?"})
    assert response.status_code == 503
    assert 503 in documented_statuses(spec, "/ask", "post")
    assert_matches_schema(response.json(), "ErrorResponse")