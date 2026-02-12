# Bug Fixes - v2.2.11

**Release Date:** 2026-02-12
**Contributors:** Black_Temple (developer), Alfred (QA/field testing)

## 🐛 Fixed Issues

### 1. ✅ Cyrillic Calendar Names Support
**Issue:** Calendar names with Cyrillic characters (Личный, Работа, etc.) were rejected by `validate_calendar_name()`.

**Root Cause:** Regular expression `r'^[a-zA-Z0-9\s_-]+$'` only accepted Latin characters.

**Fix:** Changed to `r'^[\w\s_-]+$'` with `re.UNICODE` flag to support all Unicode letters including Cyrillic, Chinese, Arabic, etc.

**File:** `src/icalendar_sync/calendar.py:142`

**Example:**
```python
# Before: ❌ Invalid calendar name: Личный
# After:  ✅ Valid calendar name: Личный
```

---

### 2. ✅ Module Import RuntimeWarning Fixed
**Issue:** `RuntimeWarning: found in sys.modules after import of package 'icalendar_sync', but prior to execution...`

**Root Cause:** Python warning when `__main__.py` is executed as a module.

**Fix:** Added warning filter in `__main__.py` to suppress this specific RuntimeWarning.

**File:** `src/icalendar_sync/__main__.py:12-14`

---

### 3. ✅ Headless Configuration Support
**Issue:** Setup wizard required interactive input (`timed_input`), making it difficult to use in automated/headless environments.

**Fix:** Added command-line arguments for non-interactive setup:
- `--username EMAIL`: Provide Apple ID via CLI
- `--password PASSWORD`: Provide app-specific password via CLI
- `--non-interactive`: Suppress prompts

**Usage:**
```bash
# Headless setup
icalendar-sync setup --username user@icloud.com --password xxxx-xxxx-xxxx-xxxx --non-interactive

# Interactive setup (original behavior)
icalendar-sync setup
```

**Files:**
- `src/icalendar_sync/calendar.py:846-850` (arguments)
- `src/icalendar_sync/calendar.py:694-735` (logic)

---

## 📊 Testing Notes

### Test Environment
- **Platform:** Linux (OpenClaw agent environment)
- **Python:** 3.9+
- **Tester:** Alfred (OpenClaw user)

### Test Cases Passed
1. ✅ Creating events in Cyrillic-named calendars (Личный, Работа)
2. ✅ Running `python -m icalendar_sync` without warnings
3. ✅ Headless setup with `--username` and `--password`
4. ✅ Backwards compatibility with interactive setup

---

## 🔄 Migration Notes

**No breaking changes.** All existing configurations and workflows remain functional.

**New features are opt-in:**
- Cyrillic names work automatically
- Headless mode requires explicit `--username`/`--password` flags
- Interactive mode remains default

---

## 🙏 Credits

Special thanks to **Alfred** for detailed bug reports and field testing in production OpenClaw environment.

---

## 📝 Related Documents
- [CHANGELOG.md](CHANGELOG.md) - Full version history
- [SECURITY.md](SECURITY.md) - Security policy
- [README.md](README.md) - User documentation
