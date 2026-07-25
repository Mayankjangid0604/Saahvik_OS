import json
from pathlib import Path
from typing import Any, Mapping


class FileDocumentLoader:
    def __init__(self, base_path: Path) -> None:
        self._base_path = base_path

    def load_text(self, name: str) -> str:
        path = self._resolve(name)
        return path.read_text(encoding="utf-8")

    def load_mapping(self, name: str) -> Mapping[str, Any]:
        path = self._resolve(name)
        with path.open("r", encoding="utf-8") as file:
            loaded = json.load(file)

        if not isinstance(loaded, dict):
            raise ValueError(f"Expected mapping document: {name}")

        return loaded

    def save_mapping(self, name: str, values: Mapping[str, Any]) -> None:
        path = self._resolve(name)
        path.write_text(
            json.dumps(values, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    def _resolve(self, name: str) -> Path:
        path = (self._base_path / name).resolve()
        base_path = self._base_path.resolve()

        if base_path != path and base_path not in path.parents:
            raise ValueError(f"Document path escapes base path: {name}")

        return path
