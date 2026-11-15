class DomainError(Exception):
    pass


class PointNotFound(DomainError):
    def __init__(self, point_id: int):
        super().__init__(f"Ponto {point_id} nao encontrado")
        self.point_id = point_id


class InvalidQuestion(DomainError):
    pass


class LLMUnavailable(DomainError):
    pass