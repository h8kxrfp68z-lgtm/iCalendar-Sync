# 📅 iCalendar Sync for OpenClaw

**Professional iCloud Calendar integration with enterprise-grade security**

[![Version](https://img.shields.io/badge/version-2.2.12-blue.svg)](https://github.com/h8kxrfp68z-lgtm/OpenClaw/releases)
[![Security Rating](https://img.shields.io/badge/security-A-brightgreen.svg)](SECURITY.md)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Cyrillic Support](https://img.shields.io/badge/cyrillic-✓-green.svg)](CHANGELOG.md)

---

## 🎉 New in v2.2.12 (Feb 12, 2026)

- **📋 Enhanced Registry Metadata**: Added clawhub.json and REGISTRY.yaml for maximum ClawHub compatibility
- **🔍 Multiple Metadata Formats**: Now 6 different metadata files to ensure ClawHub recognition
- **✅ Explicit Environment Declarations**: Required env vars declared in all possible formats

## Previous: v2.2.11 (Feb 12, 2026)

- **🌍 Cyrillic Support**: Fixed calendar name validation to support Unicode (Cyrillic, Chinese, Arabic, etc.)
- **🔧 Headless Configuration**: Added `--username`, `--password`, `--non-interactive` flags for automated setup
- **✅ RuntimeWarning Fixed**: Suppressed module import warnings when using `python -m icalendar_sync`
- **🙏 Field-Tested**: All fixes validated by real OpenClaw users (thanks Alfred!)

[See BUGFIX_NOTES.md for details](BUGFIX_NOTES.md)

[See full CHANGELOG](CHANGELOG.md) | [Security Scan Response](SECURITY_SCAN_NOTICE.md)

---

## ⚠️ CRITICAL NOTICE: What This Version Actually Includes

**Version 2.2.12 is the ENHANCED METADATA RELEASE** with Cyrillic support and headless configuration. Some documentation files (DOCUMENTATION.md, ARCHITECTURE.md) describe **planned future features** that are not yet implemented.

**IMPORTANT: See SECURITY_SCAN_NOTICE.md for detailed responses to ClawHub security scan concerns.**

### ✅ ACTUALLY IMPLEMENTED IN v2.2.12:

**Fully functional modules:**
- `src/icalendar_sync/calendar.py` (33 KB) - Complete CalDAV client
  - Event CRUD operations (create, read, update, delete)
  - Credential management (keyring + .env fallback)
  - Input validation and security checks
  - Rate limiting (10 calls/60s)
  - Recurring events (RRULE support)
  - Multi-calendar support
  - Cyrillic/Unicode calendar names
  - CLI interface with headless mode

- `src/icalendar_sync/__main__.py` - Module entry point
- `src/icalendar_sync/i18n.py` (40 KB) - Internationalization for 20 languages
- `src/icalendar_sync/translations_extended.py` - Extended translations
- `src/icalendar_sync/translations_extended2.py` - Additional translations

### ❌ NOT IMPLEMENTED (Mentioned in Extended Docs Only):

**These modules do NOT exist as separate files in v2.2.6:**
- ❌ `calendar_vault.py` - Described in ARCHITECTURE.md but not implemented
- ❌ `privacy_engine.py` - Mentioned in DOCUMENTATION.md but not a separate module
- ❌ `rate_limiter.py` - Rate limiting is embedded in calendar.py, not standalone
- ❌ `connector/` directory - No separate connector modules
- ❌ Advanced multi-agent isolation system

**Why the documentation mismatch?**
- DOCUMENTATION.md and ARCHITECTURE.md were written for a future v3.0 architecture
- v2.2.6 consolidates all logic into `calendar.py` for simplicity
- Some "modules" exist as functions/classes within calendar.py, not separate files
- Extended docs are kept for reference/planning but describe future state

**What to trust:**
- ✅ **THIS README** - Accurate for v2.2.6
- ✅ **SKILL.md** - Accurate for v2.2.6  
- ✅ **skill.yaml** - Correct metadata
- ✅ **CLAWHUB_METADATA.yaml** - Explicit credential declarations (NEW v2.2.6)
- ✅ **SECURITY_SCAN_NOTICE.md** - Addresses all ClawHub concerns (NEW v2.2.6)
- ✅ **CHANGELOG.md** - Complete version history
- ⚠️ **DOCUMENTATION.md** - Mix of current + future features (read with caution)
- ⚠️ **ARCHITECTURE.md** - Describes future v3.0 architecture

### 🔒 CREDENTIALS REQUIRED:

**Explicitly declared in registry metadata (v2.2.6 fix):**
- `ICLOUD_USERNAME` - Your Apple ID (e.g., user@icloud.com)
- `ICLOUD_APP_PASSWORD` - App-Specific Password from [https://appleid.apple.com](https://appleid.apple.com)

**Declared in:**
- skill.yaml (required: true)
- CLAWHUB_METADATA.yaml (explicit declarations with security notes)
- SECURITY_SCAN_NOTICE.md (detailed explanation)

**Storage options:**
1. ✅ **Preferred**: System keyring (macOS Keychain, Windows Credential Manager, Linux Secret Service)
2. ⚠️ **Fallback**: `~/.openclaw/.env` file (chmod 0600) - plaintext, use ONLY for development

The .env fallback is **explicitly documented and intentional** for development environments where keyring backends may not be available.

---

## ✨ Features

### 💪 Core Capabilities

- ✅ **Full Calendar Sync** - Bidirectional sync with iCloud
- 🌐 **CalDAV Protocol** - Standard-compliant implementation
- 🗓️ **Event Management** - Create, read, update, delete events
- 🔁 **Recurring Events** - Full RRULE support (daily, weekly, monthly, yearly)
- ⏰ **Alarms & Reminders** - Multiple alarms per event
- 📱 **Multi-Device** - Instant sync across iPhone, iPad, Mac
- 📂 **Multiple Calendars** - Work, Personal, Custom calendars
- 🌍 **Unicode Support** - Cyrillic, CJK, and all international scripts
- ⚡ **Conflict Detection** - Automatic scheduling conflict warnings

### 🔒 Security Features (v2.2.6)

- 🔑 **Keyring Integration** - Secure credential storage in OS keychain
- 🛡️ **Input Validation** - Protection against injection attacks (Unicode-aware)
- 🚫 **Rate Limiting** - DoS protection (10 calls/60s)
- 🔐 **SSL Verification** - Enforced certificate validation
- 🧹 **Log Filtering** - Automatic credential redaction
- 🧵 **Thread Safety** - Safe concurrent access
- 📝 **Atomic Operations** - Safe file writes
- ⏱️ **Timeout Protection** - 30s timeout on interactive inputs
- ⚠️ **CLI Credential Warnings** - Documented risks of command-line password exposure
- 🐳 **Docker Secrets Support** - Secure deployment patterns

---

## 🚀 Quick Start

### Installation

```bash
# From source
git clone https://github.com/h8kxrfp68z-lgtm/OpenClaw.git
cd OpenClaw/icalendar-sync
pip install -e .

# Or via pip (when published)
pip install openclaw-icalendar-sync
Setup
Interactive Setup (Default)
bash
# Interactive setup wizard
icalendar-sync setup
You'll need:

Apple ID email (e.g., user@icloud.com)

App-Specific Password from https://appleid.apple.com

Go to: Sign-In & Security → App-Specific Passwords

Create new password for "OpenClaw iCalendar Sync"

Headless Setup (Automated)
bash
# For automation, Docker, CI/CD, OpenClaw agents
icalendar-sync setup \
  --username "user@icloud.com" \
  --password "xxxx-xxxx-xxxx-xxxx" \
  --non-interactive
⚠️ SECURITY WARNING: Avoid passing passwords on CLI on multi-user systems. Use environment variables or secrets manager instead.

Credentials are stored securely in:

macOS: Keychain

Windows: Credential Manager

Linux: Secret Service (GNOME Keyring/KWallet)

Fallback: ~/.openclaw/.env (chmod 0600, plaintext, development only)

📖 Usage
List Calendars
bash
icalendar-sync list
Output:

text
📅 Available Calendars (5):

  -  Personal
  -  Work
  -  Family
  -  Личный      # Cyrillic support!
  -  Работа      # Russian calendar names
Get Events
bash
# Next 7 days (default)
icalendar-sync get --calendar "Work"

# Cyrillic calendar names
icalendar-sync get --calendar "Личный" --days 7
icalendar-sync get --calendar "Работа" --days 30

# English calendars still work
icalendar-sync get --calendar "Personal" --days 30
Create Event
Simple Event
bash
icalendar-sync create --calendar "Work" --json '{
  "summary": "Team Meeting",
  "dtstart": "2026-02-12T14:00:00+03:00",
  "dtend": "2026-02-12T15:00:00+03:00",
  "description": "Q1 Planning Discussion",
  "location": "Conference Room A"
}'
Cyrillic Event
bash
icalendar-sync create --calendar "Личный" --json '{
  "summary": "Встреча с врачом",
  "dtstart": "2026-02-15T10:00:00+03:00",
  "dtend": "2026-02-15T11:00:00+03:00",
  "description": "Ежегодный осмотр",
  "location": "Поликлиника №5"
}'
From JSON File
bash
# Create event.json
cat > event.json << EOF
{
  "summary": "Doctor Appointment",
  "dtstart": "2026-02-15T10:00:00+03:00",
  "dtend": "2026-02-15T11:00:00+03:00",
  "description": "Annual checkup",
  "alarms": [
    {"minutes": 60, "description": "1 hour before"},
    {"minutes": 15, "description": "15 minutes before"}
  ]
}
EOF

icalendar-sync create --calendar "Personal" --json event.json
Recurring Event
bash
icalendar-sync create --calendar "Work" --json '{
  "summary": "Weekly Standup",
  "dtstart": "2026-02-12T09:00:00+03:00",
  "dtend": "2026-02-12T09:30:00+03:00",
  "rrule": {
    "freq": "WEEKLY",
    "interval": 1,
    "byday": ["MO", "WE", "FR"],
    "count": 50
  }
}'
Delete Event
bash
# First, get the event UID
icalendar-sync get --calendar "Work"

# Then delete
icalendar-sync delete --calendar "Личный" --uid "event-uid-here"
Module Execution
bash
# All commands now work as Python module
python -m icalendar_sync list
python -m icalendar_sync setup
python -m icalendar_sync get --calendar "Личный" --days 7
python -m icalendar_sync create --calendar "Work" --json event.json
📚 API Usage (Python)
python
from icalendar_sync import CalendarManager
from datetime import datetime, timezone

# Initialize
manager = CalendarManager()

# List calendars (including Cyrillic names)
calendars = manager.list_calendars()
print(f"Found {len(calendars)} calendars")

# Get events from Russian calendar
events = manager.get_events("Личный", days_ahead=7)

# Create event in Cyrillic calendar
event_data = {
    "summary": "Проектный дедлайн",
    "dtstart": datetime(2026, 2, 20, 17, 0, tzinfo=timezone.utc),
    "dtend": datetime(2026, 2, 20, 18, 0, tzinfo=timezone.utc),
    "description": "Финальная сдача проекта",
    "location": "Онлайн",
    "alarms": [
        {"minutes": 1440, "description": "За 1 день"},
        {"minutes": 60, "description": "За 1 час"}
    ]
}

success = manager.create_event(
    calendar_name="Работа",
    event_data=event_data,
    check_conflicts=True,
    auto_confirm=False
)

if success:
    print("✅ Событие создано успешно")
🛠️ Configuration
Environment Variables
bash
# Required (or use keyring)
export ICLOUD_USERNAME="user@icloud.com"
export ICLOUD_APP_PASSWORD="xxxx-xxxx-xxxx-xxxx"

# Optional
export DEFAULT_CALENDAR="Personal"
export LOG_LEVEL="INFO"  # DEBUG, INFO, WARNING, ERROR
Security Limits
python
# Configurable in calendar.py
MAX_CALENDAR_NAME_LENGTH = 255
MAX_SUMMARY_LENGTH = 500
MAX_DESCRIPTION_LENGTH = 5000
MAX_LOCATION_LENGTH = 500
MAX_JSON_FILE_SIZE = 1048576  # 1MB
MAX_DAYS_AHEAD = 365
RATE_LIMIT_CALLS = 10
RATE_LIMIT_WINDOW = 60  # seconds
INPUT_TIMEOUT = 30  # seconds
📊 Event Schema
Required Fields
summary (string): Event title (Unicode supported)

dtstart (ISO 8601 datetime): Start time

dtend (ISO 8601 datetime): End time

Optional Fields
description (string): Event details (Unicode supported)

location (string): Event location (Unicode supported)

status (string): CONFIRMED, TENTATIVE, CANCELLED

priority (int): 0-9 (0=undefined, 1=highest, 9=lowest)

attendees (array): List of attendee emails

alarms (array): List of alarm objects

rrule (object): Recurrence rule

Datetime Format
Use ISO 8601 with timezone:

text
2026-02-12T14:00:00+03:00  # Moscow time
2026-02-12T11:00:00Z       # UTC
2026-02-12T06:00:00-05:00  # EST
Recurrence Rule (RRULE)
json
{
  "freq": "WEEKLY",
  "interval": 1,
  "count": 10,
  "until": "2026-12-31",
  "