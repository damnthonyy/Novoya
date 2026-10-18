from typing import Protocol


class UnitOfWork(Protocol):
    """One use case is one transaction. Moves to shared/application with the accounts PR (#63)."""

    async def commit(self) -> None: ...
