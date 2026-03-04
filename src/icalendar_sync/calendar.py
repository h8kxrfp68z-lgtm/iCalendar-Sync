#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
iCalendar Sync - Main Calendar Manager
Professional iCloud Calendar integration

@author: Black_Temple
@version: 2.3.0
"""

import os
import sys
import argparse
import getpass
import json
import logging
import re
import threading
import tempfile
import shutil
import subprocess
import base64
from datetime import datetime, timedelta, timezone, time as dt_time
from typing import List, Dict, Optional
from functools import wraps
import time
from pathlib import Path
from urllib.parse import urljoin, urlparse

try:
    from icalendar import Calendar as iCal, Event as iEvent, Alarm
    import requests
    import requests.exceptions
    import yaml
except ImportError as e:
    print(f"❌ Required packages not installed: {e}")
    print("Run: pip install -r requirements.txt")
    sys.exit(1)

CALDAV_AVAILABLE = True
CALDAV_IMPORT_ERROR = ""
try:
    import caldav
    from caldav.davclient import DAVClient
    from caldav.lib.error import AuthorizationError, NotFoundError, DAVError
except ImportError as e:
    CALDAV_AVAILABLE = False
    CALDAV_IMPORT_ERROR = str(e)
    caldav = None
    DAVClient = None

    class AuthorizationError(Exception):
        """Fallback AuthorizationError when caldav is unavailable."""
        pass

    class NotFoundError(Exception):
        """Fallback NotFoundError when caldav is unavailable."""
        pass

    class DAVError(Exception):
        """Fallback DAVError when caldav is unavailable."""
        pass

KEYRING_AVAILABLE = True
KEYRING_IMPORT_ERROR = ""
try:
    import keyring
    from keyring.errors import KeyringError
except ImportError as e:
    KEYRING_AVAILABLE = False
    KEYRING_IMPORT_ERROR = str(e)
    keyring = None

    class KeyringError(Exception):
        """Fallback KeyringError when keyring is unavailable."""
        pass

__author__ = "Black_Temple"
__version__ = "2.3.0"

# Security constants
MAX_CALENDAR_NAME_LENGTH = 255
MAX_SUMMARY_LENGTH = 500
MAX_DESCRIPTION_LENGTH = 5000
MAX_LOCATION_LENGTH = 500
MAX_JSON_FILE_SIZE = 1024 * 1024  # 1MB
MAX_DAYS_AHEAD = 365
MIN_DAYS_AHEAD = 1
RATE_LIMIT_CALLS = 10  # calls per window
RATE_LIMIT_WINDOW = 60  # seconds
INPUT_TIMEOUT = 30  # seconds for interactive input
MAX_CONFIG_FILE_SIZE = 64 * 1024  # 64KB
DEFAULT_CONFIG_PATH = Path.home() / ".openclaw" / "icalendar-sync.yaml"
DEFAULT_USER_AGENT = "macOS/14.0.0 (23A344) CalendarAgent/954"

# Setup logging with sensitive data filtering
class SensitiveDataFilter(logging.Filter):
    """Filter sensitive data from logs"""
    SENSITIVE_PATTERNS = [
        (re.compile(r'password["\']?\s*[:=]\s*["\']?([^"\',\s]+)', re.IGNORECASE), 'password=***'),
        (re.compile(r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', re.IGNORECASE), '***@***.***'),
        (re.compile(r'(xxxx-xxxx-xxxx-xxxx|\d{4}-\d{4}-\d{4}-\d{4})'), '****-****-****-****'),
    ]
    
    def filter(self, record):
        record.msg = self._sanitize(str(record.msg))
        if record.args:
            record.args = tuple(self._sanitize(str(arg)) for arg in record.args)
        return True
    
    def _sanitize(self, text: str) -> str:
        for pattern, replacement in self.SENSITIVE_PATTERNS:
            text = pattern.sub(replacement, text)
        return text

logging.basicConfig(
    level=os.getenv('LOG_LEVEL', 'WARNING'),
    format='%(asctime)s | %(levelname)s | %(message)s'
)
logger = logging.getLogger(__name__)
logger.addFilter(SensitiveDataFilter())


class RateLimiter:
    """Simple rate limiter for API calls"""
    def __init__(self, max_calls: int, window: int):
        self.max_calls = max_calls
        self.window = window
        self.calls = []
        self.lock = threading.Lock()
    
    def acquire(self) -> bool:
        """Try to acquire rate limit token"""
        with self.lock:
            now = time.time()
            # Remove old calls outside window
            self.calls = [call_time for call_time in self.calls if now - call_time < self.window]
            
            if len(self.calls) >= self.max_calls:
                return False
            
            self.calls.append(now)
            return True
    
    def wait_if_needed(self):
        """Wait until rate limit allows"""
        while not self.acquire():
            time.sleep(1)


def retry(max_attempts: int = 3, delay: float = 1.0, backoff: float = 2.0):
    """Retry decorator with exponential backoff and traceback cleanup"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            attempt = 0
            current_delay = delay
            last_exception = None
            
            while attempt < max_attempts:
                try:
                    return func(*args, **kwargs)
                except (requests.exceptions.RequestException, DAVError) as e:
                    attempt += 1
                    last_exception = e
                    
                    if attempt >= max_attempts:
                        logger.error(f"Failed after {max_attempts} attempts")
                        raise
                    
                    logger.warning(f"Attempt {attempt} failed, retrying in {current_delay}s")
                    time.sleep(current_delay)
                    current_delay *= backoff
                    
                    # Clear exception to prevent memory leak
                    del e
            
            return None
        return wrapper
    return decorator


def validate_calendar_name(name: str) -> bool:
    """Validate calendar name for security (supports Unicode/Cyrillic)"""
    if not name or not isinstance(name, str):
        return False
    if len(name) > MAX_CALENDAR_NAME_LENGTH:
        return False
    # Allow Unicode letters, digits, spaces, hyphens, underscores
    # \w in Python re includes Unicode letters when re.UNICODE flag is used
    if not re.match(r'^[\w\s_-]+$', name, re.UNICODE):
        return False
    # Prevent path traversal
    if '..' in name or '/' in name or '\\' in name:
        return False
    return True


