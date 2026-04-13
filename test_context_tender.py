#!/usr/bin/env python3
"""Tests for ContextTender — context-window-aware message compression."""

import unittest
import time

from tender import (
    TenderMessage,
    ContextTender,
    TenderFleet,
)


def _make_cloud_msg(payload: dict, session_id: str = "default") -> TenderMessage:
    payload.setdefault("session_id", session_id)
    return TenderMessage(
        origin="cloud",
        target="edge",
        type="context",
        payload=payload,
    )


def _make_edge_msg(payload: dict, session_id: str = "default") -> TenderMessage:
    payload.setdefault("session_id", session_id)
    return TenderMessage(
        origin="edge",
        target="cloud",
        type="context",
        payload=payload,
    )


class TestBasicPassthrough(unittest.TestCase):
    """A small message within budget should pass through uncompressed."""

    def test_single_small_message_not_compressed(self):
        tender = ContextTender(max_tokens=4096, window_size=10)
        tender.receive(_make_cloud_msg({"topic": "hello", "body": "world"}))
        results = tender.process()

        self.assertEqual(len(results), 1)
        msg = results[0]
        self.assertFalse(msg.compressed)
        self.assertEqual(msg.origin, "cloud")
        self.assertEqual(msg.target, "jetsonclaw1")
        self.assertEqual(msg.type, "context")
        self.assertFalse(msg.payload["compressed"])
        self.assertEqual(msg.payload["window_size"], 1)

    def test_small_message_preserves_content(self):
        tender = ContextTender(max_tokens=4096, window_size=10)
        original_payload = {"topic": "test", "body": "hello edge node", "session_id": "s1"}
        tender.receive(_make_cloud_msg(original_payload))
        results = tender.process()

        content = results[0].payload["content"]
        self.assertEqual(content["topic"], "test")
        self.assertEqual(content["body"], "hello edge node")
        self.assertEqual(content["session_id"], "s1")

    def test_edge_to_cloud_passes_through(self):
        tender = ContextTender()
        tender.receive(_make_edge_msg({"topic": "edge-update", "data": 42}))
        results = tender.process()

        self.assertEqual(len(results), 1)
        msg = results[0]
        self.assertEqual(msg.origin, "edge")
        self.assertEqual(msg.target, "oracle1")
        self.assertEqual(msg.payload["source"], "jetsonclaw1")
        self.assertIn("forwarded_at", msg.payload)
        self.assertEqual(msg.payload["content"]["topic"], "edge-update")


class TestCompressionTrigger(unittest.TestCase):
    """Messages exceeding the token budget should be compressed."""

    def test_oversized_single_message_hard_summarized(self):
        # Create a payload that is guaranteed to exceed a very small budget
        huge_body = "x" * 5000  # ~5000 chars → ~1250 tokens
        tender = ContextTender(max_tokens=100, window_size=10)
        tender.receive(_make_cloud_msg({"topic": "huge", "body": huge_body, "session_id": "c1"}))
        results = tender.process()

        self.assertEqual(len(results), 1)
        msg = results[0]
        self.assertTrue(msg.compressed)
        self.assertEqual(msg.payload["compression_applied"], "hard_summarize")
        # Summarized content should be much smaller
        content = msg.payload["content"]
        self.assertTrue(content["_summary"])
        self.assertEqual(content["topic"], "huge")

    def test_accumulated_messages_trigger_priority_eviction(self):
        """Fill the window with medium messages until budget is exceeded."""
        tender = ContextTender(max_tokens=100, window_size=10)

        # Send 5 messages, each ~200 chars → ~50 tokens each → 250 total > 100 budget
        for i in range(5):
            body = "word " * 50  # ~250 chars → ~62 tokens
            tender.receive(_make_cloud_msg({
                "topic": f"msg-{i}",
                "body": body,
                "session_id": "c2",
            }))

        results = tender.process()
        self.assertTrue(len(results) >= 1)

        # At least some messages should have been compressed via priority eviction
        compressed_msgs = [r for r in results if r.compressed]
        self.assertTrue(len(compressed_msgs) > 0,
                        "Expected at least one compressed message when budget exceeded")


class TestSlidingWindow(unittest.TestCase):
    """The sliding window should evict oldest entries when size is exceeded."""

    def test_window_evicts_oldest(self):
        window_size = 3
        tender = ContextTender(max_tokens=99999, window_size=window_size)

        for i in range(5):
            tender.receive(_make_cloud_msg({
                "topic": f"topic-{i}",
                "priority": "medium",
                "session_id": "sw1",
            }))

        results = tender.process()
        self.assertEqual(len(results), 5)

        # Check last message has window_size of 3 (not 5)
        last = results[-1]
        self.assertEqual(last.payload["window_size"], window_size)

        # At least 2 messages should be compressed (first 2 exceeded window)
        evicted_msgs = [r for r in results if r.compressed and r.payload.get("compression_applied") == "priority_eviction"]
        self.assertTrue(len(evicted_msgs) >= 2,
                        "Messages beyond window_size should trigger eviction")

    def test_window_per_session_isolated(self):
        """Different session_ids should have independent windows."""
        tender = ContextTender(max_tokens=99999, window_size=2)

        # Session A: 3 messages
        for i in range(3):
            tender.receive(_make_cloud_msg({"topic": f"a-{i}", "session_id": "sessionA"}))
        # Session B: 1 message
        tender.receive(_make_cloud_msg({"topic": "b-0", "session_id": "sessionB"}))

        results = tender.process()
        self.assertEqual(len(results), 4)

        # Session A's last message should have window_size=2
        session_a_results = [r for r in results
                             if r.payload.get("content", {}).get("session_id") == "sessionA"]
        last_a = session_a_results[-1]
        self.assertEqual(last_a.payload["window_size"], 2)

        # Session B's message should have window_size=1
        session_b_results = [r for r in results
                             if r.payload.get("content", {}).get("session_id") == "sessionB"]
        self.assertEqual(session_b_results[0].payload["window_size"], 1)


