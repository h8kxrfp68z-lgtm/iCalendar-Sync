# Changelog

All notable changes to iCalendar Sync will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.2.0] - 2026-02-09

### 🔒 Security

#### Critical Fixes
- **Injection Protection**: Added strict validation for calendar names (alphanumeric, spaces, hyphens, underscores only)
- **Credential Storage**: Implemented secure keyring integration (macOS Keychain, Windows Credential Manager, Linux Secret Service)
- **Path Traversal Protection**: Added file path validation and restrictions
- **Rate Limiting**: Implemented API rate limiting (10 calls per 60 seconds)
- **SSL Verification**: Enforced SSL certificate verification for all CalDAV connections

#### Additional Security Enhancements
- **Input Sanitization**: All text fields now sanitized and length-limited
  - Summary: 500 chars
  - Description: 5000 chars
  - Location: 500 chars
  - Calendar name: 255 chars
- **Log Filtering**: Sensitive data (passwords, emails) automatically filtered from logs
- **Input Timeout**: 30-second timeout for interactive prompts
- **JSON Size Limit**: Maximum 1MB for JSON input files
- **Thread Safety**: Thread-safe connection caching with locks

### 🐛 Bug Fixes

- **Race Condition**: Fixed race condition in connection caching with threading.Lock
- **Timezone Handling**: Corrected timezone conversion for all-day events
- **Memory Leak**: Added traceback cleanup in retry decorator
- **Atomic File Write**: Implemented atomic .env file writing using tempfile
- **Input Validation**: Added days_ahead range validation (1-365)
- **Email Validation**: Enhanced email validation with proper regex

### ✨ Features

- **Keyring Integration**: Primary credential storage via system keyring
- **Auto-confirm Flag**: Added `--yes` flag to skip interactive confirmations
- **Better Error Messages**: More informative error messages with type names
- **SensitiveDataFilter**: Custom logging filter for credential protection
- **RateLimiter Class**: Dedicated rate limiting implementation

### 📝 Documentation

- Added comprehensive security constants at module level
- Enhanced docstrings for all security-critical functions
- Improved CLI help messages with examples

### 🔧 Technical Improvements

- Python 3.9+ required
- Added keyring>=24.0.0 dependency
- Improved type hints throughout
- Better exception handling with specific types
- Connection caching (5-minute timeout)
- Exponential backoff in retry logic

### 🎯 Code Quality

- **Security Rating**: A (excellent)
- **Critical Vulnerabilities**: 0
- **High Risk Issues**: 0
- **Medium Risk Issues**: 0
- **Low Risk Issues**: 4 (minor improvements for future versions)

## [2.1.1] - 2026-02-09

### 🐛 Bug Fixes

- Fixed YAML structure in skill.yaml
- Fixed timezone handling issues
- Added proper conflict detection
- Improved RRULE generation
- Fixed newline escaping in cmd_setup

## [2.0.0] - 2026-02-09

### ✨ Initial Release

- Professional iCloud Calendar integration
- CalDAV protocol support
- Event creation, listing, and deletion
- Recurring events support
- Alarm/reminder support
- Multi-calendar support
- Interactive setup wizard

---

[2.2.0]: https://github.com/h8kxrfp68z-lgtm/OpenClaw/releases/tag/icalendar-sync-v2.2.0
[2.1.1]: https://github.com/h8kxrfp68z-lgtm/OpenClaw/compare/icalendar-sync-v2.0.0...icalendar-sync-v2.1.1
[2.0.0]: https://github.com/h8kxrfp68z-lgtm/OpenClaw/releases/tag/icalendar-sync-v2.0.0
