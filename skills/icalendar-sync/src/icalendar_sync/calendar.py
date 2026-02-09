#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
iCalendar Sync - Main Calendar Manager
Professional iCloud Calendar integration

@author: Black_Temple
@version: 2.1.0
"""

import os
import sys
import argparse
import getpass
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional

try:
    import caldav
    from caldav.davclient import DAVClient
    from icalendar import Calendar as iCal, Event as iEvent, Alarm
except ImportError:
    print("❌ Required packages not installed. Run: pip install -r requirements.txt")
    sys.exit(1)

__author__ = "Black_Temple"
__version__ = "2.1.0"

# Setup logging
logging.basicConfig(
    level=os.getenv('LOG_LEVEL', 'INFO'),
    format='%(asctime)s | %(levelname)s | %(message)s'
)
logger = logging.getLogger(__name__)


class CalendarManager:
    """Manage iCloud Calendar via CalDAV"""
    
    def __init__(self):
        self.username = os.getenv('ICLOUD_USERNAME')
        self.password = os.getenv('ICLOUD_APP_PASSWORD')
        self.client = None
    
    def connect(self) -> bool:
        """Connect to iCloud CalDAV"""
        if not self.username or not self.password:
            print("❌ iCloud credentials not configured")
            logger.error("Missing iCloud credentials")
            return False
        
        try:
            self.client = DAVClient(
                url="https://caldav.icloud.com",
                username=self.username,
                password=self.password
            )
            principal = self.client.principal()
            principal.calendars()
            logger.info("Successfully connected to iCloud CalDAV")
            return True
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            logger.error(f"Connection failed: {str(e)}")
            return False
    
    def list_calendars(self) -> List[str]:
        """List all calendars"""
        if not self.connect():
            return []
        
        try:
            principal = self.client.principal()
            calendars = principal.calendars()
            
            print(f"📅 Available Calendars ({len(calendars)}):\n")
            calendar_names = []
            
            for cal in calendars:
                print(f"  • {cal.name}")
                calendar_names.append(cal.name)
                logger.info(f"Found calendar: {cal.name}")
            
            return calendar_names
        except Exception as e:
            print(f"❌ Error: {e}")
            logger.error(f"Error listing calendars: {str(e)}")
            return []
    
    def get_events(self, calendar_name: str, days_ahead: int = 7) -> List:
        """Get calendar events"""
        if not self.connect():
            return []
        
        try:
            principal = self.client.principal()
            calendar = principal.calendar(name=calendar_name)
            
            start = datetime.now()
            end = start + timedelta(days=days_ahead)
            
            events = calendar.search(
                start=start,
                end=end,
                event=True,
                expand=True
            )
            
            print(f"📋 Events in '{calendar_name}' ({len(events)} found):\n")
            
            for event in events:
                ical = iCal.from_ical(event.data)
                for component in ical.walk():
                    if component.name == "VEVENT":
                        summary = component.get('summary', 'No title')
                        dtstart = component.get('dtstart')
                        dtend = component.get('dtend')
                        uid = component.get('uid')
                        
                        print(f"  🗓️  {summary}")
                        if dtstart:
                            print(f"     Start: {dtstart.dt}")
                        if dtend:
                            print(f"     End: {dtend.dt}")
                        print(f"     UID: {uid}\n")
                        
                        logger.info(f"Found event: {summary}")
            
            return events
        except Exception as e:
            print(f"❌ Error: {e}")
            logger.error(f"Error getting events: {str(e)}")
            return []
    
    def create_event(self, calendar_name: str, event_data: Dict) -> bool:
        """Create new event"""
        if not self.connect():
            return False
        
        try:
            principal = self.client.principal()
            calendar = principal.calendar(name=calendar_name)
            
            # Create iCalendar event
            cal = iCal()
            cal.add('prodid', '-//iCalendar Sync//EN')
            cal.add('version', '2.0')
            
            event = iEvent()
            import uuid
            event.add('uid', str(uuid.uuid4()))
            event.add('dtstamp', datetime.now())
            event.add('summary', event_data.
