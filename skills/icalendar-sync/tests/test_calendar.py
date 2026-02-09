#!/usr/bin/env python3
"""
Unit tests for iCalendar Sync
"""

import pytest
import sys
import os
from unittest.mock import Mock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from icalendar_sync.calendar import CalendarManager


class TestCalendarManager:
    """Test CalendarManager"""
    
    def test_init(self):
        """Test initialization"""
        manager = CalendarManager()
        assert manager.username is None or isinstance(manager.username, str)
        assert manager.password is None or isinstance(manager.password, str)
    
    @patch('icalendar_sync.calendar.DAVClient')
    def test_connect_success(self, mock_client):
        """Test successful connection"""
        mock_principal = Mock()
        mock_principal.calendars.return_value = []
        mock_client.return_value.principal.return_value = mock_principal
        
        with patch.dict(os.environ, {'ICLOUD_USERNAME': 'test@icloud.com', 
                                     'ICLOUD_APP_PASSWORD': 'test-pass'}):
            manager = CalendarManager()
            result = manager.connect()
            assert result