"""Tests for tenderctl CLI."""

import pytest
import json
import tempfile
import os
from unittest.mock import Mock, patch
from tenderctl.cli import TenderCtl
from tenderctl.state import StateManager


@pytest.fixture
def mock_github_token():
    """Fixture to provide a mock GITHUB_TOKEN."""
    with patch.dict(os.environ, {"GITHUB_TOKEN": "test_token"}):
        yield


def test_tenderctl_initialization(mock_github_token):
    """Test TenderCtl initialization."""
    with tempfile.TemporaryDirectory() as tmpdir:
        state_file = os.path.join(tmpdir, "state.json")
        ctl = TenderCtl()
        ctl.state = StateManager(state_file)

        assert ctl.github is not None
        assert ctl.compressor is not None
        assert ctl.translator is not None


def test_status_command(mock_github_token):
    """Test status command."""
    with tempfile.TemporaryDirectory() as tmpdir:
        state_file = os.path.join(tmpdir, "state.json")
        ctl = TenderCtl()
        ctl.state = StateManager(state_file)

        # Add a bottle
        ctl.state.add_bottle(
            "test-vessel/bottle-1.json",
            "test-vessel",
            {"type": "research", "priority": "high"}
        )

        # Get status
        status = ctl.status("test-vessel")

        assert status["vessel"] == "test-vessel"
        assert status["pending"] == 1
        assert status["delivered"] == 0
        assert status["acked"] == 0


def test_ack_command(mock_github_token):
    """Test ack command."""
    with tempfile.TemporaryDirectory() as tmpdir:
        state_file = os.path.join(tmpdir, "state.json")
        ctl = TenderCtl()
        ctl.state = StateManager(state_file)

        # Add a bottle
        ctl.state.add_bottle(
            "test-vessel/bottle-1.json",
            "test-vessel",
            {"type": "research", "priority": "high"}
        )

        # Ack the bottle
        result = ctl.ack("test-vessel", "bottle-1.json")

        assert result["success"] is True
        assert result["status"] == "acked"

        # Verify state
        status = ctl.status("test-vessel")
        assert status["acked"] == 1


def test_ack_nonexistent_bottle(mock_github_token):
    """Test ack command with non-existent bottle."""
    with tempfile.TemporaryDirectory() as tmpdir:
        state_file = os.path.join(tmpdir, "state.json")
        ctl = TenderCtl()
        ctl.state = StateManager(state_file)

        result = ctl.ack("test-vessel", "nonexistent.json")

        assert result["success"] is False
        assert "not found" in result["error"]
