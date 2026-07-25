from dataclasses import dataclass


@dataclass(frozen=True)
class Constitution:
    text: str
