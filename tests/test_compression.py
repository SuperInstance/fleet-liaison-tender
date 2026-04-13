"""Tests for message compression."""

import pytest
from tenderctl.compression import MessageCompressor


def test_compress_research():
    """Test research message compression."""
    compressor = MessageCompressor()
    bottle = {
        "type": "research",
        "payload": {
            "title": "ISA v3 Update",
            "changes_affecting_edge": ["opcode renumbering"],
            "changes_not_affecting_edge": ["debug extensions"],
            "isa_modifications": ["OP_COMPACT changed"],
            "deadline": "2026-04-15",
        },
    }

    result = compressor.compress(bottle)

    assert result["action"] == "ISA v3 Update"
    assert result["changes"] == ["opcode renumbering"]
    assert "deadline" in result
    assert result["compressed"] is True
    assert "changes_not_affecting_edge" not in result  # Stripped out


def test_compress_data():
    """Test data message compression."""
    compressor = MessageCompressor()
    bottle = {
        "type": "data",
        "payload": {
            "batch_size": 100,
            "items": [{"id": i} for i in range(100)],
        },
    }

    result = compressor.compress(bottle)

    assert result["batch_size"] == 100
    assert len(result["items"]) <= 10  # Limited for edge
    assert result["compressed"] is True


def test_compress_priority():
    """Test priority message compression."""
    compressor = MessageCompressor()
    bottle = {
        "type": "priority",
        "payload": {
            "priority": "high",
            "task": "Update system",
            "reason": "Security patch",
        },
    }

    result = compressor.compress(bottle)

    assert result["original"] == "high"
    assert result["translated"] == "handle_soon"
    assert result["task"] == "Update system"
    assert result["compressed"] is True


def test_priority_translation():
    """Test cloud to edge priority translation."""
    compressor = MessageCompressor()

    assert compressor._translate_priority("low") == "ignore"
    assert compressor._translate_priority("medium") == "queue"
    assert compressor._translate_priority("high") == "handle_soon"
    assert compressor._translate_priority("critical") == "immediate"
    assert compressor._translate_priority("unknown") == "queue"
