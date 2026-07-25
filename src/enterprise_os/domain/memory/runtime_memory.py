from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Mapping

from enterprise_os.domain.cognition.validation import require_mapping


@dataclass(frozen=True)
class RuntimeMemory:
    entries: tuple[Mapping[str, Any], ...]

    @classmethod
    def from_mapping(cls, values: Mapping[str, Any]) -> "RuntimeMemory":
        entries = values["entries"]
        if not isinstance(entries, list):
            raise TypeError("entries must be a list of mappings")

        validated_entries = tuple(
            MappingProxyType(dict(require_mapping(entry, f"entries[{index}]")))
            for index, entry in enumerate(entries)
        )
        return cls(entries=validated_entries)

    def to_mapping(self) -> dict[str, object]:
        return {"entries": [dict(entry) for entry in self.entries]}
