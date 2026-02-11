# iCalendar Sync for OpenClaw

**Professional iCloud Calendar integration with enterprise-grade security**

Version: 2.2.0 | Author: Black_Temple | License: MIT

---

## Overview

iCalendar Sync provides seamless integration between OpenClaw agents and iCloud Calendar using the industry-standard CalDAV protocol. Built with security-first principles, featuring Zero Trust architecture, multi-agent isolation, and comprehensive input validation.

### Key Features

- ✅ **Full Calendar Sync** - Bidirectional sync with iCloud
- 🗓️ **Event Management** - Create, read, update, delete events
- 🔁 **Recurring Events** - Full RRULE support (daily, weekly, monthly, yearly)
- ⏰ **Alarms & Reminders** - Multiple alarms per event
- 📱 **Multi-Device** - Instant sync across iPhone, iPad, Mac
- ⚡ **Conflict Detection** - Automatic scheduling conflict warnings
- 🔒 **Enterprise Security** - 95/100 security score
- 🌐 **Multi-Language** - 20 languages supported

---

## Security Features

### Zero Trust Architecture

- 🔑 **Secure Credentials** - OS keyring integration (macOS Keychain, Windows Credential Manager, Linux Secret Service)
- 🛡️ **Input Validation** - All inputs sanitized and validated
- 🚫 **Rate Limiting** - DoS protection (10 calls/60 seconds)
- 🔐 **SSL Verification** - Enforced certificate validation
- 🧹 **Log Filtering** - Automatic credential redaction
- 🧵 **Thread Safety** - Safe concurrent access
- ⏱️ **Timeout Protection** - 30s timeout on inputs
- 📝 **Path Validation** - Protection against path traversal

**Security Score: 95/100** (Enterprise Grade)

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

# Run setup wizard
python -m icalendar_sync.calendar setup
```

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
from icalendar_sync import CalendarManager
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
    check_conflicts=True,
    auto_confirm=False
)

if success:
    print("✅ Event created successfully")
```

---

## Configuration

### Environment Variables

```bash
# Required (or use keyring)
export ICLOUD_USERNAME="user@icloud.com"
export ICLOUD_APP_PASSWORD="xxxx-xxxx-xxxx-xxxx"

# Optional
export DEFAULT_CALENDAR="Personal"
export LOG_LEVEL="INFO"  # DEBUG, INFO, WARNING, ERROR
```

### Generate App-Specific Password

1. Go to https://appleid.apple.com
2. Sign in → **Security** section
3. **App-Specific Passwords** → **Generate Password**
4. Label: `OpenClaw Calendar Sync`
5. Copy password (format: `xxxx-xxxx-xxxx-xxxx`)

⚠️ **Important**: Password shown only once! Save it securely.

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
2026-02-10T14:00:00+03:00  # Moscow time
2026-02-10T11:00:00Z       # UTC
2026-02-10T06:00:00-05:00  # EST
```

### Recurrence Rule

```json
{
  "freq": "WEEKLY",        // DAILY, WEEKLY, MONTHLY, YEARLY
  "interval": 1,           // Every N periods
  "count": 10,             // Number of occurrences
  "until": "2026-12-31",   // End date
  "byday": ["MO", "WE", "FR"]  // Days of week
}
```

---

## Multi-Agent Support

Create `vault_config.yaml` for agent isolation:

```yaml
agents:
  - id: assistant
    calendars: [personal, work]
    can_create_events: true
    can_edit_events: true
    can_delete_events: true
  
  - id: scheduler
    calendars: [work]
    can_create_events: true
    can_edit_events: false
    can_delete_events: false
  
  - id: readonly_viewer
    calendars: [personal, work, family]
    can_create_events: false
    can_edit_events: false
    can_delete_events: false

calendars:
  - name: personal
    icloud_name: Personal
    privacy_level: private
  
  - name: work
    icloud_name: Work Calendar
    privacy_level: shared
  
  - name: family
    icloud_name: Family
    privacy_level: shared
```

**Privacy Levels:**
- `public` - All agents see full details
- `shared` - Authorized agents see full details
- `private` - Owner only, others see "Busy"
- `masked` - All agents see "Busy" blocks

---

## Advanced Features

### Conflict Detection

```python
from icalendar_sync.calendar_vault import ConflictResolver

resolver = ConflictResolver(timezone="Europe/Moscow")

# Find conflicts
conflicts = resolver.find_conflicts(
    events=existing_events,
    start_date=start,
    end_date=end
)

if conflicts:
    print(f"Found {len(conflicts)} conflicts")
    for conflict in conflicts:
        print(f"  - {conflict.severity}: {len(conflict.events)} events")
