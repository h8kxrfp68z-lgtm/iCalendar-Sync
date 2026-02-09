#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
iCalendar Sync - Main Calendar Manager
Professional iCloud Calendar integration

@author: Black_Temple
@version: 2.1.1
"""

import os
import sys
import argparse
import getpass
import json
import logging
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Optional, Tuple
from functools import wraps
import time

try:
    import caldav
    from caldav.davclient import DAVClient
    from caldav.lib.error import AuthorizationError, NotFoundError, DAVError
    from icalendar import Calendar as iCal, Event as iEvent, Alarm, vRecur
    import requests.exceptions
except ImportError:
    print("❌ Required packages not installed. Run: pip install -r requirements.txt")
    sys.exit(1)

__author__ = "Black_Temple"
__version__ = "2.1.1"

# Setup logging
logging.basicConfig(
    level=os.getenv('LOG_LEVEL', 'INFO'),
    format='%(asctime)s | %(levelname)s | %(message)s'
)
logger = logging.getLogger(__name__)


def retry(max_attempts: int = 3, delay: float = 1.0, backoff: float = 2.0):
    """Retry decorator with exponential backoff"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            attempt = 0
            current_delay = delay
            while attempt < max_attempts:
                try:
                    return func(*args, **kwargs)
                except (requests.exceptions.RequestException, DAVError) as e:
                    attempt += 1
                    if attempt >= max_attempts:
                        logger.error(f"Failed after {max_attempts} attempts: {str(e)}")
                        raise
                    logger.warning(f"Attempt {attempt} failed, retrying in {current_delay}s: {str(e)}")
                    time.sleep(current_delay)
                    current_delay *= backoff
            return None
        return wrapper
    return decorator


