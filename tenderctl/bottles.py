"""Bottle message handling."""

import json
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict


@dataclass
class Bottle:
    """A message bottle for fleet communication."""
    id: str
    origin: str
    target: str
    type: str
    payload: dict
    priority: str = "medium"
    compressed: bool = False
    timestamp: float = 0
    status: str = "pending"  # pending, delivered, acked

    @classmethod
    def from_dict(cls, data: dict) -> "Bottle":
        """Create Bottle from dictionary."""
        return cls(**data)

    @classmethod
    def from_json(cls, json_str: str) -> "Bottle":
        """Create Bottle from JSON string."""
        return cls.from_dict(json.loads(json_str))

    def to_dict(self) -> dict:
        """Convert Bottle to dictionary."""
        return asdict(self)

    def to_json(self) -> str:
        """Convert Bottle to JSON string."""
        return json.dumps(self.to_dict(), indent=2)


def read_bottle(content: str) -> Optional[Bottle]:
    """Read and parse a bottle from file content."""
    try:
        return Bottle.from_json(content)
    except (json.JSONDecodeError, TypeError):
        return None


def write_bottle(bottle: Bottle) -> str:
    """Write a bottle to JSON string."""
    return bottle.to_json()
