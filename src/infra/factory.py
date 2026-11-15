import os
from pathlib import Path

from src.domain.ports import LLMPort, PointRepository
from src.infra.fake_llm import FakeLLM
from src.infra.json_repository import JsonPointRepository
from src.infra.ollama_llm import OllamaAdapter


def build_llm() -> LLMPort:
    provider = os.getenv("LLM_PROVIDER", "fake")
    if provider == "ollama":
        return OllamaAdapter(
            base_url=os.getenv("OLLAMA_URL", "http://localhost:11434"),
            model=os.getenv("OLLAMA_MODEL", "llama3.2"),
            timeout=float(os.getenv("OLLAMA_TIMEOUT", "30")),
        )
    if provider == "fake":
        return FakeLLM()
    raise ValueError(f"LLM_PROVIDER invalido: {provider}")


def build_repository() -> PointRepository:
    default = Path(__file__).parent / "data" / "points.json"
    return JsonPointRepository(os.getenv("POINTS_FILE", str(default)))