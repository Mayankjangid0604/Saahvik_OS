from typing import Any, Mapping, Protocol


class DocumentLoader(Protocol):
    def load_text(self, name: str) -> str:
        ...

    def load_mapping(self, name: str) -> Mapping[str, Any]:
        ...

    def save_mapping(self, name: str, values: Mapping[str, Any]) -> None:
        ...
