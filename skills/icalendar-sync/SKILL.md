# iCalendar Sync for OpenClaw

**Professional iCloud Calendar integration via CalDAV protocol**

Version: 2.2.2 | Author: Black_Temple | License: MIT

---

## ⚠️ IMPORTANT: What This Skill Actually Provides

This skill provides **core iCloud calendar sync functionality**. Please review what is included vs. what is mentioned in extended documentation:

### ✅ Included in v2.2.2:

- **CalDAV Integration** - Bidirectional sync with iCloud calendars (calendar.py)
- **Event Operations** - Create, read, update, delete calendar events
- **Recurring Events** - Full RRULE support (daily, weekly, monthly, yearly)
- **Alarms & Reminders** - Multiple alarms per event
- **Internationalization** - 20 languages (i18n.py)
- **Timezone Support** - Proper datetime handling
- **Basic Security** - Input validation, rate limiting, SSL enforcement

### ❌ NOT in Current Release:

The following features are mentioned in DOCUMENTATION.md but are **not separate modules** in this release. Some logic may be embedded in calendar.py:

- ❌ Standalone `calendar_vault.py` module
- ❌ Standalone `privacy_engine.py` module  
- ❌ Standalone `rate_limiter.py` module
- ❌ Advanced multi-agent isolation system
- ❌ Separate iCloud connector module

**These are planned for future releases or are simplified/embedded in the main calendar.py module.**

---

## 🔒 Security Notice

### Credential Storage

**This skill REQUIRES sensitive credentials:**

1. `ICLOUD_USERNAME` - Your Apple ID email (required)
2. `ICLOUD_APP_PASSWORD` - App-Specific Password from https://appleid.apple.com (required)

**Storage Methods:**

✅ **Preferred: System Keyring**
- macOS: Keychain
- Windows: Credential Manager
- Linux: Secret Service (GNOME Keyring/KWallet)
- Credentials stored securely by OS

⚠️ **Fallback: Plaintext .env File**
- Location: `~/.openclaw/.env`
- Permissions: 0600 (user-only read/write)
- **Risk**: Credentials stored in plaintext on disk
- **Use only**: Development/testing environments

**Recommendation:** Always ensure system keyring is available before use. The .env fallback should NOT be used in production.

### What We Validate:

- ✅ Calendar names (alphanumeric, spaces, hyphens, underscores only)
- ✅ Text field lengths (summary: 500 chars, description: 5000 chars)
- ✅ Date ranges (max 365 days to prevent DoS)
- ✅ JSON file sizes (max 1MB)
- ✅ SSL certificate verification (enforced)
- ✅ Credential filtering in logs

### Rate Limiting:

- 10 API calls per 60 seconds
- Prevents API abuse and iCloud throttling
- Automatic retry with backoff

---

## Overview

iCalendar Sync provides seamless integration between OpenClaw and iCloud Calendar using the industry-standard CalDAV protocol. Built on the reliable caldav Python library with comprehensive error handling and internationalization.

### Key Features

- ✅ **Full Calendar Sync** - Bidirectional sync with iCloud via CalDAV
- 🗓️ **Event Management** - Create, read, update, delete events
- 🔁 **Recurring Events** - RRULE support (DAILY, WEEKLY, MONTHLY, YEARLY)
- ⏰ **Alarms & Reminders** - Multiple alarms per event
- 📱 **Multi-Device** - Instant sync across iPhone, iPad, Mac
- 🌐 **Multi-Language** - 20 languages (3.5B+ speakers)
- 🔐 **Secure Storage** - Keyring-first credential management
- ⚡ **Input Validation** - Protection against common attacks

### Architecture

```
src/icalendar_sync/
├── calendar.py              # Core CalDAV client (33 KB)
│                            # • Event CRUD operations
│                            # • Credential management
│                            # • Input validation
│                            # • Rate limiting
│                            # • CLI interface
│
├── i18n.py                  # Internationalization (40 KB)
│                            # • 20 language translations
│                            # • Message formatting
│
├── translations_extended.py # Extended translations
└── translations_extended2.py# Additional translations
```

