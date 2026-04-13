"""Tests for bottle handling."""

import pytest
import json
from tenderctl.bottles import Bottle, read_bottle, write_bottle


def test_bottle_creation():
    """Test creating a bottle."""
    bottle = Bottle(
        id="test-1",
        origin="cloud",
        target="edge",
        type="research",
        payload={"data": "test"},
        priority="high",
    )

    assert bottle.id == "test-1"
    assert bottle.origin == "cloud"
    assert bottle.target == "edge"
    assert bottle.type == "research"
    assert bottle.priority == "high"
    assert bottle.status == "pending"


def test_bottle_to_dict():
    """Test converting bottle to dictionary."""
    bottle = Bottle(
        id="test-1",
        origin="cloud",
        target="edge",
        type="research",
        payload={"data": "test"},
    )

    result = bottle.to_dict()

    assert result["id"] == "test-1"
    assert result["origin"] == "cloud"
    assert result["target"] == "edge"
    assert result["type"] == "research"
    assert result["payload"] == {"data": "test"}


def test_bottle_to_json():
    """Test converting bottle to JSON."""
    bottle = Bottle(
        id="test-1",
        origin="cloud",
        target="edge",
        type="research",
        payload={"data": "test"},
    )

    result = bottle.to_json()
    parsed = json.loads(result)

    assert parsed["id"] == "test-1"
    assert parsed["origin"] == "cloud"


def test_bottle_from_json():
    """Test creating bottle from JSON."""
    json_str = '{"id": "test-1", "origin": "cloud", "target": "edge", "type": "research", "payload": {"data": "test"}, "priority": "medium", "compressed": false, "timestamp": 0, "status": "pending"}'
    bottle = Bottle.from_json(json_str)

    assert bottle.id == "test-1"
    assert bottle.origin == "cloud"
    assert bottle.target == "edge"


def test_read_bottle():
    """Test reading bottle from content."""
    content = '{"id": "test-1", "origin": "cloud", "target": "edge", "type": "research", "payload": {"data": "test"}, "priority": "medium", "compressed": false, "timestamp": 0, "status": "pending"}'
    bottle = read_bottle(content)

    assert bottle is not None
    assert bottle.id == "test-1"


def test_read_invalid_bottle():
    """Test reading invalid bottle returns None."""
    bottle = read_bottle("invalid json")
    assert bottle is None


def test_write_bottle():
    """Test writing bottle to string."""
    bottle = Bottle(
        id="test-1",
        origin="cloud",
        target="edge",
        type="research",
        payload={"data": "test"},
    )

    result = write_bottle(bottle)
    parsed = json.loads(result)

    assert parsed["id"] == "test-1"
