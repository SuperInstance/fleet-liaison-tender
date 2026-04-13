#!/usr/bin/env python3
"""Fleet Liaison Tender — Social vessel for cloud-edge communication."""

import json
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional
from dataclasses import dataclass, field


@dataclass
class TenderMessage:
    origin: str        # cloud or edge
    target: str        # vessel name
    type: str          # research, data, context, priority
    payload: dict
    compressed: bool = False
    timestamp: float = field(default_factory=time.time)


class LiaisonTender:
    """Base class for fleet liaison tenders."""
    
    def __init__(self, name: str, tender_type: str):
        self.name = name
        self.tender_type = tender_type
        self.queue_in: List[TenderMessage] = []
        self.queue_out: List[TenderMessage] = []
        self.filters: Dict[str, list] = {}  # target -> list of keywords
    
    def receive(self, msg: TenderMessage):
        """Receive a message and queue for processing."""
        self.queue_in.append(msg)
    
    def process(self) -> List[TenderMessage]:
        """Process queue and produce outgoing messages."""
        raise NotImplementedError
    
    def send(self, msg: TenderMessage):
        """Queue message for delivery."""
        self.queue_out.append(msg)
    
    def status(self) -> dict:
        return {
            "name": self.name,
            "type": self.tender_type,
            "inbox": len(self.queue_in),
            "outbox": len(self.queue_out),
        }


class ResearchTender(LiaisonTender):
    """Carries findings between cloud and edge labs."""
    
    def __init__(self):
        super().__init__("research-tender", "research")
    
    def process(self) -> List[TenderMessage]:
        results = []
        while self.queue_in:
            msg = self.queue_in.pop(0)
            if msg.origin == "cloud":
                # Cloud spec → compressed edge action items
                results.append(TenderMessage(
                    origin="cloud", target="jetsonclaw1",
                    type="research",
                    payload=self._compress_spec(msg.payload),
                    compressed=True,
                ))
            elif msg.origin == "edge":
                # Edge findings → formatted for cloud consumption
                results.append(TenderMessage(
                    origin="edge", target="oracle1",
                    type="research",
                    payload=self._format_findings(msg.payload),
                ))
        self.queue_out.extend(results)
        return results
    
    def _compress_spec(self, spec: dict) -> dict:
        """Compress cloud spec for edge consumption."""
        return {
            "action": spec.get("title", "untitled"),
            "changes": spec.get("changes_affecting_edge", []),
            "ignore": spec.get("changes_not_affecting_edge", []),
            "isa_changes": spec.get("isa_modifications", []),
            "deadline": spec.get("deadline"),
        }
    
    def _format_findings(self, findings: dict) -> dict:
        """Format edge findings for cloud."""
        return {
            "source": "jetsonclaw1",
            "benchmarks": findings.get("benchmarks", {}),
            "failure_modes": findings.get("failures", []),
            "timing_data": findings.get("timing", {}),
            "recommendations": findings.get("recommendations", []),
            "reality_check": findings.get("cloud_assumption_vs_reality", {}),
        }


class DataTender(LiaisonTender):
    """Batches and packages big data for edge consumption."""
    
    def __init__(self, batch_size: int = 50):
        super().__init__("data-tender", "data")
        self.batch_size = batch_size
        self.buffer: List[dict] = []
    
    def process(self) -> List[TenderMessage]:
        results = []
        while self.queue_in:
            msg = self.queue_in.pop(0)
            if msg.origin == "cloud" and msg.target == "edge":
                self.buffer.append(msg.payload)
                if len(self.buffer) >= self.batch_size:
                    batch = self._package_batch(self.buffer)
                    results.append(TenderMessage(
                        origin="cloud", target="jetsonclaw1",
                        type="data", payload=batch, compressed=True,
                    ))
                    self.buffer = []
        self.queue_out.extend(results)
        return results
    
    def _package_batch(self, items: List[dict]) -> dict:
        return {
            "batch_size": len(items),
            "items": items,
            "edge_relevant_only": True,
            "total_cloud_events": sum(i.get("total_events", 1) for i in items),
        }


class PriorityTender(LiaisonTender):
    """Translates urgency between cloud and edge realities."""
    
    def __init__(self):
        super().__init__("priority-tender", "priority")
        self.priority_map_cloud_to_edge = {
            "low": "ignore",
            "medium": "queue",
            "high": "handle_soon",
            "critical": "immediate",
        }
        self.priority_map_edge_to_cloud = {
            "nominal": "info",
            "degraded": "warning",
            "failing": "high",
            "down": "critical",
        }
    
    def process(self) -> List[TenderMessage]:
        results = []
        while self.queue_in:
            msg = self.queue_in.pop(0)
            if msg.origin == "cloud":
                cloud_priority = msg.payload.get("priority", "low")
                edge_priority = self.priority_map_cloud_to_edge.get(cloud_priority, "queue")
                if edge_priority != "ignore":
                    results.append(TenderMessage(
                        origin="cloud", target="jetsonclaw1",
                        type="priority",
                        payload={
                            "original": cloud_priority,
                            "translated": edge_priority,
                            "task": msg.payload.get("task"),
                            "reason": msg.payload.get("reason"),
                        },
                    ))
            elif msg.origin == "edge":
                edge_status = msg.payload.get("status", "nominal")
                cloud_alert = self.priority_map_edge_to_cloud.get(edge_status, "info")
                results.append(TenderMessage(
                    origin="edge", target="oracle1",
                    type="priority",
                    payload={
                        "original": edge_status,
                        "translated": cloud_alert,
                        "sensor_data": msg.payload.get("sensors"),
                    },
                ))
        self.queue_out.extend(results)
        return results


