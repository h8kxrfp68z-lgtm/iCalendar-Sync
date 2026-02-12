text
# iCloud Calendar Sync Skill

Synchronizes calendar events between local system and iCloud.

## ⚠️ Security Requirements

**MUST READ before installation:**

1. **Never pass password via CLI**:
   ```bash
   # ❌ DANGEROUS
   ./icalendar-sync --username user@icloud.com --password "MyPassword"
   
   # ✅ SECURE - use keyring
   ./icalendar-sync --username user@icloud.com
Do NOT use .env file in production:

~/.openclaw/.env stores password in plaintext

Use only for development

On production use OS keyring

For Docker - use secrets:

bash
# ❌ DANGEROUS
docker run -e ICLOUD_PASSWORD="secret" ...

# ✅ SECURE
docker run --secret icloud_password ...
Use app-specific password:

Generate at https://appleid.apple.com/account/security

DO NOT use main Apple ID password

Can be revoked anytime

Installation
bash
./install.sh
Usage
Setup Credentials
bash
# Interactive mode (secure)
python -m icalendar_sync --setup

# Or use keyring directly
python -m icalendar_sync --username user@icloud.com
# Password will be prompted securely
List Events
bash
python -m icalendar_sync list --start "2024-01-01" --end "2024-12-31"
Requirements
Python 3.8+

iCloud app-specific password

Access to iCloud CalDAV server

License
MIT