**Note:** All core functionality is in `calendar.py`. There are no separate vault, privacy, or connector modules in this release.

---

## Quick Start

### Prerequisites

1. **Python 3.9+**
2. **iCloud Account** with 2FA enabled
3. **App-Specific Password** from https://appleid.apple.com

### Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Run setup wizard (stores credentials in keyring)
python -m icalendar_sync.calendar setup
```

### Generate App-Specific Password

1. Go to https://appleid.apple.com
2. Sign in → **Security** section
3. **App-Specific Passwords** → **Generate Password**
4. Label: `OpenClaw Calendar Sync`
5. **Copy** password (format: `xxxx-xxxx-xxxx-xxxx`)

⚠️ **Password shown only once!** Save it securely.

### First Event

```bash
# List calendars
python -m icalendar_sync.calendar list

# Create event
python -m icalendar_sync.calendar create --calendar "Personal" --json '{
  "summary": "Test Event",
  "dtstart": "2026-02-12T14:00:00+03:00",
  "dtend": "2026-02-12T15:00:00+03:00"
}'
```

---

## Usage

### List Calendars

```bash
python -m icalendar_sync.calendar list
```

**Output:**
```
📅 Available Calendars (3):

  • Personal
  • Work
  • Family
```

### Get Events

```bash
# Next 7 days (default)
python -m icalendar_sync.calendar get --calendar "Work"

# Next 30 days
python -m icalendar_sync.calendar get --calendar "Personal" --days 30
```

### Create Event

#### Simple Event

```bash
python -m icalendar_sync.calendar create --calendar "Work" --json '{
  "summary": "Team Meeting",
  "dtstart": "2026-02-10T14:00:00+03:00",
  "dtend": "2026-02-10T15:00:00+03:00",
  "description": "Q1 Planning Discussion",
  "location": "Conference Room A"
}'
```

#### Recurring Event

```bash
python -m icalendar_sync.calendar create --calendar "Work" --json '{
  "summary": "Weekly Standup",
  "dtstart": "2026-02-10T09:00:00+03:00",
  "dtend": "2026-02-10T09:30:00+03:00",
  "rrule": {
    "freq": "WEEKLY",
    "interval": 1,
    "byday": ["MO", "WE", "FR"],
    "count": 50
  }
}'
```

#### With Alarms

```bash
python -m icalendar_sync.calendar create --calendar "Personal" --json '{
  "summary": "Doctor Appointment",
  "dtstart": "2026-02-15T10:00:00+03:00",
  "dtend": "2026-02-15T11:00:00+03:00",
  "alarms": [
    {"minutes": 60, "description": "1 hour before"},
    {"minutes": 15, "description": "15 minutes before"}
  ]
}'
```

### Delete Event

```bash
# Get event UID from list
python -m icalendar_sync.calendar get --calendar "Work"

# Delete by UID
python -m icalendar_sync.calendar delete --calendar "Work" --uid "event-uid-here"
```

---

## Python API

```python
from icalendar_sync.calendar import CalendarManager
from datetime import datetime, timezone

# Initialize
manager = CalendarManager()

# List calendars
calendars = manager.list_calendars()
print(f"Found {len(calendars)} calendars")

# Get events
events = manager.get_events("Work", days_ahead=7)

# Create event
event_data = {
    "summary": "Project Deadline",
    "dtstart": datetime(2026, 2, 20, 17, 0, tzinfo=timezone.utc),
    "dtend": datetime(2026, 2, 20, 18, 0, tzinfo=timezone.utc),
    "description": "Final project submission",
    "location": "Online",
    "alarms": [
        {"minutes": 1440, "description": "1 day before"},
        {"minutes": 60, "description": "1 hour before"}
    ]
}

