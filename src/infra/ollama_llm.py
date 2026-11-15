import httpx

from src.domain.errors import LLMUnavailable
from src.domain.ports import LLMPort


class OllamaAdapter(LLMPort):
    def __init__(self, base_url: str, model: str, timeout: float = 30.0):
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._timeout = timeout

    def generate(self, prompt: str) -> str:
        try:
            response = httpx.post(
                f"{self._base_url}/api/generate",
                json={"model": self._model, "prompt": prompt, "stream": False},
                timeout=self._timeout,
            )
            response.raise_for_status()
            return response.json()["response"]
        except (httpx.HTTPError, KeyError, ValueError) as exc:
            raise LLMUnavailable(str(exc)) from exc