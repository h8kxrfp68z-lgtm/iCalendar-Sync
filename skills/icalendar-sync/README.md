# iCalendar Sync for OpenClaw

**Professional iCloud Calendar integration with Zero Trust security.**

[![Author](https://img.shields.io/badge/author-Black__Temple-blue.svg)](https://github.com/h8kxrfp68z-lgtm)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.9+-green.svg)](https://www.python.org/)

iCalendar Sync connects your OpenClaw agents to the Apple iCloud ecosystem safely and securely. It provides a robust bridge for reading and writing calendar events while maintaining strict privacy boundaries between different AI agents.

## 🌟 Features

- **🔒 Zero Trust Security:** Agents access only explicitly authorized calendars
- **🕵️ Privacy First:** Automatic sanitization of private event details
- **⚡ Real-time Sync:** Instant updates across all Apple devices
- **🤖 Multi-Agent Support:** Complete isolation between Work, Personal, Family contexts
- **🍏 Native Support:** Full compatibility with iCloud CalDAV standards
- **📊 Granular ACL:** Fine-grained permission control per calendar

## 🚀 Quick Start

### Installation

```bash
# Via OpenClaw CLI
openclaw skill install @Black_Temple/icalendar-sync
```

### Setup

```bash
# Interactive configuration
icalendar-sync setup
```

The tool will ask for:
- Your iCloud email
- App-Specific Password (generated at [appleid.apple.com](https://appleid.apple.com/))
- Test the connection

### Usage

```bash
# List your calendars
icalendar-sync list

# Get events
icalendar-sync get --calendar "Work"

# Create event
icalendar-sync create --calendar "Personal" \
  --summary "Team Meeting" \
  --start "2026-02-10T14:00:00" \
  --end "2026-02-10T15:00:00"
```

## 🔐 App-Specific Password
Your regular Apple ID password will not work.
1. Go to [appleid.apple.com](https://appleid.apple.com/)
2. Sign in
3. Navigate to Sign-In and Security
4. Click App-Specific Passwords
5. Generate new password named "iCalendar Sync"
6. Copy the code: xxxx-xxxx-xxxx-xxxx

## 🔒 Security & Privacy

### Zero Trust Model
- Agents can see **only** calendars explicitly granted to them
- Undeclared calendars are completely hidden
- Unauthorized access attempts are logged and blocked

### Data Privacy
- Private event details are automatically filtered
- Attendee lists hidden from non-participants
- Location data sanitized for unauthorized agents

## 📊 Architecture

```text
OpenClaw Framework
├── Agent 1: WorkAssistant → Work, Team calendars
├── Agent 2: PersonalHelper → Personal, Family calendars
└── Agent 3: FitnessCoach → Fitness calendar

         ↓ (iCalendar Sync)
         
iCloud Calendar Server
├── CalDAV Protocol
└── Real-time Sync
```

## 💻 Python API Usage

If you want to use `CalendarManager` as a library in your own Python code:

### Installation as Library

```bash
pip install -e skills/icalendar-sync
```

### Basic Usage

```python
from icalendar_sync import CalendarManager
from datetime import datetime, timedelta

# Initialize manager (credentials from environment or .env)
mgr = CalendarManager()

# List available calendars
calendars = mgr.list_calendars()
print("Available calendars:", calendars)

# Get events from specific calendar
events = mgr.get_events("Work", days_ahead=7)
for event in events:
    print(f"{event['summary']}: {event['start']} - {event['end']}")

# Create new event
event_data = {
    "summary": "Team Standup",
    "start": datetime.now() + timedelta(days=1),
    "end": datetime.now() + timedelta(days=1, hours=1),
    "description": "Daily sync meeting",
    "location": "Zoom"
}
mgr.create_event("Work", event_data)

# Delete event by UID
mgr.delete_event("Work", "event-uid-here")
```

### Advanced: Multi-Agent Isolation

```python
# Agent 1: Work context
work_agent = CalendarManager(allowed_calendars=["Work", "Team"])
work_events = work_agent.get_events("Work")

# Agent 2: Personal context (cannot access Work calendar)
personal_agent = CalendarManager(allowed_calendars=["Personal", "Family"])
# This will raise PermissionError:
# personal_agent.get_events("Work")
```

### Error Handling

```python
from icalendar_sync import CalendarManager, CalendarError

try:
    mgr = CalendarManager()
    mgr.create_event("NonExistent", event_data)
except CalendarError as e:
    print(f"Calendar error: {e}")
except PermissionError as e:
    print(f"Access denied: {e}")
```

## 🔧 Troubleshooting

### Common Errors

**❌ 401 Unauthorized**
- **Reason:** Using regular Apple ID password instead of App-Specific Password
- **Solution:** Generate App-Specific Password at [appleid.apple.com](https://appleid.apple.com/) (see section above)

**❌ Calendar not found**
- **Reason:** Calendar name doesn't match or case sensitivity
- **Solution:** 
  1. Run `icalendar-sync list` to see exact names
  2. Use the name in the same case: "Work" ≠ "work"
  3. If name contains spaces, use quotes: `"My Calendar"`

**❌ Connection timeout**
- **Reason:** Network issues or CalDAV blocking
- **Solution:** Check internet connection and firewall settings

**❌ Invalid JSON format**
- **Reason:** Incorrect event data format
- **Solution:** Check required fields: summary, start, end. Use ISO 8601 format for dates

**❌ Event overlap detected**
- **Reason:** Time conflict with existing event
- **Solution:** Check calendar with `get_events` and choose different time

## 📝 License
MIT License. Copyright (c) 2026 Black_Temple.
See [LICENSE](LICENSE) for details.

## 🤝 Contributing
Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests
4. Submit a PR

## 💬 Support
- 📖 [Documentation](https://github.com/h8kxrfp68z-lgtm/OpenClaw/tree/feature/icalendar-sync/skills/icalendar-sync)
- 🐛 [Issues](https://github.com/h8kxrfp68z-lgtm/OpenClaw/issues)
- 💬 [Discussions](https://github.com/h8kxrfp68z-lgtm/OpenClaw/discussions)