success = manager.create_event(
    calendar_name="Work",
    event_data=event_data,
    check_conflicts=True,  # Basic time overlap check
    auto_confirm=False
)

if success:
    print("✅ Event created successfully")
```

---

## Configuration

### Environment Variables

```bash
# Required
export ICLOUD_USERNAME="user@icloud.com"
export ICLOUD_APP_PASSWORD="xxxx-xxxx-xxxx-xxxx"

# Optional
export DEFAULT_CALENDAR="Personal"
export LOG_LEVEL="INFO"  # DEBUG, INFO, WARNING, ERROR
```

### Setup Methods

**Method 1: Setup Wizard (Recommended)**
```bash
python -m icalendar_sync.calendar setup
# Stores credentials in system keyring automatically
```

**Method 2: Environment Variables**
```bash
export ICLOUD_USERNAME="user@icloud.com"
export ICLOUD_APP_PASSWORD="xxxx-xxxx-xxxx-xxxx"
```

**Method 3: .env File (Development Only)**
```bash
# Create ~/.openclaw/.env
ICLOUD_USERNAME=user@icloud.com
ICLOUD_APP_PASSWORD=xxxx-xxxx-xxxx-xxxx
```

⚠️ **Security Warning**: Method 3 stores credentials in plaintext. Use ONLY for development.

---

## Event Schema

### Required Fields

- `summary` (string): Event title (max 500 chars)
- `dtstart` (ISO 8601): Start datetime with timezone
- `dtend` (ISO 8601): End datetime with timezone

### Optional Fields

- `description` (string): Event details (max 5000 chars)
- `location` (string): Event location (max 500 chars)
- `status` (string): CONFIRMED, TENTATIVE, CANCELLED
- `priority` (int): 0-9 (0=undefined, 1=highest, 9=lowest)
- `attendees` (array): List of attendee emails
- `alarms` (array): List of alarm objects
- `rrule` (object): Recurrence rule

### Datetime Format

ISO 8601 with timezone:
```
2026-02-10T14:00:00+03:00  # Moscow time (MSK)
2026-02-10T11:00:00Z       # UTC
2026-02-10T06:00:00-05:00  # US Eastern (EST)
```

### Recurrence Rule (RRULE)

```json
{
  "freq": "WEEKLY",           // DAILY, WEEKLY, MONTHLY, YEARLY
  "interval": 1,              // Every N periods
  "count": 10,                // Number of occurrences (optional)
  "until": "2026-12-31",      // End date (optional)
  "byday": ["MO", "WE", "FR"] // Days of week (optional)
}
```

---

## Troubleshooting

### Authentication Failed

**Error**: `Authentication failed: Invalid credentials`

**Solutions**:
1. Verify Apple ID email is correct
2. Generate new App-Specific Password at https://appleid.apple.com
3. Run setup: `python -m icalendar_sync.calendar setup`
4. Check 2FA is enabled on iCloud account

### Calendar Not Found

**Error**: `Calendar 'Work' not found`

**Solutions**:
1. List calendars: `python -m icalendar_sync.calendar list`
2. Calendar names are case-insensitive in v2.2.2
3. Ensure calendar exists in iCloud web interface

### Rate Limit Exceeded

**Error**: `Rate limit exceeded, waiting...`

**Solution**: Automatic retry after 60 seconds. To avoid:
- Reduce API call frequency
- Batch operations when possible
- Current limit: 10 calls/60 seconds

### SSL Certificate Error

**Error**: `SSL certificate verify failed`

**Solutions**:
1. Update certificates: `pip install --upgrade certifi`
2. Check system date/time is correct
3. Verify network isn't intercepting SSL

### Keyring Not Available

**Warning**: `Could not access system keyring, falling back to .env file`

**Solution**: Install keyring backend:
```bash
# Linux
sudo apt-get install gnome-keyring  # or kwallet

