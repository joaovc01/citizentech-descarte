from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.api.main import create_app
from src.infra.fake_llm import FakeLLM
from src.infra.json_repository import JsonPointRepository

ROOT = Path(__file__).resolve().parent.parent
POINTS_FILE = ROOT / "src" / "infra" / "data" / "points.json"


@pytest.fixture
def repository():
    return JsonPointRepository(POINTS_FILE)


@pytest.fixture
def make_client(repository):
    def build(llm=None):
        if llm is None:
            llm = FakeLLM()
        return TestClient(create_app(repository=repository, llm=llm))

    return build


@pytest.fixture
def client(make_client):
    return make_client()