def validate_email(email: str) -> bool:
    """Validate email address"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_secret_value(value: str) -> bool:
    """Reject dangerous control characters in secrets."""
    if not value or not isinstance(value, str):
        return False
    return all(char not in value for char in ('\n', '\r', '\x00'))


def is_truthy_env(value: str) -> bool:
    """Parse common truthy env values."""
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def resolve_config_path(config_path: Optional[str] = None) -> Path:
    """Resolve credential config path from arg/env/default."""
    raw_path = config_path or os.getenv("ICALENDAR_SYNC_CONFIG")
    if raw_path:
        return Path(raw_path).expanduser()
    return DEFAULT_CONFIG_PATH


def safe_load_config_credentials(config_path: Optional[str] = None) -> Dict[str, str]:
    """Load credentials from YAML config file."""
    path = resolve_config_path(config_path)

    try:
        path = path.resolve()
    except OSError as e:
        logger.error(f"Invalid config path: {e}")
        return {}

    if not path.is_file():
        return {}

    try:
        stat_result = path.stat()
        if stat_result.st_size > MAX_CONFIG_FILE_SIZE:
            logger.error(f"Config file too large: {stat_result.st_size} bytes")
            return {}

        file_mode = stat_result.st_mode & 0o777
        if file_mode & 0o077:
            logger.warning(
                f"Config file permissions are too open ({oct(file_mode)}). Expected 0o600."
            )

        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

        if not isinstance(data, dict):
            logger.error("Config file must contain a YAML object")
            return {}

        username = data.get("username") or data.get("icloud_username")
        password = data.get("app_password") or data.get("icloud_app_password") or data.get("password")

        if isinstance(username, str):
            username = username.strip()
        else:
            username = ""

        if isinstance(password, str):
            password = password.strip()
        else:
            password = ""

        if password and not validate_secret_value(password):
            logger.error("Config password contains invalid control characters")
            return {}

        result = {}
        if username:
            result["username"] = username
        if password:
            result["password"] = password
        return result

    except (OSError, yaml.YAMLError) as e:
        logger.error(f"Failed to read config file: {e}")
        return {}


def save_config_credentials(config_path: Optional[str], username: str, password: str) -> Optional[Path]:
    """Persist credentials to a YAML config file with strict permissions."""
    path = resolve_config_path(config_path).expanduser()
    tmp_path: Optional[Path] = None

    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            os.chmod(path.parent, 0o700)
        except OSError:
            # Best effort: some systems may deny chmod on existing directories.
            pass

        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            delete=False,
            dir=path.parent,
        ) as tmp:
            tmp_path = Path(tmp.name)
            yaml.safe_dump(
                {"username": username, "app_password": password},
                tmp,
                sort_keys=False,
                default_flow_style=False,
            )

        os.chmod(tmp_path, 0o600)
        shutil.move(str(tmp_path), str(path))
        os.chmod(path, 0o600)
        return path

    except (OSError, yaml.YAMLError) as e:
        logger.error(f"Failed to write config file: {e}")
        if tmp_path and tmp_path.exists():
            try:
                tmp_path.unlink()
            except OSError:
                pass
        return None


def sanitize_text(text: str, max_length: int) -> str:
    """Sanitize and truncate text fields"""
    if not isinstance(text, str):
        text = str(text)
    # Remove control characters
    text = ''.join(char for char in text if char.isprintable() or char in '\n\t')
    # Truncate
    if len(text) > max_length:
        text = text[:max_length-3] + '...'
    return text


def safe_file_read(file_path: str, max_size: int = MAX_JSON_FILE_SIZE) -> Optional[str]:
    """Safely read file with size limit and path validation"""
    try:
        # Resolve and validate path
        path = Path(file_path).resolve()
        
        # Check if file exists
        if not path.is_file():
            logger.error(f"File not found: {file_path}")
            return None
        
        # Check file size
        if path.stat().st_size > max_size:
            logger.error(f"File too large: {path.stat().st_size} bytes (max {max_size})")
            return None
        
        # Read file
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    
    except (OSError, ValueError) as e:
        logger.error(f"Error reading file: {str(e)}")
        return None


def timed_input(prompt: str, timeout: int = INPUT_TIMEOUT) -> Optional[str]:
    """Input with timeout (Unix-like systems)"""
    import signal
    
    def timeout_handler(signum, frame):
        raise TimeoutError("Input timeout")
    
    try:
        # Set signal alarm (Unix only)
        if hasattr(signal, 'SIGALRM'):
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(timeout)
        
        result = input(prompt)
        
        if hasattr(signal, 'SIGALRM'):
            signal.alarm(0)  # Cancel alarm
        
        return result
    
    except TimeoutError:
        print("\n⏱️  Input timeout")
        return None
    except Exception:
        return input(prompt)  # Fallback for Windows


def applescript_escape(value: str) -> str:
    """Escape text for AppleScript string literal."""
    return value.replace("\\", "\\\\").replace('"', '\\"')


def datetime_to_applescript(var_name: str, dt: datetime) -> List[str]:
    """Convert datetime into AppleScript date assignment lines."""
    if dt.tzinfo is not None:
        dt = dt.astimezone()
    month_names = [
        "January",
        "February",
        "March",
        "April",
        "May",
        "June",
        "July",
        "August",
        "September",
        "October",
        "November",
        "December",
    ]
    seconds = dt.hour * 3600 + dt.minute * 60 + dt.second
    return [
        f"set {var_name} to (current date)",
        f"set year of {var_name} to {dt.year}",
        f'set month of {var_name} to {month_names[dt.month - 1]}',
        f"set day of {var_name} to {dt.day}",
        f"set time of {var_name} to {seconds}",
    ]


class MacOSNativeCalendarManager:
    """Bridge provider: operate via native Calendar.app through osascript."""

    def __init__(self):
        if sys.platform != "darwin":
            raise RuntimeError("--provider macos-native is only available on macOS")

    def _run_applescript(self, lines: List[str]) -> Optional[str]:
        script = "\n".join(lines) + "\n"
        try:
            result = subprocess.run(
                ["osascript", "-"],
                input=script,
                text=True,
                capture_output=True,
                check=True,
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            stderr_text = sanitize_text((e.stderr or "").strip(), 500)
            logger.error(f"AppleScript error: {stderr_text}")
            print("❌ macOS Calendar bridge error")
            if stderr_text:
                print(f"   {stderr_text}")
            return None

    def list_calendars(self) -> List[str]:
        lines = [
            'set oldTIDs to AppleScript\'s text item delimiters',
            'set AppleScript\'s text item delimiters to linefeed',
            'tell application "Calendar"',
            'set calNames to name of every calendar',
            'end tell',
            'set outputText to ""',
            'if (count of calNames) > 0 then set outputText to (calNames as text)',
            'set AppleScript\'s text item delimiters to oldTIDs',
            'return outputText',
        ]
        output = self._run_applescript(lines)
        if output is None:
            return []

        calendars = [line.strip() for line in output.splitlines() if line.strip()]
        print(f"📅 Available Calendars ({len(calendars)}):\n")
        for name in calendars:
            print(f"  • {name}")
        return calendars

    def get_events(self, calendar_name: str, days_ahead: int = 7) -> List:
        if not validate_calendar_name(calendar_name):
            print("❌ Invalid calendar name")
            return []
        if not (MIN_DAYS_AHEAD <= days_ahead <= MAX_DAYS_AHEAD):
            print(f"❌ days_ahead must be between {MIN_DAYS_AHEAD} and {MAX_DAYS_AHEAD}")
            return []

        escaped_name = applescript_escape(calendar_name)
        lines = [
            'set oldTIDs to AppleScript\'s text item delimiters',
            'set AppleScript\'s text item delimiters to linefeed',
            'tell application "Calendar"',
            f'if not (exists calendar "{escaped_name}") then error "Calendar not found"',
            f'set calRef to calendar "{escaped_name}"',
            'set startDate to current date',
            f'set endDate to startDate + ({days_ahead} * days)',
            'set eventLines to {}',
            'repeat with e in (every event of calRef whose start date ≥ startDate and start date ≤ endDate)',
            'set end of eventLines to ((summary of e as text) & "|||" & (id of e as text) & "|||" & ((start date of e) as text) & "|||" & ((end date of e) as text))',
            'end repeat',
            'end tell',
            'set outputText to ""',
            'if (count of eventLines) > 0 then set outputText to (eventLines as text)',
            'set AppleScript\'s text item delimiters to oldTIDs',
            'return outputText',
        ]
        output = self._run_applescript(lines)
        if output is None:
            return []

        parsed_events = []
        print(f"📋 Events in '{calendar_name}' ({len([l for l in output.splitlines() if l.strip()])} found):\n")
        for line in output.splitlines():
            if not line.strip():
                continue
            parts = line.split("|||")
            if len(parts) < 4:
                continue
            summary, event_id, start_raw, end_raw = parts[0], parts[1], parts[2], parts[3]
            print(f"  🗓️  {summary}")
            print(f"     Start: {start_raw}")
            print(f"     End: {end_raw}")
            print(f"     UID: {event_id}\n")
            parsed_events.append(
                {
                    "summary": summary,
                    "uid": event_id,
                    "dtstart": start_raw,
                    "dtend": end_raw,
                }
            )
        return parsed_events

    def create_event(
        self,
        calendar_name: str,
        event_data: Dict,
        check_conflicts: bool = True,
        auto_confirm: bool = False
    ) -> bool:
        if not validate_calendar_name(calendar_name):
            print("❌ Invalid calendar name")
            return False

        required_fields = ['summary', 'dtstart', 'dtend']
        missing_fields = [f for f in required_fields if f not in event_data]
        if missing_fields:
            print(f"❌ Missing required fields: {', '.join(missing_fields)}")
            return False

        dtstart = event_data["dtstart"]
        dtend = event_data["dtend"]
        if not isinstance(dtstart, datetime) or not isinstance(dtend, datetime):
            print("❌ dtstart and dtend must be datetime objects")
            return False
        if dtend <= dtstart:
            print("❌ Event end time must be after start time")
            return False

        summary = applescript_escape(sanitize_text(event_data.get("summary", ""), MAX_SUMMARY_LENGTH))
        description = applescript_escape(sanitize_text(event_data.get("description", ""), MAX_DESCRIPTION_LENGTH))
        location = applescript_escape(sanitize_text(event_data.get("location", ""), MAX_LOCATION_LENGTH))
        escaped_name = applescript_escape(calendar_name)

        lines = []
        lines.extend(datetime_to_applescript("startDate", dtstart))
        lines.extend(datetime_to_applescript("endDate", dtend))
        lines.extend([
            'tell application "Calendar"',
            f'if not (exists calendar "{escaped_name}") then error "Calendar not found"',
            f'set calRef to calendar "{escaped_name}"',
            f'set newEvent to make new event at end of events of calRef with properties {{summary:"{summary}", start date:startDate, end date:endDate}}',
        ])
        if description:
            lines.append(f'set description of newEvent to "{description}"')
        if location:
            lines.append(f'set location of newEvent to "{location}"')
        lines.extend([
            'set eventId to id of newEvent',
            'end tell',
            'return eventId as text',
        ])

        output = self._run_applescript(lines)
        if output is None:
            return False

        print(f"✅ Event '{event_data.get('summary', 'Untitled')}' created successfully")
        if output:
            logger.info(f"Created native event id={output}")
        return True

    def delete_event(self, calendar_name: str, event_uid: str) -> bool:
        if not validate_calendar_name(calendar_name):
            print("❌ Invalid calendar name")
            return False
        if not event_uid or not isinstance(event_uid, str):
            print("❌ Valid event UID required")
            return False

        escaped_name = applescript_escape(calendar_name)
        escaped_uid = applescript_escape(event_uid.strip())
        lines = [
            'tell application "Calendar"',
            f'if not (exists calendar "{escaped_name}") then error "Calendar not found"',
            f'set calRef to calendar "{escaped_name}"',
            f'set matches to (every event of calRef whose id is "{escaped_uid}")',
            'if (count of matches) = 0 then error "Event not found"',
            'delete (item 1 of matches)',
            'end tell',
            'return "ok"',
        ]
        output = self._run_applescript(lines)
        if output is None:
            return False
        print("🗑️  Event deleted successfully")
        return True

    def update_event(
        self,
        calendar_name: str,
        event_uid: str,
        update_data: Dict,
        recurrence_id: Optional[str] = None,
        mode: str = 'single'
    ) -> bool:
        if not validate_calendar_name(calendar_name):
            print("❌ Invalid calendar name")
            return False
        if not event_uid or not isinstance(event_uid, str):
            print("❌ Valid event UID required")
            return False
        if mode not in ['single', 'all', 'future']:
            print("❌ Invalid mode. Must be 'single', 'all', or 'future'")
            return False
        if recurrence_id or mode in ('all', 'future'):
            print("⚠️  macOS native provider updates a single event by ID (recurrence mode ignored)")

        escaped_name = applescript_escape(calendar_name)
        escaped_uid = applescript_escape(event_uid.strip())
        lines = [
            'tell application "Calendar"',
            f'if not (exists calendar "{escaped_name}") then error "Calendar not found"',
            f'set calRef to calendar "{escaped_name}"',
            f'set matches to (every event of calRef whose id is "{escaped_uid}")',
            'if (count of matches) = 0 then error "Event not found"',
            'set targetEvent to item 1 of matches',
            'end tell',
        ]

        if 'summary' in update_data:
            summary = applescript_escape(sanitize_text(update_data['summary'], MAX_SUMMARY_LENGTH))
            lines.extend([
                'tell application "Calendar"',
                f'set summary of targetEvent to "{summary}"',
                'end tell',
            ])
        if 'description' in update_data:
            description = applescript_escape(sanitize_text(update_data['description'], MAX_DESCRIPTION_LENGTH))
            lines.extend([
                'tell application "Calendar"',
                f'set description of targetEvent to "{description}"',
                'end tell',
            ])
        if 'location' in update_data:
            location = applescript_escape(sanitize_text(update_data['location'], MAX_LOCATION_LENGTH))
            lines.extend([
                'tell application "Calendar"',
                f'set location of targetEvent to "{location}"',
                'end tell',
            ])
        if 'dtstart' in update_data:
            dtstart = update_data['dtstart']
            if isinstance(dtstart, str):
                dtstart = datetime.fromisoformat(dtstart)
            if not isinstance(dtstart, datetime):
                print("❌ Invalid dtstart")
                return False
            lines.extend(datetime_to_applescript("newStartDate", dtstart))
            lines.extend([
                'tell application "Calendar"',
                'set start date of targetEvent to newStartDate',
                'end tell',
            ])
        if 'dtend' in update_data:
            dtend = update_data['dtend']
            if isinstance(dtend, str):
                dtend = datetime.fromisoformat(dtend)
            if not isinstance(dtend, datetime):
                print("❌ Invalid dtend")
                return False
            lines.extend(datetime_to_applescript("newEndDate", dtend))
            lines.extend([
                'tell application "Calendar"',
                'set end date of targetEvent to newEndDate',
                'end tell',
            ])

        lines.append('return "ok"')
        output = self._run_applescript(lines)
        if output is None:
            return False

        print("✅ Event updated successfully")
        return True


class CalendarManager:
    """Manage iCloud Calendar via CalDAV"""
    
    def __init__(
        self,
        config_path: Optional[str] = None,
        user_agent: Optional[str] = None,
        debug_http: bool = False,
        credential_source: str = "auto"
    ):
        if not CALDAV_AVAILABLE:
            raise RuntimeError(
                f"CalDAV provider is unavailable: {CALDAV_IMPORT_ERROR}. "
                "Install dependencies from requirements.txt or use --provider macos-native."
            )

        self.config_path = resolve_config_path(config_path)
        self.debug_http = debug_http or is_truthy_env(os.getenv("ICALENDAR_SYNC_DEBUG_HTTP", "0"))
        self.user_agent = (
            user_agent
            or os.getenv("ICALENDAR_SYNC_USER_AGENT")
            or DEFAULT_USER_AGENT
        ).strip()
        if credential_source not in ("auto", "keyring", "env", "file"):
            logger.warning(f"Unknown credential source '{credential_source}', using auto")
            credential_source = "auto"
        self.credential_source = credential_source
        self.base_url = os.getenv("ICALENDAR_SYNC_CALDAV_URL", "https://caldav.icloud.com").strip()
        self._config_credentials = safe_load_config_credentials(str(self.config_path))
        self._last_http_debug: Dict[str, str] = {}
        self.username = self._resolve_username()
        self.password = self._load_password()
        self.client: Optional[DAVClient] = None
        self._connected: bool = False
        self._connection_time: Optional[datetime] = None
        self._cache_timeout: int = 300  # 5 minutes
        self._connection_lock = threading.Lock()
        self._rate_limiter = RateLimiter(RATE_LIMIT_CALLS, RATE_LIMIT_WINDOW)

    def _resolve_username(self) -> Optional[str]:
        """Resolve username based on selected credential source."""
        if self.credential_source == "env":
            return os.getenv("ICLOUD_USERNAME")
        if self.credential_source == "file":
            return self._config_credentials.get("username")
        return os.getenv("ICLOUD_USERNAME") or self._config_credentials.get("username")

    def _build_request_headers(self, target_url: str) -> Dict[str, str]:
        """Build request headers to mimic native macOS Calendar client."""
        parsed = urlparse(target_url)
        host = parsed.netloc or "caldav.icloud.com"
        return {
            "User-Agent": self.user_agent,
            "Host": host,
            "Origin": "https://www.icloud.com",
            "Accept": "*/*",
            "Connection": "keep-alive",
        }

    def _capture_response_debug(self, response) -> None:
        """Capture response diagnostics for debug output."""
        debug_data = {
            "status": str(getattr(response, "status_code", "")),
            "reason": str(getattr(response, "reason", "")),
            "url": str(getattr(response, "url", "")),
        }
        headers = getattr(response, "headers", {})
        for key in ("x-apple-request-id", "x-apple-session-token", "www-authenticate", "location"):
            value = headers.get(key) or headers.get(key.title())
            if value:
                debug_data[key] = str(value)

        if self.debug_http:
            body = sanitize_text(getattr(response, "text", "") or "", 2000)
            if body:
                debug_data["body"] = body

        self._last_http_debug = debug_data

    def _debug_string_from_last_response(self) -> str:
        """Format stored response diagnostics."""
        if not self._last_http_debug:
            return ""
        order = ["status", "reason", "url", "x-apple-request-id", "x-apple-session-token", "www-authenticate", "location", "body"]
        parts = []
        for key in order:
            value = self._last_http_debug.get(key)
            if value:
                parts.append(f"{key}={value}")
        return ", ".join(parts)

    def _resolve_caldav_endpoint(self) -> str:
        """Resolve potential iCloud redirect chain (caldav.icloud.com -> pXX-caldav.icloud.com)."""
        current_url = self.base_url
        if not self.username or not self.password:
            return current_url

        max_redirects = 5
        timeout = 15
        session = requests.Session()
        auth_header = "Basic " + base64.b64encode(
            f"{self.username}:{self.password}".encode("utf-8")
        ).decode("ascii")

        for _ in range(max_redirects):
            headers = self._build_request_headers(current_url)
            headers["Authorization"] = auth_header

            try:
                response = session.get(
                    current_url,
                    headers=headers,
                    allow_redirects=False,
                    timeout=timeout,
                )
                self._capture_response_debug(response)
            except requests.exceptions.RequestException as e:
                if self.debug_http:
                    logger.debug(f"Endpoint resolution failed: {self._format_exception_details(e)}")
                break

            if response.status_code in (301, 302, 307, 308):
                location = response.headers.get("Location")
                if not location:
                    break
                next_url = urljoin(current_url, location)
                next_host = (urlparse(next_url).hostname or "").lower()
                if next_host and next_host.endswith("icloud.com"):
                    current_url = next_url
                    continue
                break

            break

        return current_url
    
    def _format_exception_details(self, exc: Exception) -> str:
        """Build a compact diagnostic string for network/auth failures."""
        details = [f"type={type(exc).__name__}"]

        for attr in ("status", "reason", "url"):
            value = getattr(exc, attr, None)
            if value:
                details.append(f"{attr}={value}")

        response = getattr(exc, "response", None)
        if response is not None:
            status_code = getattr(response, "status_code", None)
            if status_code:
                details.append(f"http_status={status_code}")
            headers = getattr(response, "headers", {})
            for key in ("x-apple-request-id", "x-apple-session-token"):
                value = headers.get(key) or headers.get(key.title())
                if value:
                    details.append(f"{key}={value}")
            if self.debug_http:
                response_text = getattr(response, "text", "")
                if response_text:
                    details.append(f"response={sanitize_text(response_text, 300)}")

        if self.debug_http and getattr(exc, "args", None):
            details.append(f"args={sanitize_text(str(exc.args), 300)}")

        return ", ".join(details)

    def _load_password(self) -> Optional[str]:
        """Load password from keyring, env, or secure config file."""
        username = self.username
        if self.credential_source in ("auto", "keyring") and username and KEYRING_AVAILABLE:
            try:
                # Try keyring first
                password = keyring.get_password('openclaw-icalendar', username)
                if password:
                    logger.debug("Loaded password from keyring")
                    return password
            except KeyringError:
                pass
        elif self.credential_source == "keyring" and not KEYRING_AVAILABLE:
            logger.error(f"Keyring requested but unavailable: {KEYRING_IMPORT_ERROR}")
            return None

        if self.credential_source in ("auto", "env"):
            env_password = os.getenv('ICLOUD_APP_PASSWORD')
            if env_password:
                if validate_secret_value(env_password):
                    return env_password
                logger.error("Environment password contains invalid control characters")

        if self.credential_source in ("auto", "file"):
            config_password = self._config_credentials.get("password")
            config_username = self._config_credentials.get("username")
            if config_password and validate_secret_value(config_password):
                if not username or not config_username or config_username == username:
                    if not self.username and config_username:
                        self.username = config_username
                    return config_password

        return None
    
    def _is_connection_valid(self) -> bool:
        """Check if cached connection is still valid (thread-safe)"""
        with self._connection_lock:
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
        
        # Rate limiting
        self._rate_limiter.wait_if_needed()
        
        try:
            with self._connection_lock:
                if self.debug_http:
                    logger.setLevel(logging.DEBUG)
                    logger.debug("CalDAV debug enabled")

                resolved_url = self._resolve_caldav_endpoint()
                headers = self._build_request_headers(resolved_url)
                if self.debug_http:
                    logger.debug(
                        "CalDAV headers prepared: "
                        f"Host={headers.get('Host')} Origin={headers.get('Origin')} "
                        f"User-Agent={headers.get('User-Agent')}"
                    )

                client_kwargs = dict(
                    url=resolved_url,
                    username=self.username,
                    password=self.password,
                    ssl_verify_cert=True  # Enforce SSL verification
                )
                client_kwargs["headers"] = headers

                try:
                    self.client = DAVClient(**client_kwargs)
                except TypeError:
                    # Older caldav versions may not support custom headers.
                    client_kwargs.pop("headers", None)
                    self.client = DAVClient(**client_kwargs)
                    if hasattr(self.client, "session") and hasattr(self.client.session, "headers"):
                        self.client.session.headers.update(headers)

                principal = self.client.principal()
                principal.calendars()
                
                self._connected = True
                self._connection_time = datetime.now(timezone.utc)
                logger.info("Successfully connected to iCloud CalDAV")
                return True
            
        except AuthorizationError as e:
            print("❌ Authentication failed: invalid credentials or blocked iCloud request")
            if self.debug_http and self._debug_string_from_last_response():
                print(f"   Apple response: {self._debug_string_from_last_response()}")
            if self.debug_http:
                print(f"   Debug: {self._format_exception_details(e)}")
            logger.error(f"Authentication failed ({self._format_exception_details(e)})")
            self._connected = False
            return False
        except requests.exceptions.SSLError as e:
            print("❌ TLS/SSL handshake error")
            if self.debug_http and self._debug_string_from_last_response():
                print(f"   Apple response: {self._debug_string_from_last_response()}")
            if self.debug_http:
                print(f"   Debug: {self._format_exception_details(e)}")
            logger.error(f"TLS handshake error ({self._format_exception_details(e)})")
            self._connected = False
            raise
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
            print("❌ Network error")
            if self.debug_http and self._debug_string_from_last_response():
                print(f"   Apple response: {self._debug_string_from_last_response()}")
            if self.debug_http:
                print(f"   Debug: {self._format_exception_details(e)}")
            logger.error(f"Network error ({self._format_exception_details(e)})")
            self._connected = False
            raise  # Re-raise for retry decorator
        except DAVError as e:
            print("❌ CalDAV error")
            if self.debug_http and self._debug_string_from_last_response():
                print(f"   Apple response: {self._debug_string_from_last_response()}")
            if self.debug_http:
                print(f"   Debug: {self._format_exception_details(e)}")
            logger.error(f"CalDAV error ({self._format_exception_details(e)})")
            self._connected = False
            raise  # Re-raise for retry decorator
        except Exception as e:
            print(f"❌ Unexpected error: {type(e).__name__}")
            if self.debug_http and self._debug_string_from_last_response():
                print(f"   Apple response: {self._debug_string_from_last_response()}")
            if self.debug_http:
                print(f"   Debug: {self._format_exception_details(e)}")
            logger.error(f"Unexpected connection error: {self._format_exception_details(e)}")
            self._connected = False
            return False
    
    def list_calendars(self) -> List[str]:
        """List all calendars"""
        if not self.connect():
            return []
        
        self._rate_limiter.wait_if_needed()
        
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
            
        except NotFoundError:
            print("❌ Calendars not found")
            logger.error("Calendars not found")
            return []
        except DAVError:
            print("❌ CalDAV error")
            logger.error("Error listing calendars")
            return []
        except Exception as e:
            print("❌ Error listing calendars")
            logger.error(f"Unexpected error listing calendars: {type(e).__name__}")
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
                            
                            # Convert date to datetime properly
                            if not isinstance(evt_start_dt, datetime):
                                # Use start of day in user's timezone
                                evt_start_dt = datetime.combine(
                                    evt_start_dt, 
                                    dt_time.min
                                ).replace(tzinfo=start.tzinfo or timezone.utc)
                            
                            if not isinstance(evt_end_dt, datetime):
                                # Use end of day in user's timezone
                                evt_end_dt = datetime.combine(
                                    evt_end_dt, 
                                    dt_time.max
                                ).replace(tzinfo=end.tzinfo or timezone.utc)
                            
                            # Ensure timezone awareness
                            if evt_start_dt.tzinfo is None:
                                evt_start_dt = evt_start_dt.replace(tzinfo=timezone.utc)
                            if evt_end_dt.tzinfo is None:
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
            logger.warning(f"Could not check conflicts: {type(e).__name__}")
            return []
    
    def get_events(self, calendar_name: str, days_ahead: int = 7) -> List:
        """Get calendar events"""
        # Validate calendar name
        if not validate_calendar_name(calendar_name):
            print("❌ Invalid calendar name")
            logger.error(f"Invalid calendar name provided")
            return []
        
        # Validate days_ahead
        if not (MIN_DAYS_AHEAD <= days_ahead <= MAX_DAYS_AHEAD):
            print(f"❌ days_ahead must be between {MIN_DAYS_AHEAD} and {MAX_DAYS_AHEAD}")
            return []
        
        if not self.connect():
            return []
        
        self._rate_limiter.wait_if_needed()
        
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
            
        except NotFoundError:
            print(f"❌ Calendar '{calendar_name}' not found")
            logger.error("Calendar not found")
            return []
        except DAVError:
            print("❌ CalDAV error")
            logger.error("Error getting events")
            return []
        except Exception as e:
            print("❌ Error getting events")
            logger.error(f"Unexpected error getting events: {type(e).__name__}")
            return []
    
    def create_event(
        self, 
        calendar_name: str, 
        event_data: Dict,
        check_conflicts: bool = True,
        auto_confirm: bool = False
    ) -> bool:
        """Create new event with validation and conflict detection"""
        # Validate calendar name
        if not validate_calendar_name(calendar_name):
            print("❌ Invalid calendar name")
            logger.error("Invalid calendar name provided")
            return False
        
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
        
        # Sanitize text fields
        summary = sanitize_text(event_data['summary'], MAX_SUMMARY_LENGTH)
        event_data['summary'] = summary
        
        if 'description' in event_data:
            event_data['description'] = sanitize_text(
                event_data['description'], 
                MAX_DESCRIPTION_LENGTH
            )
        
        if 'location' in event_data:
            event_data['location'] = sanitize_text(
                event_data['location'], 
                MAX_LOCATION_LENGTH
            )
        
        self._rate_limiter.wait_if_needed()
        
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
                    
                    if not auto_confirm:
                        response = timed_input("Continue anyway? (y/n): ")
                        if response is None or response.lower() != 'y':
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
            event.add('summary', summary)
            event.add('dtstart', dtstart)
            event.add('dtend', dtend)
            
            # Optional fields
            if 'location' in event_data:
                event.add('location', event_data['location'])
            if 'description' in event_data:
                event.add('description', event_data['description'])
            if 'status' in event_data:
                event.add('status', event_data['status'])
            if 'priority' in event_data and isinstance(event_data['priority'], int):
                event.add('priority', max(0, min(9, event_data['priority'])))
            
            # Add alarms if specified
            if 'alarms' in event_data and isinstance(event_data['alarms'], list):
                for alarm_data in event_data['alarms']:
                    if isinstance(alarm_data, dict):
                        alarm = Alarm()
                        alarm.add('action', 'DISPLAY')
                        minutes = alarm_data.get('minutes', 15)
                        alarm.add('trigger', timedelta(minutes=-abs(minutes)))
                        alarm.add('description', alarm_data.get('description', 'Reminder'))
                        event.add_component(alarm)
            
            # Add recurring rules if specified
            if 'rrule' in event_data and isinstance(event_data['rrule'], dict):
                rrule_data = event_data['rrule']
                rrule_dict = {'FREQ': [rrule_data.get('freq', 'WEEKLY')]}
                
                if 'count' in rrule_data and isinstance(rrule_data['count'], int):
                    rrule_dict['COUNT'] = [max(1, rrule_data['count'])]
                if 'interval' in rrule_data and isinstance(rrule_data['interval'], int):
                    rrule_dict['INTERVAL'] = [max(1, rrule_data['interval'])]
                if 'byday' in rrule_data:
                    rrule_dict['BYDAY'] = rrule_data['byday']
                if 'until' in rrule_data:
                    rrule_dict['UNTIL'] = [rrule_data['until']]
                
                event.add('rrule', rrule_dict)
            
            cal.add_component(event)
            
            # Save event
            calendar.save_event(cal.to_ical().decode('utf-8'))
            
            print(f"✅ Event '{summary}' created successfully")
            logger.info(f"Created event in {calendar_name}")
            return True
            
        except NotFoundError:
            print(f"❌ Calendar '{calendar_name}' not found")
            logger.error("Calendar not found")
            return False
        except DAVError:
            print("❌ CalDAV error")
            logger.error("Error creating event")
            return False
        except Exception as e:
            print("❌ Error creating event")
            logger.error(f"Unexpected error creating event: {type(e).__name__}")
            return False
    
    def delete_event(self, calendar_name: str, event_uid: str) -> bool:
        """Delete event"""
        # Validate calendar name
        if not validate_calendar_name(calendar_name):
            print("❌ Invalid calendar name")
            logger.error("Invalid calendar name provided")
            return False
        
        if not event_uid or not isinstance(event_uid, str):
            print("❌ Valid event UID required")
            return False
        
        # Sanitize UID
        event_uid = event_uid.strip()
        if len(event_uid) > 500:
            print("❌ Invalid event UID (too long)")
            return False
        
        if not self.connect():
            return False
        
        self._rate_limiter.wait_if_needed()
        
        try:
            principal = self.client.principal()
            calendar = principal.calendar(name=calendar_name)
            
            event = calendar.event_by_uid(event_uid)
            event.delete()
            
            print("🗑️  Event deleted successfully")
            logger.info(f"Deleted event from {calendar_name}")
            return True
            
        except NotFoundError:
            print("❌ Event or calendar not found")
            logger.error("Event/calendar not found")
            return False
        except DAVError:
            print("❌ CalDAV error")
            logger.error("Error deleting event")
            return False
        except Exception as e:
            print("❌ Error deleting event")
            logger.error(f"Unexpected error deleting event: {type(e).__name__}")
            return False

    def update_event(
        self,
        calendar_name: str,
        event_uid: str,
        update_data: Dict,
        recurrence_id: Optional[str] = None,
        mode: str = 'single'
    ) -> bool:
        """
        Update existing event with smart recurrence handling

        Args:
            calendar_name: Name of calendar
            event_uid: UID of event to update
            update_data: Dictionary with fields to update
            recurrence_id: ISO datetime of specific instance (for recurring events)
            mode: Update mode - 'single', 'all', or 'future'

        Returns:
            True if successful, False otherwise
        """
        # Validate inputs
        if not validate_calendar_name(calendar_name):
            print("❌ Invalid calendar name")
            logger.error("Invalid calendar name provided")
            return False

        if not event_uid or not isinstance(event_uid, str):
            print("❌ Valid event UID required")
            return False

        event_uid = event_uid.strip()
        if len(event_uid) > 500:
            print("❌ Invalid event UID (too long)")
            return False

        if mode not in ['single', 'all', 'future']:
            print("❌ Invalid mode. Must be 'single', 'all', or 'future'")
            return False

        if not self.connect():
            return False

        self._rate_limiter.wait_if_needed()

        try:
            principal = self.client.principal()
            calendar = principal.calendar(name=calendar_name)

            # Fetch existing event
            event_obj = calendar.event_by_uid(event_uid)
            ical_data = event_obj.data

            # Parse iCalendar data
            cal = iCal.from_ical(ical_data)
            event = None
            for component in cal.walk():
                if component.name == 'VEVENT':
                    event = component
                    break

            if event is None:
                print("❌ Could not parse event data")
                return False

            # Check if event has RRULE (is recurring)
            has_rrule = 'RRULE' in event

            # Handle recurrence based on mode
            if has_rrule and mode == 'single' and recurrence_id:
                # Create exception for single instance
                print(f"📅 Creating exception for instance: {recurrence_id}")
                return self._update_single_instance(
                    calendar, event_uid, recurrence_id, update_data, cal, event
                )

            elif has_rrule and mode == 'future' and recurrence_id:
                # Split series: update current and future
                print(f"🔮 Updating this and future instances from: {recurrence_id}")
                return self._update_future_instances(
                    calendar, event_uid, recurrence_id, update_data, cal, event
                )

            elif has_rrule and mode == 'all':
                # Update master recurrence rule
                print("🔁 Updating entire recurrence series")
                return self._update_all_instances(
                    calendar, event_obj, update_data, cal, event
                )

            else:
                # Simple update (non-recurring or mode='all' on non-recurring)
                print("✏️  Updating event")
                return self._update_simple(
                    calendar, event_obj, update_data, cal, event
                )

        except NotFoundError:
            print("❌ Event or calendar not found")
            logger.error("Event/calendar not found")
            return False
        except DAVError:
            print("❌ CalDAV error")
            logger.error("Error updating event")
            return False
        except Exception as e:
            print("❌ Error updating event")
            logger.error(f"Unexpected error updating event: {type(e).__name__}: {str(e)}")
            return False

    def _update_simple(self, calendar, event_obj, update_data: Dict, cal, event) -> bool:
        """Update a simple (non-recurring) event or all instances of recurring event"""
        # Apply updates to event
        self._apply_updates_to_event(event, update_data)
        if not self._validate_event_time_range(event):
            return False

        # Save back to server
        event_obj.data = cal.to_ical()
        event_obj.save()

        print("✅ Event updated successfully")
        logger.info("Event updated")
        return True

    def _update_all_instances(self, calendar, event_obj, update_data: Dict, cal, event) -> bool:
        """Update the master recurrence rule (affects all instances)"""
        # Apply updates to master event
        self._apply_updates_to_event(event, update_data)
        if not self._validate_event_time_range(event):
            return False

        # Save back to server
        event_obj.data = cal.to_ical()
        event_obj.save()

        print("✅ All instances updated successfully")
        logger.info("All recurrence instances updated")
        return True

    def _update_single_instance(
        self, calendar, event_uid: str, recurrence_id: str,
        update_data: Dict, cal, master_event
    ) -> bool:
        """Create an exception for a single instance of a recurring event"""
        try:
            # Parse recurrence_id datetime
            recurrence_dt = datetime.fromisoformat(recurrence_id)
            if recurrence_dt.tzinfo is None:
                recurrence_dt = recurrence_dt.replace(tzinfo=timezone.utc)

            # Create exception event (copy of master with RECURRENCE-ID)
            exception_event = iEvent()

            # Copy essential fields from master
            exception_event.add('uid', master_event['UID'])
            exception_event.add('dtstamp', datetime.now(timezone.utc))
            exception_event.add('recurrence-id', recurrence_dt)

            # Copy existing fields that aren't being updated
            for key in ['SUMMARY', 'LOCATION', 'DESCRIPTION', 'STATUS', 'PRIORITY']:
                if key in master_event and key.lower() not in update_data:
                    exception_event.add(key.lower(), master_event[key])

            # Apply updates
            self._apply_updates_to_event(exception_event, update_data)

            # Set dtstart/dtend if not in update_data
            if 'dtstart' not in update_data:
                exception_event.add('dtstart', recurrence_dt)
            if 'dtend' not in update_data:
                # Calculate duration from master event
                master_start = master_event['DTSTART'].dt
                master_end = master_event['DTEND'].dt
                duration = master_end - master_start
                exception_event.add('dtend', recurrence_dt + duration)

            if not self._validate_event_time_range(exception_event):
                return False

            # Create new calendar with exception
            exception_cal = iCal()
            exception_cal.add('prodid', '-//iCalendar Sync//EN')
            exception_cal.add('version', '2.0')
            exception_cal.add_component(exception_event)

            # Save exception event to server
            calendar.save_event(exception_cal.to_ical().decode('utf-8'))

            print(f"✅ Exception created for instance: {recurrence_id}")
            logger.info(f"Created exception for recurrence instance")
            return True

        except ValueError as e:
            print(f"❌ Invalid recurrence_id format: {e}")
            return False

    def _update_future_instances(
        self, calendar, event_uid: str, recurrence_id: str,
        update_data: Dict, cal, master_event
    ) -> bool:
        """Split series: end original series before recurrence_id, create new series from recurrence_id"""
        try:
            # Parse recurrence_id datetime
            split_dt = datetime.fromisoformat(recurrence_id)
            if split_dt.tzinfo is None:
                split_dt = split_dt.replace(tzinfo=timezone.utc)

            # Update master event RRULE to end before split point
            if 'RRULE' in master_event:
                rrule = master_event['RRULE']
                # Set UNTIL to day before split
                rrule['UNTIL'] = [split_dt - timedelta(days=1)]
                master_event['RRULE'] = rrule

            # Save modified master
            event_obj = calendar.event_by_uid(event_uid)
            event_obj.data = cal.to_ical()
            event_obj.save()

            # Create new series starting from split point
            new_cal = iCal()
            new_cal.add('prodid', '-//iCalendar Sync//EN')
            new_cal.add('version', '2.0')

            new_event = iEvent()
            import uuid
            new_event.add('uid', str(uuid.uuid4()))
            new_event.add('dtstamp', datetime.now(timezone.utc))

            # Copy and update fields from master
            for key in ['SUMMARY', 'LOCATION', 'DESCRIPTION', 'STATUS', 'PRIORITY', 'RRULE']:
                if key in master_event and key.lower() not in update_data:
                    new_event.add(key.lower(), master_event[key])

            # Set new start time
            new_event.add('dtstart', split_dt)

            # Calculate end time
            master_start = master_event['DTSTART'].dt
            master_end = master_event['DTEND'].dt
            duration = master_end - master_start
            new_event.add('dtend', split_dt + duration)

            # Apply updates
            self._apply_updates_to_event(new_event, update_data)
            if not self._validate_event_time_range(new_event):
                return False

            new_cal.add_component(new_event)
            calendar.save_event(new_cal.to_ical().decode('utf-8'))

            print(f"✅ Series split at {recurrence_id}. New series created with updates.")
            logger.info("Split recurrence series and created new series")
            return True

        except ValueError as e:
            print(f"❌ Invalid recurrence_id format: {e}")
            return False

    def _apply_updates_to_event(self, event, update_data: Dict):
        """Apply update_data fields to an event component"""
        # Update text fields with sanitization
        if 'summary' in update_data:
            event['SUMMARY'] = sanitize_text(update_data['summary'], MAX_SUMMARY_LENGTH)

        if 'description' in update_data:
            event['DESCRIPTION'] = sanitize_text(
                update_data['description'], MAX_DESCRIPTION_LENGTH
            )

        if 'location' in update_data:
            event['LOCATION'] = sanitize_text(update_data['location'], MAX_LOCATION_LENGTH)

        # Update datetime fields
        if 'dtstart' in update_data:
            dtstart = update_data['dtstart']
            if isinstance(dtstart, str):
                dtstart = datetime.fromisoformat(dtstart)
            if dtstart.tzinfo is None:
                dtstart = dtstart.replace(tzinfo=timezone.utc)
            event['DTSTART'] = dtstart

        if 'dtend' in update_data:
            dtend = update_data['dtend']
            if isinstance(dtend, str):
                dtend = datetime.fromisoformat(dtend)
            if dtend.tzinfo is None:
                dtend = dtend.replace(tzinfo=timezone.utc)
            event['DTEND'] = dtend

        # Update other fields
        if 'status' in update_data:
            event['STATUS'] = update_data['status']

        if 'priority' in update_data and isinstance(update_data['priority'], int):
            event['PRIORITY'] = max(0, min(9, update_data['priority']))

    def _validate_event_time_range(self, event) -> bool:
        """Validate DTSTART/DTEND range after updates."""
        if 'DTSTART' not in event or 'DTEND' not in event:
            return True

        start_value = event['DTSTART']
        end_value = event['DTEND']
        start_dt = getattr(start_value, 'dt', start_value)
        end_dt = getattr(end_value, 'dt', end_value)

        if not isinstance(start_dt, datetime) or not isinstance(end_dt, datetime):
            return True

        if end_dt <= start_dt:
            print("❌ Event end time must be after start time")
            logger.error("Invalid update: dtend must be after dtstart")
            return False

        return True


def cmd_setup(args):
    """Interactive or headless setup of credentials"""
    print("\n🔧 iCalendar Sync Setup\n")

    non_interactive = getattr(args, 'non_interactive', False)
    username_arg = getattr(args, 'username', None)
    storage = getattr(args, "storage", "keyring")
    config_path_arg = getattr(args, "config", None)

    if non_interactive:
        email = (username_arg or os.getenv('ICLOUD_USERNAME') or "").strip()
        password = (os.getenv('ICLOUD_APP_PASSWORD') or "").strip()

        if not email:
            print("❌ ICLOUD_USERNAME is required in non-interactive mode")
            logger.error("Setup: Missing ICLOUD_USERNAME in non-interactive mode")
            return
        if not password:
            print("❌ ICLOUD_APP_PASSWORD is required in non-interactive mode")
            logger.error("Setup: Missing ICLOUD_APP_PASSWORD in non-interactive mode")
            return
        if not validate_secret_value(password):
            print("❌ Invalid ICLOUD_APP_PASSWORD value")
            logger.error("Setup: Invalid ICLOUD_APP_PASSWORD value")
            return
    else:
        # Interactive mode
        print("To use iCalendar Sync, you need to configure your iCloud credentials.")
        print("⚠️  Use an App-Specific Password, NOT your regular Apple ID password.\n")
        print("Get it from: https://appleid.apple.com -> Sign-In & Security -> App-Specific Passwords\n")

        if username_arg:
            email = username_arg.strip()
            print(f"📧 Using provided email: {email}")
        else:
            email = input("📧 iCloud Email: ").strip()

        if not email:
            print("❌ Email cannot be empty")
            return

        # Validate email
        if not validate_email(email):
            print("❌ Invalid email format")
            response = timed_input("Continue anyway? (y/n): ")
            if response is None or response.lower() != 'y':
                print("Setup cancelled")
                return

        password = getpass.getpass("🔑 App-Specific Password (xxxx-xxxx-xxxx-xxxx): ").strip()
        if not password:
            print("❌ Password cannot be empty")
            return
        if not validate_secret_value(password):
            print("❌ Invalid password value")
            logger.error("Setup: Invalid password value")
            return

        # Validate format
        if not all(c.isalnum() or c == '-' for c in password):
            print("⚠️  Password format looks unusual")
            response = timed_input("Are you sure this is correct? (y/n): ")
            if response is None or response.lower() != 'y':
                print("Setup cancelled")
                return
    
    # Validate email format before proceeding
    if not validate_email(email):
        logger.error("Setup: Invalid email format")
        print("❌ Invalid email format")
        return

    if storage == "file":
        saved_path = save_config_credentials(config_path_arg, email, password)
        if saved_path is None:
            print("❌ Failed to save credentials to config file")
            return
        print(f"\n✅ Credentials saved to config file: {saved_path}")
        print("   File permissions set to 0600")
        logger.info(f"Credentials stored in config file: {saved_path}")
    else:
        if not KEYRING_AVAILABLE:
            print("❌ Keyring backend is not available in this runtime.")
            print(f"   Reason: {KEYRING_IMPORT_ERROR}")
            suggested_path = resolve_config_path(config_path_arg)
            print(f"   Use file storage instead: icalendar-sync setup --storage file --config {suggested_path}")
            return
        # Try to store in keyring first
        try:
            keyring.set_password('openclaw-icalendar', email, password)
            print("\n✅ Credentials saved securely to system keyring")
            logger.info("Credentials stored in keyring")
        except KeyringError:
            logger.error("Setup: Could not access system keyring")
            suggested_path = resolve_config_path(config_path_arg)
            print("❌ Could not access system keyring. Credentials were not persisted.")
            print(f"   Use file storage instead: icalendar-sync setup --storage file --config {suggested_path}")
            return
    
    print("🚀 You can now use iCalendar Sync!\n")


def build_manager(args):
    """Create CalendarManager from common CLI args."""
    provider = (getattr(args, "provider", None) or os.getenv("ICALENDAR_SYNC_PROVIDER", "auto")).strip()
    if provider not in ("auto", "caldav", "macos-native"):
        logger.warning(f"Unknown provider '{provider}', falling back to auto")
        provider = "auto"

    if provider == "auto":
        if sys.platform == "darwin":
            return MacOSNativeCalendarManager()
        provider = "caldav"

    if provider == "macos-native":
        return MacOSNativeCalendarManager()

    raw_storage = getattr(args, "storage", None)
    credential_source = (raw_storage or os.getenv("ICALENDAR_SYNC_STORAGE", "auto")).strip()
    explicit_config = bool(getattr(args, "config", None))
    # If config path is provided explicitly and storage wasn't explicitly set,
    # prefer file credentials to avoid accidental stale env/keyring usage.
    if explicit_config and raw_storage is None and credential_source == "auto":
        credential_source = "file"

    return CalendarManager(
        config_path=getattr(args, "config", None),
        user_agent=getattr(args, "user_agent", None),
        debug_http=getattr(args, "debug_http", False),
        credential_source=credential_source,
    )


def run_with_fallback(args, operation_name: str, *operation_args, **operation_kwargs):
    """Run provider operation with automatic macOS native fallback on CalDAV auth/connect failure."""
    provider_pref = (getattr(args, "provider", None) or os.getenv("ICALENDAR_SYNC_PROVIDER", "auto")).strip()
    if provider_pref not in ("auto", "caldav", "macos-native"):
        provider_pref = "auto"

    try:
        manager = build_manager(args)
    except RuntimeError as e:
        if sys.platform == "darwin" and provider_pref in ("auto", "caldav"):
            print("⚠️  CalDAV provider unavailable, switching to macOS native provider")
            logger.warning(f"CalDAV unavailable, fallback to macOS native: {e}")
            manager = MacOSNativeCalendarManager()
        else:
            print(f"❌ {e}")
            logger.error(str(e))
            return None

    operation = getattr(manager, operation_name)
    result = operation(*operation_args, **operation_kwargs)

    should_fallback = (
        sys.platform == "darwin"
        and provider_pref in ("auto", "caldav")
        and isinstance(manager, CalendarManager)
        and (result is False or result is None or result == [])
        and not manager._connected
    )
    if should_fallback:
        print("⚠️  CalDAV authentication/connect failed, switching to macOS native provider")
        logger.warning("Fallback from CalDAV to macOS native provider")
        native_manager = MacOSNativeCalendarManager()
        native_operation = getattr(native_manager, operation_name)
        return native_operation(*operation_args, **operation_kwargs)

    return result


def cmd_list(args):
    """List calendars"""
    run_with_fallback(args, "list_calendars")


def cmd_get_events(args):
    """Get events from calendar"""
    if not args.calendar:
        print("❌ Calendar name required")
        return
    
    run_with_fallback(args, "get_events", args.calendar, args.days_ahead)


def cmd_create_event(args):
    """Create event"""
    if not args.calendar or not args.json:
        print("❌ Calendar and JSON data required")
        return
    
    try:
        # Parse JSON
        if os.path.isfile(args.json):
            content = safe_file_read(args.json, MAX_JSON_FILE_SIZE)
            if content is None:
                print("❌ Could not read JSON file")
                return
            event_data = json.loads(content)
        else:
            # Limit inline JSON size too
            if len(args.json) > MAX_JSON_FILE_SIZE:
                print("❌ JSON data too large")
                return
            event_data = json.loads(args.json)
        
        # Convert string dates to datetime
        if 'dtstart' in event_data and isinstance(event_data['dtstart'], str):
            event_data['dtstart'] = datetime.fromisoformat(event_data['dtstart'])
        if 'dtend' in event_data and isinstance(event_data['dtend'], str):
            event_data['dtend'] = datetime.fromisoformat(event_data['dtend'])
        
        check_conflicts = not args.no_conflict_check if hasattr(args, 'no_conflict_check') else True
        auto_confirm = getattr(args, 'yes', False)
        run_with_fallback(
            args,
            "create_event",
            args.calendar,
            event_data,
            check_conflicts=check_conflicts,
            auto_confirm=auto_confirm,
        )
        
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

    run_with_fallback(args, "delete_event", args.calendar, args.uid)


def cmd_update_event(args):
    """Update event with smart recurrence handling"""
    if not args.calendar or not args.uid or not args.json:
        print("❌ Calendar, event UID, and JSON data required")
        return

    try:
        # Parse JSON
        if os.path.isfile(args.json):
            content = safe_file_read(args.json, MAX_JSON_FILE_SIZE)
            if content is None:
                print("❌ Could not read JSON file")
                return
            update_data = json.loads(content)
        else:
            # Limit inline JSON size
            if len(args.json) > MAX_JSON_FILE_SIZE:
                print("❌ JSON data too large")
                return
            update_data = json.loads(args.json)

        # Convert string dates to datetime if present
        if 'dtstart' in update_data and isinstance(update_data['dtstart'], str):
            update_data['dtstart'] = datetime.fromisoformat(update_data['dtstart'])
        if 'dtend' in update_data and isinstance(update_data['dtend'], str):
            update_data['dtend'] = datetime.fromisoformat(update_data['dtend'])

        # Determine mode and recurrence_id
        mode = getattr(args, 'mode', 'single')
        recurrence_id = getattr(args, 'recurrence_id', None)

        run_with_fallback(
            args,
            "update_event",
            args.calendar,
            args.uid,
            update_data,
            recurrence_id=recurrence_id,
            mode=mode
        )

    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON: {e}")
        return
    except ValueError as e:
        print(f"❌ Invalid datetime format: {e}")
        return


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
  icalendar-sync update --calendar "Work" --uid "event-id" --json '{"summary":"Updated Meeting"}'
  icalendar-sync update --calendar "Work" --uid "event-id" --json data.json --recurrence-id "2026-02-20T10:00:00" --mode single
  icalendar-sync delete --calendar "Work" --uid "event-id"
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Setup
    setup_parser = subparsers.add_parser('setup', help='Configure iCloud credentials')
    setup_parser.add_argument('--username', help='Apple ID email (optional in non-interactive mode)')
    setup_parser.add_argument('--non-interactive', action='store_true',
                             help='Non-interactive mode (reads ICLOUD_USERNAME and ICLOUD_APP_PASSWORD)')
    setup_parser.add_argument('--storage', choices=['keyring', 'file'], default='keyring',
                             help='Credential storage backend (default: keyring)')
    setup_parser.add_argument('--config',
                             help='Path to YAML config with credentials (used for --storage file and runtime lookup)')
    setup_parser.add_argument('--debug-http', action='store_true',
                             help='Show detailed auth/network diagnostics')
    setup_parser.add_argument('--user-agent',
                             help=f'Override CalDAV User-Agent (default: {DEFAULT_USER_AGENT})')
    setup_parser.set_defaults(func=cmd_setup)
    
    # List
    list_parser = subparsers.add_parser('list', help='List calendars')
    list_parser.add_argument('--provider', choices=['auto', 'caldav', 'macos-native'], default='auto',
                            help='Calendar provider backend')
    list_parser.add_argument('--storage', choices=['auto', 'keyring', 'env', 'file'], default=None,
                            help='Credential source for CalDAV provider (default: auto)')
    list_parser.add_argument('--config', help='Path to YAML config with credentials')
    list_parser.add_argument('--debug-http', action='store_true',
                            help='Show detailed auth/network diagnostics')
    list_parser.add_argument('--user-agent',
                            help=f'Override CalDAV User-Agent (default: {DEFAULT_USER_AGENT})')
    list_parser.set_defaults(func=cmd_list)
    
    # Get events
    get_parser = subparsers.add_parser('get', help='Get calendar events')
    get_parser.add_argument('--calendar', help='Calendar name')
    get_parser.add_argument('--days', type=int, default=7, dest='days_ahead',
                           help=f'Days ahead to retrieve (default: 7, max: {MAX_DAYS_AHEAD})')
    get_parser.add_argument('--provider', choices=['auto', 'caldav', 'macos-native'], default='auto',
                           help='Calendar provider backend')
    get_parser.add_argument('--storage', choices=['auto', 'keyring', 'env', 'file'], default=None,
                           help='Credential source for CalDAV provider (default: auto)')
    get_parser.add_argument('--config', help='Path to YAML config with credentials')
    get_parser.add_argument('--debug-http', action='store_true',
                           help='Show detailed auth/network diagnostics')
    get_parser.add_argument('--user-agent',
                           help=f'Override CalDAV User-Agent (default: {DEFAULT_USER_AGENT})')
    get_parser.set_defaults(func=cmd_get_events)
    
    # Create event
    create_parser = subparsers.add_parser('create', help='Create calendar event')
    create_parser.add_argument('--calendar', required=True, help='Calendar name')
    create_parser.add_argument('--json', required=True, 
                              help='JSON with event data (file path or JSON string)')
    create_parser.add_argument('--no-conflict-check', action='store_true',
                              help='Skip conflict detection')
    create_parser.add_argument('-y', '--yes', action='store_true',
                              help='Auto-confirm without prompts')
    create_parser.add_argument('--provider', choices=['auto', 'caldav', 'macos-native'], default='auto',
                              help='Calendar provider backend')
    create_parser.add_argument('--storage', choices=['auto', 'keyring', 'env', 'file'], default=None,
                              help='Credential source for CalDAV provider (default: auto)')
    create_parser.add_argument('--config', help='Path to YAML config with credentials')
    create_parser.add_argument('--debug-http', action='store_true',
                              help='Show detailed auth/network diagnostics')
    create_parser.add_argument('--user-agent',
                              help=f'Override CalDAV User-Agent (default: {DEFAULT_USER_AGENT})')
    create_parser.set_defaults(func=cmd_create_event)
    
    # Update event
    update_parser = subparsers.add_parser('update', help='Update calendar event')
    update_parser.add_argument('--calendar', required=True, help='Calendar name')
    update_parser.add_argument('--uid', required=True, help='Event UID')
    update_parser.add_argument('--json', required=True,
                              help='JSON with update data (file path or JSON string)')
    update_parser.add_argument('--recurrence-id',
                              help='ISO datetime of specific instance (for recurring events)')
    update_parser.add_argument('--mode', default='single',
                              choices=['single', 'all', 'future'],
                              help='Update mode: single instance, all instances, or this and future (default: single)')
    update_parser.add_argument('--provider', choices=['auto', 'caldav', 'macos-native'], default='auto',
                              help='Calendar provider backend')
    update_parser.add_argument('--storage', choices=['auto', 'keyring', 'env', 'file'], default=None,
                              help='Credential source for CalDAV provider (default: auto)')
    update_parser.add_argument('--config', help='Path to YAML config with credentials')
    update_parser.add_argument('--debug-http', action='store_true',
                              help='Show detailed auth/network diagnostics')
    update_parser.add_argument('--user-agent',
                              help=f'Override CalDAV User-Agent (default: {DEFAULT_USER_AGENT})')
    update_parser.set_defaults(func=cmd_update_event)

    # Delete event
    delete_parser = subparsers.add_parser('delete', help='Delete calendar event')
    delete_parser.add_argument('--calendar', required=True, help='Calendar name')
    delete_parser.add_argument('--uid', required=True, help='Event UID')
    delete_parser.add_argument('--provider', choices=['auto', 'caldav', 'macos-native'], default='auto',
                              help='Calendar provider backend')
    delete_parser.add_argument('--storage', choices=['auto', 'keyring', 'env', 'file'], default=None,
                              help='Credential source for CalDAV provider (default: auto)')
    delete_parser.add_argument('--config', help='Path to YAML config with credentials')
    delete_parser.add_argument('--debug-http', action='store_true',
                              help='Show detailed auth/network diagnostics')
    delete_parser.add_argument('--user-agent',
                              help=f'Override CalDAV User-Agent (default: {DEFAULT_USER_AGENT})')
    delete_parser.set_defaults(func=cmd_delete_event)

    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(0)
    
    args.func(args)


if __name__ == '__main__':
    main()