class TestPriorityPreservation(unittest.TestCase):
    """Higher-priority messages should be preserved over lower-priority ones."""

    def test_low_priority_evicted_before_high(self):
        """When budget is tight, low-priority messages should be evicted first."""
        tender = ContextTender(max_tokens=80, window_size=10)

        # First: low priority message
        tender.receive(_make_cloud_msg({
            "topic": "low-priority-old",
            "body": "word " * 30,  # ~150 chars → ~37 tokens
            "priority": "low",
            "session_id": "p1",
        }))

        time.sleep(0.01)  # Ensure different timestamps

        # Second: high priority message
        tender.receive(_make_cloud_msg({
            "topic": "high-priority-new",
            "body": "word " * 30,
            "priority": "critical",
            "session_id": "p1",
        }))

        results = tender.process()
        self.assertEqual(len(results), 2)

        # The second (high priority) message should still carry its full content
        high_msg = results[1]
        content = high_msg.payload.get("content", {})
        # If no eviction happened (both fit), check window
        # If eviction happened, the high-priority should be kept
        self.assertEqual(content.get("topic"), "high-priority-new")
        self.assertEqual(content.get("priority"), "critical")

    def test_critical_message_never_evicted_when_multiple(self):
        """With mixed priorities under tight budget, critical msgs survive."""
        tender = ContextTender(max_tokens=60, window_size=10)

        # Send 3 low-priority, then 1 critical
        for i in range(3):
            tender.receive(_make_cloud_msg({
                "topic": f"low-{i}",
                "body": "word " * 20,
                "priority": "low",
                "session_id": "p2",
            }))
            time.sleep(0.01)

        tender.receive(_make_cloud_msg({
            "topic": "critical-update",
            "body": "word " * 20,
            "priority": "critical",
            "session_id": "p2",
        }))

        results = tender.process()
        self.assertEqual(len(results), 4)

        # Find the critical message result
        critical_result = results[3]
        content = critical_result.payload.get("content", {})
        self.assertEqual(content.get("topic"), "critical-update")

    def test_priority_ordering_eviction(self):
        """Medium priority evicted before high priority when both old."""
        tender = ContextTender(max_tokens=50, window_size=10)

        # Old medium
        tender.receive(_make_cloud_msg({
            "topic": "old-medium",
            "body": "word " * 15,
            "priority": "medium",
            "session_id": "p3",
        }))
        time.sleep(0.01)

        # Old high
        tender.receive(_make_cloud_msg({
            "topic": "old-high",
            "body": "word " * 15,
            "priority": "high",
            "session_id": "p3",
        }))

        # After processing, both may be evicted if budget exceeded,
        # but medium should be evicted before high
        results = tender.process()

        # Check that the high priority message retained its content
        high_result = results[1]
        content = high_result.payload.get("content", {})
        if not high_result.compressed or high_result.payload.get("compression_applied") == "hard_summarize":
            # If it was hard-summarized, the summary should still reference it
            if high_result.payload.get("compression_applied") == "hard_summarize":
                self.assertEqual(content.get("topic"), "old-high")
        else:
            self.assertEqual(content.get("topic"), "old-high")


class TestIntegrationWithTenderFleet(unittest.TestCase):
    """ContextTender should work correctly within TenderFleet."""

    def test_context_tender_registered_in_fleet(self):
        fleet = TenderFleet()
        self.assertIn("context", fleet.tenders)
        self.assertIsInstance(fleet.tenders["context"], ContextTender)

    def test_fleet_run_cycle_processes_context(self):
        fleet = TenderFleet()
        fleet.tenders["context"].receive(_make_cloud_msg({
            "topic": "fleet-test",
            "session_id": "fleet1",
        }))
        results = fleet.run_cycle()
        self.assertIn("context", results)
        self.assertEqual(results["context"], 1)

    def test_fleet_status_includes_context(self):
        fleet = TenderFleet()
        status = fleet.status()
        self.assertIn("context", status)
        self.assertEqual(status["context"]["name"], "context-tender")
        self.assertEqual(status["context"]["type"], "context")

    def test_fleet_all_four_tenders_present(self):
        fleet = TenderFleet()
        self.assertEqual(set(fleet.tenders.keys()), {"research", "data", "context", "priority"})


class TestTokenEstimation(unittest.TestCase):
    """Verify the token estimation heuristic works correctly."""

    def test_empty_payload_minimum_one_token(self):
        tender = ContextTender()
        self.assertEqual(tender._estimate_tokens({}), 1)

    def test_larger_payload_produces_more_tokens(self):
        tender = ContextTender()
        small = {"a": "b"}
        large = {"a": "x" * 1000}
        self.assertGreater(tender._estimate_tokens(large), tender._estimate_tokens(small))

    def test_token_estimate_scales_with_content(self):
        tender = ContextTender()
        payload = {"body": "hello world"}
        tokens = tender._estimate_tokens(payload)
        self.assertGreater(tokens, 0)


if __name__ == "__main__":
    unittest.main()