# macOS/Windows: Built-in, no action needed
```

---

## Supported Languages

20 languages covering 3.5B+ native speakers:

🇬🇧 English • 🇪🇸 Spanish • 🇫🇷 French • 🇩🇪 German • 🇮🇹 Italian • 🇷🇺 Russian • 🇨🇳 Chinese (Simplified) • 🇹🇼 Chinese (Traditional) • 🇯🇵 Japanese • 🇰🇷 Korean • 🇵🇹 Portuguese • 🇧🇷 Portuguese (Brazil) • 🇵🇱 Polish • 🇹🇷 Turkish • 🇮🇳 Hindi • 🇳🇱 Dutch • 🇸🇦 Arabic • 🇸🇪 Swedish • 🇳🇴 Norwegian • 🇩🇰 Danish

---

## Limitations

- **Rate Limit**: 10 API calls per 60 seconds
- **Date Range**: Maximum 365 days per query (DoS protection)
- **File Size**: JSON files max 1MB
- **Text Fields**: Summary (500 chars), Description (5000 chars), Location (500 chars)
- **Conflict Detection**: Basic time overlap check only (no complex scheduling logic)
- **Multi-Agent**: Not implemented in current release

---

## Security Best Practices

1. ✅ **Use system keyring** - Never use .env in production
2. ✅ **Enable 2FA** on your iCloud account
3. ✅ **Rotate App-Specific Passwords** every 90 days
4. ✅ **One password per app** - Don't reuse passwords
5. ✅ **Monitor access** - Check iCloud security settings regularly
6. ✅ **Keep updated**: `pip install -U caldav icalendar keyring`
7. ✅ **Run audits**: `pip-audit` to check for vulnerabilities
8. ✅ **Review logs** - Check for suspicious activity

---

## Performance

### Benchmarks (Python 3.11, v2.2.2)

| Operation | Average Time | Notes |
|-----------|--------------|-------|
| List calendars | ~500ms | Cached 5 min |
| Get events (7 days) | ~800ms | ~50 events |
| Create event | ~1.2s | With validation |
| Delete event | ~600ms | |

### Optimization Tips

- Connection caching enabled by default (5 min)
- Limit `--days` parameter to reduce API calls
- Cache calendar list locally if needed frequently

---

## Changelog

### v2.2.2 (2026-02-11)

**Documentation:**
- 📝 Added comprehensive CRITICAL NOTICE in README.md
- 📝 Clarified which modules exist vs. documented
- 📝 Added disclaimers about future features in DOCUMENTATION.md
- 📝 Addressed ClawHub security scan concerns

**Version (from v2.2.1):**
- 🔢 Bumped version to 2.2.2 across all files
- 🔧 Synchronized setup.py, skill.yaml, pyproject.toml, __init__.py
- 📝 Updated all version references

**Fixes (from v2.2.0):**
- 🔧 Fixed setup.py version mismatch
- 🔧 Fixed skill.yaml metadata (env vars now marked required)
- 🔧 Updated SKILL.md to reflect actual capabilities
- 🔧 Added security disclaimers about credential storage
- 🔧 Removed references to non-existent modules

**Previous (2026-02-10):**
- ✨ Case-insensitive calendar lookup
- ✨ DoS protection (365 days, 1000 events max)
- ✨ Full timezone support
- 🔒 Security hardening (injection, path traversal, CVE fixes)
- 📚 Complete documentation

---

## Support & Documentation

- **This File**: Basic usage and security info
- **README.md**: Project overview and quick start
- **DOCUMENTATION.md**: Extended guide (some features not yet implemented)
- **SECURITY.md**: Security policy and reporting
- **GitHub Issues**: https://github.com/h8kxrfp68z-lgtm/OpenClaw/issues
- **Email**: contact@clawhub.ai

---

## License

MIT License

Copyright (c) 2026 Black_Temple

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

---

**Made with ❤️ for OpenClaw Multi-Agent Framework**

Version: 2.2.2 | Last Updated: February 11, 2026 | Status: Production Ready
