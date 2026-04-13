"""Local state tracking for tender messages."""

import json
import os
from typing import Dict, List
from pathlib import Path


class StateManager:
    """Manages message state in local JSON file."""

    def __init__(self, state_file: str = None):
        if state_file is None:
            state_file = os.path.expanduser("~/.tenderctl/state.json")
        self.state_file = Path(state_file)
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        self.state: Dict = self._load_state()

    def _load_state(self) -> Dict:
        """Load state from file."""
        if self.state_file.exists():
            with open(self.state_file, "r") as f:
                return json.load(f)
        return {"bottles": {}, "vessels": {}}

    def _save_state(self):
        """Save state to file."""
        with open(self.state_file, "w") as f:
            json.dump(self.state, f, indent=2)

    def add_bottle(self, bottle_id: str, vessel: str, bottle_data: dict):
        """Add a bottle to state tracking."""
        self.state["bottles"][bottle_id] = {
            "id": bottle_id,
            "vessel": vessel,
            "status": "pending",
            "timestamp": bottle_data.get("timestamp"),
            "delivered_at": None,
            "acked_at": None,
        }
        self._save_state()

    def update_bottle_status(self, bottle_id: str, status: str):
        """Update bottle status."""
        if bottle_id in self.state["bottles"]:
            import time
            self.state["bottles"][bottle_id]["status"] = status
            if status == "delivered":
                self.state["bottles"][bottle_id]["delivered_at"] = time.time()
            elif status == "acked":
                self.state["bottles"][bottle_id]["acked_at"] = time.time()
            self._save_state()

    def get_bottle(self, bottle_id: str) -> dict:
        """Get bottle state."""
        return self.state["bottles"].get(bottle_id)

    def get_vessel_status(self, vessel: str) -> dict:
        """Get status counts for a vessel."""
        vessel_bottles = [
            b for b in self.state["bottles"].values()
            if b["vessel"] == vessel
        ]
        return {
            "vessel": vessel,
            "pending": sum(1 for b in vessel_bottles if b["status"] == "pending"),
            "delivered": sum(1 for b in vessel_bottles if b["status"] == "delivered"),
            "acked": sum(1 for b in vessel_bottles if b["status"] == "acked"),
            "total": len(vessel_bottles),
        }

    def get_all_status(self) -> dict:
        """Get status for all vessels."""
        vessels = set(b["vessel"] for b in self.state["bottles"].values())
        return {
            "vessels": {
                v: self.get_vessel_status(v) for v in sorted(vessels)
            },
            "total_bottles": len(self.state["bottles"]),
        }
