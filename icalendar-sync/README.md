# 📅 iCalendar Sync for OpenClaw

**Professional iCloud Calendar integration with enterprise-grade security**

[![Version](https://img.shields.io/badge/version-2.2.5-blue.svg)](https://github.com/h8kxrfp68z-lgtm/OpenClaw/releases)
[![Security Rating](https://img.shields.io/badge/security-A-brightgreen.svg)](SECURITY.md)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Cyrillic Support](https://img.shields.io/badge/cyrillic-✓-green.svg)](CHANGELOG.md)

---

## 🎉 New in v2.2.5 (Feb 12, 2026)

- **🔥 Cyrillic Calendar Names**: Full support for Russian, Ukrainian, and other Unicode calendar names ("Личный", "Работа", "Семья")
- **🔥 Headless Setup**: Automated credential configuration via CLI arguments for Docker, CI/CD, and agents
- **📦 Module Execution**: Run as Python module with `python -m icalendar_sync`
- **✨ Clean Output**: Eliminated RuntimeWarning for better UX

[See full CHANGELOG](CHANGELOG.md) | [Migration Guide](CALENDAR_PY_PATCH_2.2.5.md)

---

## ⚠️ CRITICAL NOTICE: What This Version Actually Includes

**Version 2.2.5 is a CORE IMPLEMENTATION** with essential CalDAV sync functionality. Some documentation files (DOCUMENTATION.md, ARCHITECTURE.md) describe **planned future features** that are not yet implemented.

**IMPORTANT: See SECURITY_SCAN_NOTICE.md for detailed responses to ClawHub security scan concerns.**

### ✅ ACTUALLY IMPLEMENTED IN v2.2.5:

**Fully functional modules:**
- `src/icalendar_sync/calendar.py` (33 KB) - Complete CalDAV client
  - Event CRUD operations (create, read, update, delete)
  - Credential management (keyring + .env fallback)
  - Input validation and security checks
  - Rate limiting (10 calls/60s)
  - Recurring events (RRULE support)
  - Multi-calendar support
  - **NEW:** Cyrillic/Unicode calendar names
  - CLI interface with headless mode

- `src/icalendar_sync/__main__.py` - Module entry point (NEW in v2.2.5)
- `src/icalendar_sync/i18n.py` (40 KB) - Internationalization for 20 languages
- `src/icalendar_sync/translations_extended.py` - Extended translations
- `src/icalendar_sync/translations_extended2.py` - Additional translations

### ❌ NOT IMPLEMENTED (Mentioned in Extended Docs Only):

**These modules do NOT exist as separate files in v2.2.5:**
- ❌ `calendar_vault.py` - Described in ARCHITECTURE.md but not implemented
- ❌ `privacy_engine.py` - Mentioned in DOCUMENTATION.md but not a separate module
- ❌ `rate_limiter.py` - Rate limiting is embedded in calendar.py, not standalone
- ❌ `connector/` directory - No separate connector modules
- ❌ Advanced multi-agent isolation system

**Why the documentation mismatch?**
- DOCUMENTATION.md and ARCHITECTURE.md were written for a future v3.0 architecture
- v2.2.5 consolidates all logic into `calendar.py` for simplicity
- Some "modules" exist as functions/classes within calendar.py, not separate files
- Extended docs are kept for reference/planning but describe future state

**What to trust:**
- ✅ **THIS README** - Accurate for v2.2.5
- ✅ **SKILL.md** - Accurate for v2.2.5  
- ✅ **skill.yaml** - Correct metadata (lines 33-46: `required: true`)
- ✅ **CLAWHUB_METADATA.yaml** - Explicit credential declarations
- ✅ **SECURITY_SCAN_NOTICE.md** - Addresses all ClawHub concerns
- ✅ **CHANGELOG.md** - Complete version history
- ⚠️ **DOCUMENTATION.md** - Mix of current + future features (read with caution)
- ⚠️ **ARCHITECTURE.md** - Describes future v3.0 architecture

### 🔒 CREDENTIALS REQUIRED:

**Despite what any cached metadata says, this skill REQUIRES:**
- `ICLOUD_USERNAME` - Your Apple ID (e.g., user@icloud.com)
- `ICLOUD_APP_PASSWORD` - App-Specific Password from https://appleid.apple.com

**Declared in:**
- skill.yaml lines 33-46 (`required: true`)
- CLAWHUB_METADATA.yaml (explicit declarations)
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
- 🌍 **Unicode Support** - Cyrillic, CJK, and all international scripts (NEW in v2.2.5)
- ⚡ **Conflict Detection** - Automatic scheduling conflict warnings

### 🔒 Security Features (v2.2.5)

- 🔑 **Keyring Integration** - Secure credential storage in OS keychain
- 🛡️ **Input Validation** - Protection against injection attacks (Unicode-aware)
- 🚫 **Rate Limiting** - DoS protection (10 calls/60s)
- 🔐 **SSL Verification** - Enforced certificate validation
- 🧹 **Log Filtering** - Automatic credential redaction
- 🧵 **Thread Safety** - Safe concurrent access
- 📝 **Atomic Operations** - Safe file writes
- ⏱️ **Timeout Protection** - 30s timeout on interactive inputs

---

## 🚀 Quick Start

### Installation

```bash
# From source
git clone https://github.com/h8kxrfp68z-lgtm/OpenClaw.git
cd OpenClaw/skills/icalendar-sync
pip install -e .

# Or via pip (when published)
pip install openclaw-icalendar-sync
```

### Setup

#### Interactive Setup (Default)

```bash
# Interactive setup wizard
icalendar-sync setup
```

You'll need:
1. **Apple ID email** (e.g., user@icloud.com)
2. **App-Specific Password** from https://appleid.apple.com
   - Go to: Sign-In & Security → App-Specific Passwords
   - Create new password for "OpenClaw iCalendar Sync"

#### Headless Setup (NEW in v2.2.5) 🔥

```bash
# For automation, Docker, CI/CD, OpenClaw agents
icalendar-sync setup \
  --username "user@icloud.com" \
  --password "xxxx-xxxx-xxxx-xxxx" \
  --non-interactive
```

Credentials are stored securely in:
- **macOS**: Keychain
- **Windows**: Credential Manager
- **Linux**: Secret Service (GNOME Keyring/KWallet)
- **Fallback**: `~/.openclaw/.env` (chmod 0600)

---

## 📖 Usage

### List Calendars

```bash
icalendar-sync list
```

Output:
```
📅 Available Calendars (5):

  • Personal
  • Work
  • Family
  • Личный      # Cyrillic support NEW in v2.2.5!
  • Работа      # Russian calendar names now work!
```

### Get Events

```bash
# Next 7 days (default)
icalendar-sync get --calendar "Work"

# Cyrillic calendar names (NEW in v2.2.5)
icalendar-sync get --calendar "Личный" --days 7
icalendar-sync get --calendar "Работа" --days 30

# English calendars still work
icalendar-sync get --calendar "Personal" --days 30
```

### Create Event

#### Simple Event

```bash
icalendar-sync create --calendar "Work" --json '{
  "summary": "Team Meeting",
  "dtstart": "2026-02-12T14:00:00+03:00",
  "dtend": "2026-02-12T15:00:00+03:00",
  "description": "Q1 Planning Discussion",
  "location": "Conference Room A"
}'
```

#### Cyrillic Event (NEW in v2.2.5)

```bash
icalendar-sync create --calendar "Личный" --json '{
  "summary": "Встреча с врачом",
  "dtstart": "2026-02-15T10:00:00+03:00",
  "dtend": "2026-02-15T11:00:00+03:00",
  "description": "Ежегодный осмотр",
  "location": "Поликлиника №5"
}'
```

#### From JSON File

```bash
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
```

#### Recurring Event

```bash
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
```

#### Skip Conflict Check

```bash
icalendar-sync create --calendar "Work" \
  --json event.json \
  --no-conflict-check \
  --yes  # Auto-confirm
```

### Delete Event

```bash
# First, get the event UID
icalendar-sync get --calendar "Work"

# Then delete (works with Cyrillic calendars too)
icalendar-sync delete --calendar "Личный" --uid "event-uid-here"
```

### Module Execution (NEW in v2.2.5) 📦

```bash
# All commands now work as Python module
python -m icalendar_sync list
python -m icalendar_sync setup
python -m icalendar_sync get --calendar "Личный" --days 7
python -m icalendar_sync create --calendar "Work" --json event.json
```

---

## 📚 API Usage (Python)

```python
from icalendar_sync import CalendarManager
from datetime import datetime, timezone, timedelta

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
    calendar_name="Работа",  # Cyrillic calendar name
    event_data=event_data,
    check_conflicts=True,
    auto_confirm=False
)

if success:
    print("✅ Событие создано успешно")
```

---

## 🛠️ Configuration

### Environment Variables

```bash
# Required (or use keyring)
export ICLOUD_USERNAME="user@icloud.com"
export ICLOUD_APP_PASSWORD="xxxx-xxxx-xxxx-xxxx"

# Optional
export DEFAULT_CALENDAR="Personal"  # Or "Личный" for Russian
export LOG_LEVEL="INFO"  # DEBUG, INFO, WARNING, ERROR
```

### Security Limits

```python
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
```

---

## 📊 Event Schema

### Required Fields

- `summary` (string): Event title (Unicode supported)
- `dtstart` (ISO 8601 datetime): Start time
- `dtend` (ISO 8601 datetime): End time

### Optional Fields

- `description` (string): Event details (Unicode supported)
- `location` (string): Event location (Unicode supported)
- `status` (string): CONFIRMED, TENTATIVE, CANCELLED
- `priority` (int): 0-9 (0=undefined, 1=highest, 9=lowest)
- `attendees` (array): List of attendee emails
- `alarms` (array): List of alarm objects
- `rrule` (object): Recurrence rule

### Datetime Format

Use ISO 8601 with timezone:
```
2026-02-12T14:00:00+03:00  # Moscow time
2026-02-12T11:00:00Z       # UTC
2026-02-12T06:00:00-05:00  # EST
```

### Recurrence Rule (RRULE)

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

## 🔍 Troubleshooting

### Invalid Calendar Name (Fixed in v2.2.5)

```bash
# v2.2.4 and earlier:
❌ Invalid calendar name  # When using "Личный"

# v2.2.5:
✅ Calendar names with Cyrillic, CJK, and Unicode now work!
```

**Solution**: Upgrade to v2.2.5 or later.

### Authentication Failed

```bash
❌ Authentication failed: Invalid credentials
```

**Solution**: 
1. Verify your Apple ID email is correct
2. Generate a new App-Specific Password at https://appleid.apple.com
3. Run `icalendar-sync setup` again (or use `--non-interactive` for automation)

### Calendar Not Found

```bash
❌ Calendar 'Work' not found
```

**Solution**:
1. Run `icalendar-sync list` to see available calendars
2. Calendar names are case-sensitive and Unicode-aware
3. Use exact name including spaces and special characters
4. Ensure the calendar exists in your iCloud account

### Rate Limit Exceeded

```bash
Rate limit exceeded, waiting...
```

**Solution**: This is normal. The tool automatically waits and retries. To avoid:
- Reduce frequency of calls
- Batch operations when possible
- Current limit: 10 calls per 60 seconds

### SSL Certificate Error

```bash
❌ Network error: SSL certificate verify failed
```

**Solution**:
1. Update CA certificates: `pip install --upgrade certifi`
2. Check system date/time is correct
3. Verify network isn't using SSL interception

### Keyring Not Available

```bash
⚠️ Could not access system keyring, falling back to .env file
```

**Solution**: This is a warning, not an error. Install keyring backend:
```bash
# Linux
sudo apt-get install gnome-keyring  # or kwallet

# macOS/Windows: Built-in
```

### Module Import Error (Fixed in v2.2.5)

```bash
# v2.2.4 and earlier:
python -m icalendar_sync list
# ModuleNotFoundError: No module named 'icalendar_sync'

# v2.2.5:
python -m icalendar_sync list
# ✅ Works correctly
```

**Solution**: Upgrade to v2.2.5 or use `icalendar-sync` command directly.

---

## 💻 Development

### Setup Development Environment

```bash
git clone https://github.com/h8kxrfp68z-lgtm/OpenClaw.git
cd OpenClaw/skills/icalendar-sync

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -e ".[dev]"

# Run tests
pytest tests/ -v

# Code formatting
black src/

# Security scan
bandit -r src/
pip-audit
```

### Project Structure

```
icalendar-sync/
├── src/
│   └── icalendar_sync/
│       ├── __init__.py              # Package initialization
│       ├── __main__.py              # Module entry point (NEW v2.2.5)
│       ├── calendar.py              # Main implementation (33 KB)
│       ├── i18n.py                  # Internationalization (40 KB)
│       ├── translations_extended.py
│       └── translations_extended2.py
├── tests/
│   ├── test_calendar.py
│   └── test_security.py
├── docs/
│   ├── ARCHITECTURE.md              # ⚠️ Describes future v3.0 architecture
│   └── MULTILINGUAL.md              # ✅ Current i18n documentation
├── pyproject.toml                   # Project metadata
├── requirements.txt                 # Dependencies
├── skill.yaml                       # OpenClaw skill definition
├── README.md                        # ✅ This file (accurate for v2.2.5)
├── SKILL.md                         # ✅ Accurate capabilities list
├── CHANGELOG.md                     # ✅ Version history (NEW v2.2.5)
├── CALENDAR_PY_PATCH_2.2.5.md       # ✅ Upgrade patch instructions
├── VERSION_2.2.5_SUMMARY.md         # ✅ Release summary
├── DOCUMENTATION.md                 # ⚠️ Mix of current + future features
├── CLAWHUB_METADATA.yaml            # ✅ Security metadata
├── SECURITY_SCAN_NOTICE.md          # ✅ Security scan responses
├── SECURITY.md                      # Security policy
└── LICENSE                          # MIT License
```

---

## 🔒 Security

See [SECURITY.md](SECURITY.md) for:
- Security features
- Vulnerability reporting
- Audit results
- Best practices

**Security Rating**: A (Excellent)  
**Last Audit**: February 12, 2026  
**Version Audited**: 2.2.5

---

## 📝 Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history.

**Latest (v2.2.5)**: Cyrillic support, headless setup, module execution, bug fixes.

---

## 👥 Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

### Code Standards

- Python 3.9+ compatible
- Type hints required
- Black formatting (line length 100)
- Pytest for tests
- Security-first mindset
- Unicode-aware string handling (NEW requirement v2.2.5)

---

## 💬 Support

- **Issues**: [GitHub Issues](https://github.com/h8kxrfp68z-lgtm/OpenClaw/issues)
- **Discussions**: [GitHub Discussions](https://github.com/h8kxrfp68z-lgtm/OpenClaw/discussions)
- **Security**: security@clawhub.ai
- **Email**: contact@clawhub.ai

---

## 📜 License

MIT License - see [LICENSE](LICENSE) file for details.

---

## 🚀 Roadmap

### v2.3.0 (Planned)
- [ ] Calendar sharing management
- [ ] Event search and filtering
- [ ] Batch operations API
- [ ] Webhook support for real-time sync

### v3.0.0 (Future)
- [ ] Separate calendar_vault module
- [ ] Standalone privacy_engine module
- [ ] Separate rate_limiter module
- [ ] Google Calendar support
- [ ] Outlook/Exchange support
- [ ] Multi-platform sync engine
- [ ] Advanced conflict resolution
- [ ] Multi-agent isolation system

---

## 🙏 Acknowledgments

- [caldav](https://github.com/python-caldav/caldav) - CalDAV client library
- [icalendar](https://github.com/collective/icalendar) - iCalendar parser
- [keyring](https://github.com/jaraco/keyring) - Secure credential storage
- OpenClaw community for feedback and testing
- Russian users for reporting Cyrillic issues (fixed in v2.2.5!)

---

**Made with ❤️ by Black_Temple**  
**For OpenClaw Multi-Agent Framework**

🌟 Star this repo if you find it useful!  
🐛 Report bugs or request features via [Issues](https://github.com/h8kxrfp68z-lgtm/OpenClaw/issues)  
🇷🇺 Теперь с поддержкой русского языка! (v2.2.5)
