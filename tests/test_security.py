#!/usr/bin/env python3
"""
Security-focused tests for iCalendar Sync.
"""

import argparse
import os
import sys
from datetime import datetime, timezone
from unittest.mock import patch
from keyring.errors import KeyringError

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from icalendar_sync.calendar import CalendarManager, cmd_setup, validate_secret_value


def test_validate_secret_value_rejects_control_chars():
    assert validate_secret_value("xxxx-xxxx-xxxx-xxxx")
    assert not validate_secret_value("xxxx-xxxx\n-xxxx-xxxx")
    assert not validate_secret_value("xxxx-xxxx\r-xxxx-xxxx")
    assert not validate_secret_value("xxxx-\x00xxx-xxxx-xxxx")


def test_setup_non_interactive_requires_env_vars():
    args = argparse.Namespace(username=None, non_interactive=True)

    with patch.dict(os.environ, {}, clear=True):
        with patch("icalendar_sync.calendar.keyring.set_password") as mock_set_password:
            cmd_setup(args)
            mock_set_password.assert_not_called()


def test_setup_non_interactive_saves_to_keyring():
    args = argparse.Namespace(username=None, non_interactive=True)

    with patch.dict(
        os.environ,
        {"ICLOUD_USERNAME": "test@icloud.com", "ICLOUD_APP_PASSWORD": "xxxx-xxxx-xxxx-xxxx"},
        clear=True,
    ):
        with patch("icalendar_sync.calendar.keyring.set_password") as mock_set_password:
            cmd_setup(args)
            mock_set_password.assert_called_once_with(
                "openclaw-icalendar",
                "test@icloud.com",
                "xxxx-xxxx-xxxx-xxxx",
            )


def test_setup_keyring_error_does_not_write_plaintext_file():
    args = argparse.Namespace(username=None, non_interactive=True)

    with patch.dict(
        os.environ,
        {"ICLOUD_USERNAME": "test@icloud.com", "ICLOUD_APP_PASSWORD": "xxxx-xxxx-xxxx-xxxx"},
        clear=True,
    ):
        with patch(
            "icalendar_sync.calendar.keyring.set_password",
            side_effect=KeyringError("keyring unavailable"),
        ):
            with patch("builtins.open") as mock_open:
                cmd_setup(args)
                mock_open.assert_not_called()


def test_update_validation_rejects_invalid_time_range():
    manager = CalendarManager()
    start = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)
    end = datetime(2026, 1, 1, 11, 0, tzinfo=timezone.utc)
    event = {"DTSTART": start, "DTEND": end}

    assert manager._validate_event_time_range(event) is False