class CalendarManager:
    """Manage iCloud Calendar via CalDAV"""
    
    def __init__(self):
        self.username = os.getenv('ICLOUD_USERNAME')
        self.password = os.getenv('ICLOUD_APP_PASSWORD')
        self.client: Optional[DAVClient] = None
        self._connected: bool = False
        self._connection_time: Optional[datetime] = None
        self._cache_timeout: int = 300  # 5 minutes
    
    def _is_connection_valid(self) -> bool:
        """Check if cached connection is still valid"""
        if not self._connected or not self._connection_time:
            return False
        elapsed = (datetime.now(timezone.utc) - self._connection_time).total_seconds()
        return elapsed < self._cache_timeout
    
    @retry(max_attempts=3, delay=1.0, backoff=2.0)
    def connect(self) -> bool:
        """Connect to iCloud CalDAV with retry logic and connection caching"""
        # Return cached connection if valid
        if self._is_connection_valid():
            logger.debug("Using cached CalDAV connection")
            return True
        
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
            
            self._connected = True
            self._connection_time = datetime.now(timezone.utc)
            logger.info("Successfully connected to iCloud CalDAV")
            return True
            
        except AuthorizationError as e:
            print(f"❌ Authentication failed: Invalid credentials")
            logger.error(f"Authentication failed: {str(e)}")
            self._connected = False
            return False
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
            print(f"❌ Network error: {e}")
            logger.error(f"Network error: {str(e)}")
            self._connected = False
            raise  # Re-raise for retry decorator
        except DAVError as e:
            print(f"❌ CalDAV error: {e}")
            logger.error(f"CalDAV error: {str(e)}")
            self._connected = False
            raise  # Re-raise for retry decorator
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            logger.error(f"Unexpected connection error: {str(e)}")
            self._connected = False
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
            
        except NotFoundError as e:
            print(f"❌ Calendars not found: {e}")
            logger.error(f"Calendars not found: {str(e)}")
            return []
        except DAVError as e:
            print(f"❌ CalDAV error: {e}")
            logger.error(f"Error listing calendars: {str(e)}")
            return []
        except Exception as e:
            print(f"❌ Error: {e}")
            logger.error(f"Unexpected error listing calendars: {str(e)}")
            return []
    
    def _check_event_conflicts(
        self, 
        calendar, 
        start: datetime, 
        end: datetime, 
        exclude_uid: Optional[str] = None
    ) -> List[Dict]:
        """Check for conflicting events in the given time range"""
        try:
            events = calendar.search(
                start=start - timedelta(hours=1),
                end=end + timedelta(hours=1),
                event=True,
                expand=True
            )
            
            conflicts = []
            for event in events:
                ical = iCal.from_ical(event.data)
                for component in ical.walk():
                    if component.name == "VEVENT":
                        evt_uid = str(component.get('uid', ''))
                        if exclude_uid and evt_uid == exclude_uid:
                            continue
                        
                        evt_start = component.get('dtstart')
                        evt_end = component.get('dtend')
                        
                        if evt_start and evt_end:
                            evt_start_dt = evt_start.dt
                            evt_end_dt = evt_end.dt
                            
                            # Convert to datetime if date
                            if not isinstance(evt_start_dt, datetime):
                                evt_start_dt = datetime.combine(evt_start_dt, datetime.min.time())
                                evt_start_dt = evt_start_dt.replace(tzinfo=timezone.utc)
                            if not isinstance(evt_end_dt, datetime):
                                evt_end_dt = datetime.combine(evt_end_dt, datetime.max.time())
                                evt_end_dt = evt_end_dt.replace(tzinfo=timezone.utc)
                            
                            # Check overlap
                            if not (end <= evt_start_dt or start >= evt_end_dt):
                                conflicts.append({
                                    'summary': str(component.get('summary', 'No title')),
                                    'start': evt_start_dt,
                                    'end': evt_end_dt,
                                    'uid': evt_uid
                                })
            
            return conflicts
            
        except Exception as e:
            logger.warning(f"Could not check conflicts: {str(e)}")
            return []
    
    def get_events(self, calendar_name: str, days_ahead: int = 7) -> List:
        """Get calendar events"""
        if not self.connect():
            return []
        
        try:
            principal = self.client.principal()
            calendar = principal.calendar(name=calendar_name)
            
            start = datetime.now(timezone.utc)
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
            
        except NotFoundError as e:
            print(f"❌ Calendar '{calendar_name}' not found")
            logger.error(f"Calendar not found: {str(e)}")
            return []
        except DAVError as e:
            print(f"❌ CalDAV error: {e}")
            logger.error(f"Error getting events: {str(e)}")
            return []
        except Exception as e:
            print(f"❌ Error: {e}")
            logger.error(f"Unexpected error getting events: {str(e)}")
            return []
    
    def create_event(
        self, 
        calendar_name: str, 
        event_data: Dict,
        check_conflicts: bool = True
    ) -> bool:
        """Create new event with validation and conflict detection"""
        if not self.connect():
            return False
        
        # Validate required fields
        required_fields = ['summary', 'dtstart', 'dtend']
        missing_fields = [f for f in required_fields if f not in event_data]
        if missing_fields:
            print(f"❌ Missing required fields: {', '.join(missing_fields)}")
            logger.error(f"Missing required fields: {missing_fields}")
            return False
        
        # Validate datetime objects
        if not isinstance(event_data['dtstart'], datetime):
            print("❌ dtstart must be a datetime object")
            return False
        if not isinstance(event_data['dtend'], datetime):
            print("❌ dtend must be a datetime object")
            return False
        
        # Ensure timezone awareness
        dtstart = event_data['dtstart']
        dtend = event_data['dtend']
        
        if dtstart.tzinfo is None:
            dtstart = dtstart.replace(tzinfo=timezone.utc)
            logger.warning("dtstart had no timezone, assuming UTC")
        if dtend.tzinfo is None:
            dtend = dtend.replace(tzinfo=timezone.utc)
            logger.warning("dtend had no timezone, assuming UTC")
        
        # Validate time range
        if dtend <= dtstart:
            print("❌ Event end time must be after start time")
            return False
        
        try:
            principal = self.client.principal()
            calendar = principal.calendar(name=calendar_name)
            
            # Check conflicts
            if check_conflicts:
                conflicts = self._check_event_conflicts(calendar, dtstart, dtend)
                if conflicts:
                    print(f"⚠️  Warning: {len(conflicts)} conflicting event(s) found:")
                    for conf in conflicts:
                        print(f"   - {conf['summary']} ({conf['start']} to {conf['end']})")
                    
                    response = input("Continue anyway? (y/n): ").lower()
                    if response != 'y':
                        print("Event creation cancelled")
                        return False
            
            # Create iCalendar event
            cal = iCal()
            cal.add('prodid', '-//iCalendar Sync//EN')
            cal.add('version', '2.0')
            
            event = iEvent()
            import uuid
            event.add('uid', str(uuid.uuid4()))
            event.add('dtstamp', datetime.now(timezone.utc))
            event.add('summary', event_data['summary'])
            event.add('dtstart', dtstart)
            event.add('dtend', dtend)
            
            # Optional fields
            if 'location' in event_data:
                event.add('location', event_data['location'])
            if 'description' in event_data:
                event.add('description', event_data['description'])
            if 'status' in event_data:
                event.add('status', event_data['status'])
            if 'priority' in event_data:
                event.add('priority', event_data['priority'])
            
            # Add alarms if specified
            if 'alarms' in event_data and isinstance(event_data['alarms'], list):
                for alarm_data in event_data['alarms']:
                    alarm = Alarm()
                    alarm.add('action', 'DISPLAY')
                    alarm.add('trigger', timedelta(minutes=-alarm_data.get('minutes', 15)))
                    alarm.add('description', alarm_data.get('description', 'Reminder'))
                    event.add_component(alarm)
            
            # Add recurring rules if specified
            if 'rrule' in event_data:
                rrule_data = event_data['rrule']
                rrule_dict = {'FREQ': [rrule_data.get('freq', 'WEEKLY')]}
                
                if 'count' in rrule_data:
                    rrule_dict['COUNT'] = [rrule_data['count']]
                if 'interval' in rrule_data:
                    rrule_dict['INTERVAL'] = [rrule_data['interval']]
                if 'byday' in rrule_data:
                    rrule_dict['BYDAY'] = rrule_data['byday']
                if 'until' in rrule_data:
                    rrule_dict['UNTIL'] = [rrule_data['until']]
                
                event.add('rrule', rrule_dict)
            
            cal.add_component(event)
            
            # Save event
            calendar.save_event(cal.to_ical().decode('utf-8'))
            
            print(f"✅ Event '{event_data['summary']}' created successfully")
            logger.info(f"Created event: {event_data['summary']} in {calendar_name}")
            return True
            
        except NotFoundError as e:
            print(f"❌ Calendar '{calendar_name}' not found")
            logger.error(f"Calendar not found: {str(e)}")
            return False
        except DAVError as e:
            print(f"❌ CalDAV error: {e}")
            logger.error(f"Error creating event: {str(e)}")
            return False
        except Exception as e:
            print(f"❌ Error creating event: {e}")
            logger.error(f"Unexpected error creating event: {str(e)}")
            return False
    
    def delete_event(self, calendar_name: str, event_uid: str) -> bool:
        """Delete event"""
        if not self.connect():
            return False
        
        if not event_uid or not isinstance(event_uid, str):
            print("❌ Valid event UID required")
            return False
        
        try:
            principal = self.client.principal()
            calendar = principal.calendar(name=calendar_name)
            
            event = calendar.event_by_uid(event_uid)
            event.delete()
            
            print(f"🗑️  Event deleted successfully")
            logger.info(f"Deleted event: {event_uid} from {calendar_name}")
            return True
            
        except NotFoundError as e:
            print(f"❌ Event or calendar not found")
            logger.error(f"Event/calendar not found: {str(e)}")
            return False
        except DAVError as e:
            print(f"❌ CalDAV error: {e}")
            logger.error(f"Error deleting event: {str(e)}")
            return False
        except Exception as e:
            print(f"❌ Error deleting event: {e}")
            logger.error(f"Unexpected error deleting event: {str(e)}")
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
    
    # Basic email validation
    if '@' not in email or '.' not in email.split('@')[1]:
        print("⚠️  Email format looks invalid")
        response = input("Continue anyway? (y/n): ").lower()
        if response != 'y':
            print("Setup cancelled")
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
    
    # Write with proper newlines
    lines.append(f'ICLOUD_USERNAME="{email}"\n')
    lines.append(f'ICLOUD_APP_PASSWORD="{password}"\n')
    
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
        check_conflicts = not args.no_conflict_check if hasattr(args, 'no_conflict_check') else True
        manager.create_event(args.calendar, event_data, check_conflicts=check_conflicts)
        
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON: {e}")
        return
    except ValueError as e:
        print(f"❌ Invalid datetime format: {e}")
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
  icalendar-sync create --calendar "Personal" --json '{"summary":"Meeting","dtstart":"2026-02-10T14:00:00+03:00","dtend":"2026-02-10T15:00:00+03:00"}'
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
    create_parser.add_argument('--no-conflict-check', action='store_true',
                              help='Skip conflict detection')
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
