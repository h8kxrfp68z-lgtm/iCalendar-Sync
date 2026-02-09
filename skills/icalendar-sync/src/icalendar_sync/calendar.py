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
            event.add('summary', event_data.get('summary', 'New Event'))
            event.add('dtstart', event_data['dtstart'])
            event.add('dtend', event_data['dtend'])
            
            if 'location' in event_data:
                event.add('location', event_data['location'])
            if 'description' in event_data:
                event.add('description', event_data['description'])
            if 'status' in event_data:
                event.add('status', event_data['status'])
            if 'priority' in event_data:
                event.add('priority', event_data['priority'])
            
            # Add alarms if specified
            if 'alarms' in event_data:
                for alarm_data in event_data['alarms']:
                    alarm = Alarm()
                    alarm.add('action', 'DISPLAY')
                    alarm.add('trigger', timedelta(minutes=-alarm_data.get('minutes', 15)))
                    alarm.add('description', alarm_data.get('description', 'Reminder'))
                    event.add_component(alarm)
            
            # Add recurring rules if specified
            if 'rrule' in event_data:
                rrule = event_data['rrule']
                rrule_str = f"FREQ={rrule.get('freq', 'WEEKLY')}"
                if 'count' in rrule:
                    rrule_str += f";COUNT={rrule['count']}"
                if 'interval' in rrule:
                    rrule_str += f";INTERVAL={rrule['interval']}"
                event.add('rrule', rrule_str)
            
            cal.add_component(event)
            
            # Save event
            calendar.save_event(cal.to_ical().decode('utf-8'))
            
            print(f"✅ Event '{event_data.get('summary')}' created successfully")
            logger.info(f"Created event: {event_data.get('summary')} in {calendar_name}")
            return True
            
        except Exception as e:
            print(f"❌ Error creating event: {e}")
            logger.error(f"Error creating event: {str(e)}")
            return False
    
    def delete_event(self, calendar_name: str, event_uid: str) -> bool:
        """Delete event"""
        if not self.connect():
            return False
        
        try:
            principal = self.client.principal()
            calendar = principal.calendar(name=calendar_name)
            
            event = calendar.event_by_uid(event_uid)
            event.delete()
            
            print(f"🗑️  Event deleted successfully")
            logger.info(f"Deleted event: {event_uid} from {calendar_name}")
            return True
            
        except Exception as e:
            print(f"❌ Error deleting event: {e}")
            logger.error(f"Error deleting event: {str(e)}")
            return False


def cmd_setup(args):
    """Interactive setup of credentials"""
    print("\n🔧 iCalendar Sync Setup\n")
    print("To use iCalendar Sync, you need to configure your iCloud credentials.")
    print("⚠️  Use an App-Specific Password, NOT your regular Apple ID password.\n")
    print("Get it from: https://appleid.apple.com -> Sign-In & Security -> App-Specific Passwords\n")
    
    email = input("📧 iCloud Email: ").strip()
    if not email:
        print("❌ Email cannot be empty")
        return
    
    password = getpass.getpass("🔑 App-Specific Password (xxxx-xxxx-xxxx-xxxx): ").strip()
    if not password:
        print("❌ Password cannot be empty")
        return
    
    # Validate format
    if not all(c.isalnum() or c == '-' for c in password):
        print("⚠️  Password format looks unusual")
        response = input("Are you sure this is correct? (y/n): ").lower()
        if response != 'y':
            print("Setup cancelled")
            return
    
    # Save to .env
    env_path = os.path.expanduser("~/.openclaw/.env")
    os.makedirs(os.path.dirname(env_path), exist_ok=True)
    
    # Read existing
    lines = []
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            lines = [l for l in f.readlines() 
                    if not l.startswith(('ICLOUD_USERNAME', 'ICLOUD_APP_PASSWORD'))]
    
    # Write
    lines.append(f'ICLOUD_USERNAME="{email}"\\n')
    lines.append(f'ICLOUD_APP_PASSWORD="{password}"\\n')
    
    with open(env_path, 'w') as f:
        f.writelines(lines)
    
    os.chmod(env_path, 0o600)
    print(f"\n✅ Configuration saved securely to {env_path}")
    print("🚀 You can now use iCalendar Sync!\n")


def cmd_list(args):
    """List calendars"""
    manager = CalendarManager()
    manager.list_calendars()


def cmd_get_events(args):
    """Get events from calendar"""
    if not args.calendar:
        print("❌ Calendar name required")
        return
    
    manager = CalendarManager()
    manager.get_events(args.calendar, args.days_ahead)


def cmd_create_event(args):
    """Create event"""
    if not args.calendar or not args.json:
        print("❌ Calendar and JSON data required")
        return
    
    try:
        # Parse JSON
        if os.path.isfile(args.json):
            with open(args.json, 'r') as f:
                event_data = json.load(f)
        else:
            event_data = json.loads(args.json)
        
        # Convert string dates to datetime
        if 'dtstart' in event_data and isinstance(event_data['dtstart'], str):
            event_data['dtstart'] = datetime.fromisoformat(event_data['dtstart'])
        if 'dtend' in event_data and isinstance(event_data['dtend'], str):
            event_data['dtend'] = datetime.fromisoformat(event_data['dtend'])
        
        manager = CalendarManager()
        manager.create_event(args.calendar, event_data)
        
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON: {e}")
        return


def cmd_delete_event(args):
    """Delete event"""
    if not args.calendar or not args.uid:
        print("❌ Calendar and event UID required")
        return
    
    manager = CalendarManager()
    manager.delete_event(args.calendar, args.uid)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='iCalendar Sync - Professional iCloud Calendar for OpenClaw',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  icalendar-sync setup                                  # Configure credentials
  icalendar-sync list                                   # List calendars
  icalendar-sync get --calendar "Work" --days 7         # Get events
  icalendar-sync create --calendar "Personal" --json '{"summary":"Meeting","dtstart":"2026-02-10T14:00:00","dtend":"2026-02-10T15:00:00"}'
  icalendar-sync delete --calendar "Work" --uid "event-id"
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Setup
    setup_parser = subparsers.add_parser('setup', help='Configure iCloud credentials')
    setup_parser.set_defaults(func=cmd_setup)
    
    # List
    list_parser = subparsers.add_parser('list', help='List calendars')
    list_parser.set_defaults(func=cmd_list)
    
    # Get events
    get_parser = subparsers.add_parser('get', help='Get calendar events')
    get_parser.add_argument('--calendar', help='Calendar name')
    get_parser.add_argument('--days', type=int, default=7, dest='days_ahead',
                           help='Days ahead to retrieve (default: 7)')
    get_parser.set_defaults(func=cmd_get_events)
    
    # Create event
    create_parser = subparsers.add_parser('create', help='Create calendar event')
    create_parser.add_argument('--calendar', required=True, help='Calendar name')
    create_parser.add_argument('--json', required=True, 
                              help='JSON with event data (file path or JSON string)')
    create_parser.set_defaults(func=cmd_create_event)
    
    # Delete event
    delete_parser = subparsers.add_parser('delete', help='Delete calendar event')
    delete_parser.add_argument('--calendar', required=True, help='Calendar name')
    delete_parser.add_argument('--uid', required=True, help='Event UID')
    delete_parser.set_defaults(func=cmd_delete_event)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(0)
    
    args.func(args)


if __name__ == '__main__':
    main()