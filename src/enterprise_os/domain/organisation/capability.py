from dataclasses import dataclass


@dataclass(frozen=True)
class Capability:
    identifier: str
    name: str
    description: str
    purpose: str
    strategic_importance: str
    required_skills: tuple[str, ...]
    dependencies: tuple[str, ...]
    maturity: str
    confidence: str


@dataclass(frozen=True)
class CapabilityAnalysis:
    missing_capabilities: tuple[Capability, ...]
    existing_capabilities: tuple[Capability, ...]
    overlapping_capabilities: tuple[Capability, ...]
    critical_capabilities: tuple[Capability, ...]
    optional_capabilities: tuple[Capability, ...]
    reasoning: str