```

### Find Free Slots

```python
# Find 1-hour slots in next 7 days
free_slots = resolver.find_free_slots(
    events=events,
    start_date=start,
    end_date=end,
    duration_minutes=60,
    only_working_hours=True
)

for slot in free_slots:
    print(f"Free: {slot.start} - {slot.end}")
```

---

## Troubleshooting

### Authentication Failed

**Error**: `Authentication failed: Invalid credentials`

**Solution**:
1. Verify Apple ID email is correct
2. Generate new App-Specific Password at https://appleid.apple.com
3. Run setup again: `python -m icalendar_sync.calendar setup`

### Calendar Not Found

**Error**: `Calendar 'Work' not found`

**Solution**:
1. List calendars: `python -m icalendar_sync.calendar list`
2. Use exact name (case-insensitive in v2.2.0)
3. Ensure calendar exists in iCloud

### Rate Limit Exceeded

**Error**: `Rate limit exceeded, waiting...`

**Solution**: Automatic retry after 60 seconds. To avoid:
- Reduce API call frequency
- Batch operations
- Current limit: 10 calls/60s

### SSL Certificate Error

**Error**: `SSL certificate verify failed`

**Solution**:
1. Update certificates: `pip install --upgrade certifi`
2. Check system date/time
3. Verify network SSL settings

---

## Security Best Practices

1. **Always use keyring** for credential storage (not .env files)
2. **Enable 2FA** on your iCloud account
3. **Rotate App-Specific Passwords** every 90 days
4. **Use separate passwords** for each application
5. **Monitor access logs** regularly
6. **Review agent permissions** in vault_config.yaml
7. **Keep dependencies updated**: `pip install -U caldav icalendar`
8. **Run security audits**: `bandit -r src/`

---

## Performance

### Benchmarks (v2.2.0)

| Operation | Time | Notes |
|-----------|------|-------|
| List calendars | ~500ms | Cached for 5 min |
| Get events (7 days) | ~800ms | ~50 events |
| Create event | ~1.2s | With conflict check |
| Delete event | ~600ms | |
| Find free slots | ~1.5s | 7 days, 100 events |

### Optimization Tips

- Enable connection caching (default: 5 min)
- Use batch operations when possible
- Limit `days_ahead` parameter
- Cache calendar list locally

---

## Supported Languages

20 languages with 3.5B+ native speakers:

🇬🇧 English • 🇪🇸 Spanish • 🇫🇷 French • 🇩🇪 German • 🇮🇹 Italian • 🇷🇺 Russian • 🇨🇳 Chinese (Simplified) • 🇹🇼 Chinese (Traditional) • 🇯🇵 Japanese • 🇰🇷 Korean • 🇵🇹 Portuguese • 🇧🇷 Portuguese (Brazil) • 🇵🇱 Polish • 🇹🇷 Turkish • 🇮🇳 Hindi • 🇳🇱 Dutch • 🇸🇦 Arabic • 🇸🇪 Swedish • 🇳🇴 Norwegian • 🇩🇰 Danish

---

## Limitations

- **Rate Limit**: 10 API calls per 60 seconds
- **Date Range**: Maximum 365 days
- **Event Limit**: 1000 events per query (DoS protection)
- **File Size**: JSON files max 1MB
- **Text Fields**: Summary (500 chars), Description (5000 chars), Location (500 chars)

---

## Changelog

### v2.2.0 (2026-02-10)

**New Features:**
- ✨ Case-insensitive calendar lookup
- ✨ DoS protection (365 days, 1000 events)
- ✨ Full timezone support with zoneinfo
- ✨ Conflict deduplication with __hash__/__eq__

**Security:**
- 🔒 Fixed command injection in install.sh
- 🔒 Path traversal protection in calendar_vault
- 🔒 Updated requests to 2.32.0+ (CVE-2023-32681)
- 🔒 Config validation
- 🔒 Deep copy in privacy_engine

**Documentation:**
- 📚 Complete 20-section documentation
- 📚 Architecture diagrams
- 📚 Security audit (95/100)
- 📚 Multilingual support guide

---

## Support

- **Documentation**: [DOCUMENTATION.md](DOCUMENTATION.md)
- **Security Policy**: [SECURITY.md](SECURITY.md)
- **Issues**: [GitHub Issues](https://github.com/h8kxrfp68z-lgtm/OpenClaw/issues)
- **Email**: contact@clawhub.ai

---

## License

MIT License - Copyright (c) 2026 Black_Temple

See LICENSE file for full text.

---

**Made with ❤️ for OpenClaw Multi-Agent Framework**

Version: 2.2.0 | Last Updated: February 11, 2026
