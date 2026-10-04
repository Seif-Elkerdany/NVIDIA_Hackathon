"""Service error value; HTTP response mapping remains at the API boundary."""

from dataclasses import dataclass

from .dto import FieldError


@dataclass(eq=False)
class DomainError(Exception):
    code: str
    safe_message: str
    status: int
    retryable: bool = False
    field_errors: tuple[FieldError, ...] = ()

    def __str__(self) -> str:
        return self.safe_message
