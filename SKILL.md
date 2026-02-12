# iCloud Calendar Sync Skill

Synchronizes calendar events between local system and iCloud.

## ⚠️ Security Requirements

**CRITICAL - Read before installation:**

### 1. Use App-Specific Password ONLY

- Generate at https://appleid.apple.com/account/security
- **NEVER use your main Apple ID password**
- Can be revoked anytime if compromised

### 2. Use OS Keyring for Credential Storage

The skill stores credentials securely in your operating system's keyring:
- **macOS**: Keychain
- **Windows**: Credential Manager
- **Linux**: Secret Service API

### 3. For Docker/Containers - Use Secrets Manager

```bash
# ✅ SECURE - Use Docker secrets
docker run --secret icloud_username --secret icloud_password ...

# ✅ SECURE - Use Kubernetes secrets
kubectl create secret generic icloud-credentials \
  --from-literal=username=user@icloud.com \
  --from-literal=password=xxxx-xxxx-xxxx-xxxx
```

## Installation

```bash
./install.sh
```

## Usage

### Setup Credentials (Interactive)

```bash
# Interactive mode - password prompted securely
python -m icalendar_sync setup --username user@icloud.com
```

The password will be prompted interactively and stored in OS keyring.

### List Calendars

```bash
python -m icalendar_sync list
```

### Get Calendar Events

```bash
python -m icalendar_sync get --calendar "Personal" --days 7
```

### Create Event

```bash
python -m icalendar_sync create \
  --calendar "Personal" \
  --title "Meeting" \
  --start "2024-06-15 14:00" \
  --duration 60
```

### Delete Event

```bash
python -m icalendar_sync delete --calendar "Personal" --uid "event-uid-here"
```

## Requirements

- Python 3.9+
- iCloud app-specific password
- Access to iCloud CalDAV server (caldav.icloud.com:443)

## Security Features

- ✅ OS keyring integration for credential storage
- ✅ App-specific password requirement (not main password)
- ✅ SSL/TLS verification enforced
- ✅ Rate limiting (10 calls per 60 seconds)
- ✅ Automatic credential redaction in logs
- ✅ Input validation on all user inputs

## License

MIT
