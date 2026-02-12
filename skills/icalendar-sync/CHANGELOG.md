# Changelog

All notable changes to iCalendar Sync will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.2.5] - 2026-02-12

### Added
- 🔥 **Cyrillic calendar names support**: Теперь можно использовать русские названия календарей ("Личный", "Работа", etc.)
- 🔥 **Headless setup mode**: CLI flags `--username`, `--password`, `--non-interactive` for automation
- 📦 **Module execution support**: Can now run via `python -m icalendar_sync`
- 📄 Created `__main__.py` for proper package entry point

### Changed
- `validate_calendar_name()`: Changed regex from `r'^[a-zA-Z0-9\s_-]+$'` to `r'^[\w\s_-]+$'` for Unicode support
- `cmd_setup()`: Added optional CLI arguments `--username`, `--password`, `--non-interactive`
- Version bumped from 2.2.4 → 2.2.5 in all files

### Fixed
- 🐛 **CRITICAL**: Russian users blocked by ASCII-only calendar name validation
- 🐛 **HIGH**: Headless environments unable to run setup (timed_input issues)
- 🐛 **MEDIUM**: `ModuleNotFoundError` when running `python -m icalendar_sync`
- 🐛 **LOW**: RuntimeWarning about duplicate module imports

### Technical Details

**Regex Change:**
```python
# Old (v2.2.4):
if not re.match(r'^[a-zA-Z0-9\s_-]+$', name):
    return False

# New (v2.2.5):
if not re.match(r'^[\w\s_-]+$', name, re.UNICODE):
    return False
```

**Headless Setup:**
```bash
# Old: Interactive only
icalendar-sync setup
# (prompts for email and password)

# New: Supports CLI args
icalendar-sync setup --username "user@icloud.com" --password "xxxx-xxxx-xxxx-xxxx" --non-interactive
```

**Module Execution:**
```bash
# Now works:
python -m icalendar_sync list
python -m icalendar_sync setup
```

---

## [2.2.4] - 2026-02-11

### Fixed
- 🚨 **CRITICAL**: Removed duplicate `src/` directory from repository root
- 🚨 Deleted `src/icalendar_sync/calendar_vault/` files causing [docs-code-mismatch]
- Documentation now matches actual code structure

### Changed
- Updated `CLAWHUB_METADATA.yaml` with cleanup explanation
- Clarified repository structure in all documentation

---

## [2.2.3] - 2026-02-11

### Added
- `CLAWHUB_METADATA.yaml`: Machine-readable credential declarations
- `SECURITY_SCAN_NOTICE.md`: Comprehensive response to ClawHub security scan

### Changed
- Enhanced `skill.yaml` with explicit credential declarations (lines 1-10, 33-46)
- Strengthened security documentation in README.md and SKILL.md
- Version bumped to 2.2.3

---

## [2.2.2] - 2026-02-10

### Changed
- Documentation updates and security scan responses
- Clarified metadata inconsistencies

---

## [2.2.1] - 2026-02-09

### Added
- Internationalization support (i18n.py with 20 languages)
- Extended translations

---

## [2.2.0] - 2026-02-08

### Added
- Rate limiting (10 calls / 60 seconds)
- Input validation and sanitization
- Conflict detection for events
- Atomic file operations
- Thread-safe connection caching
- Sensitive data filtering in logs

### Security
- Enhanced credential storage (keyring primary, .env fallback)
- SSL certificate verification enforced
- Path traversal prevention
- JSON file size limits
- Timeout protection on user inputs

---

## [2.1.0] - 2026-02-05

### Added
- Recurring events support (RRULE)
- Multi-alarm support
- Enhanced error handling with retry logic

---

## [2.0.0] - 2026-02-01

### Added
- Complete CalDAV client implementation
- CRUD operations for events
- Interactive setup wizard
- CLI interface
- Security features baseline

---

## [1.0.0] - 2026-01-15

### Added
- Initial release
- Basic iCloud calendar sync
- Event listing
