"""Priority translation between cloud and edge."""

from typing import Dict


class PriorityTranslator:
    """Translates priority levels between cloud and edge realities."""

    CLOUD_TO_EDGE = {
        "low": "ignore",
        "medium": "queue",
        "high": "handle_soon",
        "critical": "immediate",
    }

    EDGE_TO_CLOUD = {
        "nominal": "info",
        "degraded": "warning",
        "failing": "high",
        "down": "critical",
    }

    def cloud_to_edge(self, cloud_priority: str) -> str:
        """Translate cloud priority to edge priority."""
        return self.CLOUD_TO_EDGE.get(cloud_priority.lower(), "queue")

    def edge_to_cloud(self, edge_status: str) -> str:
        """Translate edge status to cloud alert level."""
        return self.EDGE_TO_CLOUD.get(edge_status.lower(), "info")

    def should_forward(self, cloud_priority: str) -> bool:
        """Determine if message should be forwarded to edge."""
        edge_priority = self.cloud_to_edge(cloud_priority)
        return edge_priority != "ignore"

    def translate_message(self, bottle: Dict, direction: str = "cloud_to_edge") -> Dict:
        """Translate priority in a message bottle."""
        if direction == "cloud_to_edge":
            original = bottle.get("priority", "medium")
            translated = self.cloud_to_edge(original)
            return {
                **bottle,
                "original_priority": original,
                "translated_priority": translated,
                "should_forward": self.should_forward(original),
            }
        else:
            original = bottle.get("status", "nominal")
            translated = self.edge_to_cloud(original)
            return {
                **bottle,
                "original_status": original,
                "translated_alert": translated,
            }
