"""Message compression for edge consumption."""

from typing import Dict, List


class MessageCompressor:
    """Compresses cloud-originated messages for edge consumption."""

    def compress(self, bottle: Dict) -> Dict:
        """Compress a bottle message for edge delivery."""
        msg_type = bottle.get("type", "context")

        if msg_type == "research":
            return self._compress_research(bottle)
        elif msg_type == "data":
            return self._compress_data(bottle)
        elif msg_type == "context":
            return self._compress_context(bottle)
        elif msg_type == "priority":
            return self._compress_priority(bottle)
        else:
            return self._compress_generic(bottle)

    def _compress_research(self, bottle: Dict) -> Dict:
        """Compress research spec to action items."""
        payload = bottle.get("payload", {})
        return {
            "action": payload.get("title", "untitled"),
            "changes": payload.get("changes_affecting_edge", []),
            "isa_changes": payload.get("isa_modifications", []),
            "deadline": payload.get("deadline"),
            "compressed": True,
        }

    def _compress_data(self, bottle: Dict) -> Dict:
        """Compress data batch to edge-relevant items."""
        payload = bottle.get("payload", {})
        return {
            "batch_size": payload.get("batch_size", 1),
            "items": payload.get("items", [])[:10],  # Limit to 10 items for edge
            "edge_relevant_only": True,
            "compressed": True,
        }

    def _compress_context(self, bottle: Dict) -> Dict:
        """Compress context to essential information."""
        payload = bottle.get("payload", {})
        return {
            "update_type": payload.get("type", "general"),
            "affects_edge": payload.get("affects_edge", False),
            "action_required": payload.get("action_required", False),
            "summary": payload.get("summary", "")[:200],  # Limit summary length
            "compressed": True,
        }

    def _compress_priority(self, bottle: Dict) -> Dict:
        """Compress priority message."""
        payload = bottle.get("payload", {})
        original_priority = payload.get("priority", "medium")
        edge_priority = self._translate_priority(original_priority)

        return {
            "original": original_priority,
            "translated": edge_priority,
            "task": payload.get("task", ""),
            "reason": payload.get("reason", "")[:100],
            "compressed": True,
        }

    def _compress_generic(self, bottle: Dict) -> Dict:
        """Generic compression for unknown message types."""
        payload = bottle.get("payload", {})
        return {
            "type": bottle.get("type", "unknown"),
            "summary": str(payload)[:200],
            "compressed": True,
        }

    def _translate_priority(self, cloud_priority: str) -> str:
        """Translate cloud priority to edge priority."""
        priority_map = {
            "low": "ignore",
            "medium": "queue",
            "high": "handle_soon",
            "critical": "immediate",
        }
        return priority_map.get(cloud_priority.lower(), "queue")
