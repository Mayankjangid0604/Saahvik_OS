from dataclasses import dataclass


@dataclass(frozen=True)
class BusinessFunction:
    identifier: str
    name: str
    description: str
    purpose: str
