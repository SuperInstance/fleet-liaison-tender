"""Tests for priority translation."""

import pytest
from tenderctl.priority import PriorityTranslator


def test_cloud_to_edge_translation():
    """Test cloud to edge priority translation."""
    translator = PriorityTranslator()

    assert translator.cloud_to_edge("low") == "ignore"
    assert translator.cloud_to_edge("medium") == "queue"
    assert translator.cloud_to_edge("high") == "handle_soon"
    assert translator.cloud_to_edge("critical") == "immediate"


def test_edge_to_cloud_translation():
    """Test edge to cloud status translation."""
    translator = PriorityTranslator()

    assert translator.edge_to_cloud("nominal") == "info"
    assert translator.edge_to_cloud("degraded") == "warning"
    assert translator.edge_to_cloud("failing") == "high"
    assert translator.edge_to_cloud("down") == "critical"


def test_should_forward():
    """Test forwarding decision based on priority."""
    translator = PriorityTranslator()

    assert translator.should_forward("low") is False
    assert translator.should_forward("medium") is True
    assert translator.should_forward("high") is True
    assert translator.should_forward("critical") is True


def test_translate_message_cloud_to_edge():
    """Test message translation from cloud to edge."""
    translator = PriorityTranslator()
    bottle = {
        "priority": "high",
        "payload": {"data": "test"},
    }

    result = translator.translate_message(bottle, "cloud_to_edge")

    assert result["original_priority"] == "high"
    assert result["translated_priority"] == "handle_soon"
    assert result["should_forward"] is True


def test_translate_message_edge_to_cloud():
    """Test message translation from edge to cloud."""
    translator = PriorityTranslator()
    bottle = {
        "status": "degraded",
        "payload": {"data": "test"},
    }

    result = translator.translate_message(bottle, "edge_to_cloud")

    assert result["original_status"] == "degraded"
    assert result["translated_alert"] == "warning"
