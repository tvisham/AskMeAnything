from typing import Protocol


class BaseAgent(Protocol):
    """Minimal agent interface."""

    name: str

    def handle(self, query: str) -> str:
        """Process a query and return a response string."""

        ...
