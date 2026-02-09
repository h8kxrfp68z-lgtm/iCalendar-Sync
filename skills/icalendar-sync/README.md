# 📅 iCalendar Sync for OpenClaw

**Professional iCloud Calendar integration with enterprise-grade security**

[![Version](https://img.shields.io/badge/version-2.2.0-blue.svg)](https://github.com/h8kxrfp68z-lgtm/OpenClaw/releases/tag/icalendar-sync-v2.2.0)
[![Security Rating](https://img.shields.io/badge/security-A-brightgreen.svg)](SECURITY.md)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)

## ✨ Features

### 💪 Core Capabilities

- ✅ **Full Calendar Sync** - Bidirectional sync with iCloud
- 🌐 **CalDAV Protocol** - Standard-compliant implementation
- 🗓️ **Event Management** - Create, read, update, delete events
- 🔁 **Recurring Events** - Full RRULE support (daily, weekly, monthly, yearly)
- ⏰ **Alarms & Reminders** - Multiple alarms per event
- 📱 **Multi-Device** - Instant sync across iPhone, iPad, Mac
- 📂 **Multiple Calendars** - Work, Personal, Custom calendars
- ⚡ **Conflict Detection** - Automatic scheduling conflict warnings

### 🔒 Security Features (v2.2.0)

- 🔑 **Keyring Integration** - Secure credential storage in OS keychain
- 🛡️ **Input Validation** - Protection against injection attacks
- 🚫 **Rate Limiting** - DoS protection (10 calls/60s)
- 🔐 **SSL Verification** - Enforced certificate validation
- 🧹 **Log Filtering** - Automatic credential redaction
- 🧵 **Thread Safety** - Safe concurrent access
- 📝 **Atomic Operations** - Safe file writes
- ⏱️ **Timeout Protection** - 30s timeout on interactive inputs

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

```bash
# Interactive setup wizard
icalendar-sync setup
```

You'll need:
1. **Apple ID email** (e.g., user@icloud.com)
2. **App-Specific Password** from https://appleid.apple.com
   - Go to: Sign-In & Security → App-Specific Passwords
   - Create new password for "OpenClaw iCalendar Sync"

Credentials are stored securely in:
- **macOS**: Keychain
- **Windows**: Credential Manager
- **Linux**: Secret Service (GNOME Keyring/KWallet)
- **Fallback**: `~/.openclaw/.env` (chmod 0600)

## 📖 Usage

### List Calendars

```bash
icalendar-sync list
```

Output:
```
📅 Available Calendars (3):

  • Personal
  • Work
  • Family
```

### Get Events

```bash
# Next 7 days (default)
icalendar-sync get --calendar "Work"

# Next 30 days
icalendar-sync get --calendar "Personal" --days 30
```

### Create Event

#### Simple Event

```bash
icalendar-sync create --calendar "Work" --json '{
  "summary": "Team Meeting",
  "dtstart": "2026-02-10T14:00:00+03:00",
  "dtend": "2026-02-10T15:00:00+03:00",
  "description": "Q1 Planning Discussion",
  "location": "Conference Room A"
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

# Then delete
icalendar-sync delete --calendar "Work" --uid "event-uid-here"
```

## 📚 API Usage (Python)

```python
from icalendar_sync import CalendarManager
from datetime import datetime, timezone, timedelta

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

## 🛠️ Configuration

### Environment Variables

```bash
# Required (or use keyring)
export ICLOUD_USERNAME="user@icloud.com"
export ICLOUD_APP_PASSWORD="xxxx-xxxx-xxxx-xxxx"

# Optional
export DEFAULT_CALENDAR="Personal"
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

## 📊 Event Schema

### Required Fields

- `summary` (string): Event title
- `dtstart` (ISO 8601 datetime): Start time
- `dtend` (ISO 8601 datetime): End time

### Optional Fields

- `description` (string): Event details
- `location` (string): Event location
- `status` (string): CONFIRMED, TENTATIVE, CANCELLED
- `priority` (int): 0-9 (0=undefined, 1=highest, 9=lowest)
- `attendees` (array): List of attendee emails
- `alarms` (array): List of alarm objects
- `rrule` (object): Recurrence rule

### Datetime Format

Use ISO 8601 with timezone:
```
2026-02-10T14:00:00+03:00  # Moscow time
2026-02-10T11:00:00Z       # UTC
2026-02-10T06:00:00-05:00  # EST
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

## 🔍 Troubleshooting

### Authentication Failed

```bash
❌ Authentication failed: Invalid credentials
```

**Solution**: 
1. Verify your Apple ID email is correct
2. Generate a new App-Specific Password at https://appleid.apple.com
3. Run `icalendar-sync setup` again

### Calendar Not Found

```bash
❌ Calendar 'Work' not found
```

**Solution**:
1. Run `icalendar-sync list` to see available calendars
2. Calendar names are case-sensitive
3. Ensure the calendar exists in your iCloud account

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
│       ├── __init__.py
│       └── calendar.py       # Main implementation
├── tests/
│   ├── test_calendar.py
│   └── test_security.py
├── pyproject.toml           # Project metadata
├── requirements.txt         # Dependencies
├── skill.yaml               # OpenClaw skill definition
├── README.md                # This file
├── CHANGELOG.md             # Version history
├── SECURITY.md              # Security policy
└── LICENSE                  # MIT License
```

## 🔒 Security

See [SECURITY.md](SECURITY.md) for:
- Security features
- Vulnerability reporting
- Audit results
- Best practices

**Security Rating**: A (Excellent)  
**Last Audit**: February 9, 2026  
**Version Audited**: 2.2.0

## 📝 Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history.

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

## 💬 Support

- **Issues**: [GitHub Issues](https://github.com/h8kxrfp68z-lgtm/OpenClaw/issues)
- **Discussions**: [GitHub Discussions](https://github.com/h8kxrfp68z-lgtm/OpenClaw/discussions)
- **Security**: security@clawhub.ai
- **Email**: contact@clawhub.ai

## 📜 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🚀 Roadmap

### v2.3.0 (Planned)
- [ ] Calendar sharing management
- [ ] Event search and filtering
- [ ] Batch operations API
- [ ] Webhook support for real-time sync

### v3.0.0 (Future)
- [ ] Google Calendar support
- [ ] Outlook/Exchange support
- [ ] Multi-platform sync engine
- [ ] Advanced conflict resolution

## 🙏 Acknowledgments

- [caldav](https://github.com/python-caldav/caldav) - CalDAV client library
- [icalendar](https://github.com/collective/icalendar) - iCalendar parser
- [keyring](https://github.com/jaraco/keyring) - Secure credential storage
- OpenClaw community for feedback and testing

---

**Made with ❤️ by Black_Temple**  
**For OpenClaw Multi-Agent Framework**

🌟 Star this repo if you find it useful!  
🐛 Report bugs or request features via [Issues](https://github.com/h8kxrfp68z-lgtm/OpenClaw/issues)
