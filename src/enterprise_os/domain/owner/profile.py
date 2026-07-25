from dataclasses import dataclass
from typing import Any, Mapping

from enterprise_os.domain.cognition.validation import require_text


@dataclass(frozen=True)
class OwnerProfile:
    owner_id: str
    display_name: str

    @classmethod
    def from_mapping(cls, values: Mapping[str, Any]) -> "OwnerProfile":
        owner_id = str(values["owner_id"])
        display_name = str(values["display_name"])
        require_text(owner_id, "owner_id")
        require_text(display_name, "display_name")

        return cls(
            owner_id=owner_id,
            display_name=display_name,
        )

    def to_mapping(self) -> dict[str, Any]:
        return {
            "owner_id": self.owner_id,
            "display_name": self.display_name,
        }
