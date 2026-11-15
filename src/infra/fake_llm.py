import re

from src.domain.errors import LLMUnavailable
from src.domain.ports import LLMPort


class FakeLLM(LLMPort):
    def __init__(self, response: str | None = None, fail: bool = False):
        self._response = response
        self._fail = fail
        self.prompts: list[str] = []

    def generate(self, prompt: str) -> str:
        self.prompts.append(prompt)
        if self._fail:
            raise LLMUnavailable("fake indisponivel")
        if self._response is not None:
            return self._response
        match = re.search(r"\[ID (\d+)\]", prompt)
        if match is None:
            return "Nao encontrei um ponto de coleta para essa pergunta."
        return f"Voce pode descartar no ponto [ID {match.group(1)}]."