class ContextTender(LiaisonTender):
    """Carries fleet-wide context to isolated edge nodes with window management.

    Maintains a sliding window of recent messages per session, estimates token
    counts, and applies priority-based eviction when the context budget is
    exceeded.  Older, lower-priority entries are evicted first so that the
    most important context is always available to the edge node.
    """

    PRIORITY_ORDER = {"low": 0, "medium": 1, "high": 2, "critical": 3}

    def __init__(self, max_tokens: int = 4096, window_size: int = 10):
        super().__init__("context-tender", "context")
        self.max_tokens = max_tokens
        self.window_size = window_size
        # session_id -> list of window entries
        self.context_windows: Dict[str, List[dict]] = {}

    # ------------------------------------------------------------------
    # Token estimation
    # ------------------------------------------------------------------

    def _estimate_tokens(self, payload: dict) -> int:
        """Rough token estimate (~4 chars per token for mixed English text)."""
        text = json.dumps(payload, separators=(',', ':'))
        return max(1, len(text) // 4)

    # ------------------------------------------------------------------
    # Window management
    # ------------------------------------------------------------------

    def _get_priority(self, payload: dict) -> str:
        return payload.get("priority", "low")

    def _enforce_window_size(self, session_id: str) -> int:
        """Trim the window to *window_size*, evicting oldest entries first.

        Returns the number of entries evicted.
        """
        window = self.context_windows.get(session_id, [])
        evicted = 0
        while len(window) > self.window_size:
            window.pop(0)
            evicted += 1
        self.context_windows[session_id] = window
        return evicted

    def _priority_eviction(self, session_id: str) -> int:
        """Evict lowest-priority / oldest entries until within *max_tokens*.

        The most recent entry is never evicted.  Returns count evicted.
        """
        window = self.context_windows.get(session_id, [])
        total = sum(e["tokens"] for e in window)
        evicted = 0

        while total > self.max_tokens and len(window) > 1:
            # Find the lowest-priority, oldest entry (never index -1)
            evict_idx = 0
            evict_score = (
                self.PRIORITY_ORDER.get(window[0]["priority"], 0),
                window[0]["timestamp"],
            )
            for i in range(len(window) - 1):
                score = (
                    self.PRIORITY_ORDER.get(window[i]["priority"], 0),
                    window[i]["timestamp"],
                )
                if score < evict_score:
                    evict_score = score
                    evict_idx = i
            removed = window.pop(evict_idx)
            total -= removed["tokens"]
            evicted += 1

        self.context_windows[session_id] = window
        return evicted

    # ------------------------------------------------------------------
    # Payload helpers
    # ------------------------------------------------------------------

    def _summarize_payload(self, payload: dict) -> dict:
        """Create a condensed summary of a single payload."""
        return {
            "_summary": True,
            "topic": payload.get("topic", payload.get("subject", "general")),
            "key_info": payload.get("key_info", payload.get("summary", "")),
            "original_tokens": self._estimate_tokens(payload),
        }

    # ------------------------------------------------------------------
    # Direction-specific processing
    # ------------------------------------------------------------------

    def _process_cloud_to_edge(self, msg: TenderMessage) -> TenderMessage:
        session_id = msg.payload.get("session_id", "default")
        tokens = self._estimate_tokens(msg.payload)

        entry = {
            "payload": msg.payload,
            "timestamp": msg.timestamp,
            "priority": self._get_priority(msg.payload),
            "tokens": tokens,
        }

        if session_id not in self.context_windows:
            self.context_windows[session_id] = []
        self.context_windows[session_id].append(entry)

        # 1. Enforce sliding-window size
        window_evicted = self._enforce_window_size(session_id)

        # 2. If still over token budget, priority-evict
        window = self.context_windows[session_id]
        total_tokens = sum(e["tokens"] for e in window)
        budget_evicted = 0
        if total_tokens > self.max_tokens:
            budget_evicted = self._priority_eviction(session_id)

        # Recalculate after evictions
        window = self.context_windows[session_id]
        total_tokens = sum(e["tokens"] for e in window)
        total_evicted = window_evicted + budget_evicted

        # Single message exceeds budget on its own → hard summarize
        if tokens > self.max_tokens:
            compressed_content = self._summarize_payload(msg.payload)
            return TenderMessage(
                origin="cloud",
                target="jetsonclaw1",
                type="context",
                payload={
                    "content": compressed_content,
                    "window_size": len(window),
                    "total_tokens": self._estimate_tokens(compressed_content),
                    "compression_applied": "hard_summarize",
                },
                compressed=True,
            )

        if total_evicted > 0 or total_tokens > self.max_tokens:
            return TenderMessage(
                origin="cloud",
                target="jetsonclaw1",
                type="context",
                payload={
                    "content": msg.payload,
                    "evicted_count": total_evicted,
                    "window_size": len(window),
                    "total_tokens": total_tokens,
                    "compression_applied": "priority_eviction",
                },
                compressed=True,
            )

        # Within budget — passthrough
        return TenderMessage(
            origin="cloud",
            target="jetsonclaw1",
            type="context",
            payload={
                "content": msg.payload,
                "window_size": len(window),
                "total_tokens": total_tokens,
                "compressed": False,
            },
        )

    def _process_edge_to_cloud(self, msg: TenderMessage) -> TenderMessage:
        return TenderMessage(
            origin="edge",
            target="oracle1",
            type="context",
            payload={
                "content": msg.payload,
                "source": "jetsonclaw1",
                "forwarded_at": time.time(),
            },
        )

    # ------------------------------------------------------------------
    # Core process loop (matches LiaisonTender interface)
    # ------------------------------------------------------------------

    def process(self) -> List[TenderMessage]:
        results = []
        while self.queue_in:
            msg = self.queue_in.pop(0)
            if msg.origin == "cloud":
                results.append(self._process_cloud_to_edge(msg))
            elif msg.origin == "edge":
                results.append(self._process_edge_to_cloud(msg))
        self.queue_out.extend(results)
        return results


class TenderFleet:
    """Manages all liaison tenders."""
    
    def __init__(self):
        self.tenders = {
            "research": ResearchTender(),
            "data": DataTender(),
            "context": ContextTender(),
            "priority": PriorityTender(),
        }
    
    def run_cycle(self):
        """Process all tender queues."""
        results = {}
        for name, tender in self.tenders.items():
            processed = tender.process()
            results[name] = len(processed)
        return results
    
    def status(self):
        return {name: tender.status() for name, tender in self.tenders.items()}


if __name__ == "__main__":
    print("╔══════════════════════════════════════════════╗")
    print("║  Fleet Liaison Tender — Communication Layer   ║")
    print("╚══════════════════════════════════════════════╝\n")
    
    fleet = TenderFleet()
    
    # Simulate cloud → edge research
    fleet.tenders["research"].receive(TenderMessage(
        origin="cloud", target="edge", type="research",
        payload={
            "title": "ISA v3 Edge Encoding",
            "changes_affecting_edge": ["compact mode opcodes renumbered"],
            "changes_not_affecting_edge": ["cloud-only debug extensions"],
            "isa_modifications": ["OP_COMPACT prefix byte changed from 0xFE to 0xFD"],
            "deadline": "2026-04-15",
        },
    ))
    
    # Simulate edge → cloud findings
    fleet.tenders["research"].receive(TenderMessage(
        origin="edge", target="cloud", type="research",
        payload={
            "benchmarks": {"16K rooms": "25.5us/tick"},
            "failures": ["COBS framing drops bytes at 115200 baud on long cables"],
            "timing": {"model_hot_swap": "42s measured"},
            "recommendations": ["Use shorter serial cables for ESP32 bridge"],
            "cloud_assumption_vs_reality": {
                "assumption": "model swap takes 45s",
                "reality": "42s on Orin, but 68s with fragmented VRAM",
            },
        },
    ))
    
    # Simulate priority translation
    fleet.tenders["priority"].receive(TenderMessage(
        origin="cloud", target="edge", type="priority",
        payload={"priority": "medium", "task": "Update ISA opcodes", "reason": "Fleet-wide convergence"},
    ))
    
    fleet.tenders["priority"].receive(TenderMessage(
        origin="edge", target="cloud", type="priority",
        payload={"status": "degraded", "sensors": {"cpu_temp": "72C", "gpu_util": "95%"}},
    ))
    
    # Run processing cycle
    print("Processing tender queues...")
    results = fleet.run_cycle()
    for name, count in results.items():
        print(f"  {name}: {count} messages processed")
    
    # Show outbound messages
    print("\nOutbound messages:")
    for name, tender in fleet.tenders.items():
        for msg in tender.queue_out:
            print(f"  [{name}] {msg.origin} → {msg.target}: {msg.type}")
            if "reality_check" in str(msg.payload):
                rc = msg.payload.get("reality_check", {})
                print(f"    Reality check: {rc.get('assumption')} → {rc.get('reality')}")
            if "translated" in msg.payload:
                print(f"    Priority: {msg.payload.get('original')} → {msg.payload.get('translated')}")
    
    print("\nTender fleet status:")
    for name, status in fleet.status().items():
        print(f"  {name}: inbox={status['inbox']}, outbox={status['outbox']}")
    
    print("\n═══════════════════════════════════════════")
    print("Social vessels. Information management. Fleet-scale.")
    print("═══════════════════════════════════════════")
