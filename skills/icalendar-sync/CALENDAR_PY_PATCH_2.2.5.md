# Code Patch for calendar.py v2.2.5

This file contains specific code changes needed for `src/icalendar_sync/calendar.py` to upgrade from v2.2.4 to v2.2.5.

---

## Change 1: Update version string

**Line:** ~9  
**Old:**
```python
@version: 2.2.0
```

**New:**
```python
@version: 2.2.5
```

---

## Change 2: Update __version__ variable

**Line:** ~36  
**Old:**
```python
__version__ = "2.2.0"
```

**New:**
```python
__version__ = "2.2.5"
```

---

## Change 3: Fix validate_calendar_name() - Support Cyrillic

**Line:** ~147-153 (function `validate_calendar_name`)  
**Old:**
```python
def validate_calendar_name(name: str) -> bool:
    """Validate calendar name for security"""
    if not name or not isinstance(name, str):
        return False
    if len(name) > MAX_CALENDAR_NAME_LENGTH:
        return False
    # Allow only alphanumeric, spaces, hyphens, underscores
    if not re.match(r'^[a-zA-Z0-9\s_-]+$', name):
        return False
    # Prevent path traversal
    if '..' in name or '/' in name or '\\' in name:
        return False
    return True
```

**New:**
```python
def validate_calendar_name(name: str) -> bool:
    """Validate calendar name for security (supports Unicode/Cyrillic)"""
    if not name or not isinstance(name, str):
        return False
    if len(name) > MAX_CALENDAR_NAME_LENGTH:
        return False
    # Allow Unicode word characters (alphanumeric + Cyrillic, CJK, etc.), spaces, hyphens, underscores
    # \w in Python 3 with re.UNICODE matches [a-zA-Z0-9_] + Unicode letters/digits
    if not re.match(r'^[\w\s-]+$', name, re.UNICODE):
        return False
    # Prevent path traversal
    if '..' in name or '/' in name or '\\' in name:
        return False
    return True
```

**Key change:** `r'^[a-zA-Z0-9\s_-]+$'` → `r'^[\w\s-]+$'` with `re.UNICODE` flag.

**Why:** `\w` with `re.UNICODE` matches any Unicode letter or digit, including Cyrillic (А-Я, а-я), allowing Russian calendar names like "Личный", "Работа".

---

## Change 4: Add headless setup support - Update cmd_setup()

**Line:** ~789-856 (function `cmd_setup`)  
**Old:**
```python
def cmd_setup(args):
    """Interactive setup of credentials"""
    print("\n🔧 iCalendar Sync Setup\n")
    print("To use iCalendar Sync, you need to configure your iCloud credentials.")
    print("⚠️  Use an App-Specific Password, NOT your regular Apple ID password.\n")
    print("Get it from: https://appleid.apple.com -> Sign-In & Security -> App-Specific Passwords\n")
    
    email = input("📧 iCloud Email: ").strip()
    if not email:
        print("❌ Email cannot be empty")
        return
    
    # Validate email
    if not validate_email(email):
        print("❌ Invalid email format")
        response = timed_input("Continue anyway? (y/n): ")
        if response is None or response.lower() != 'y':
            print("Setup cancelled")
            return
    
    password = getpass.getpass("🔑 App-Specific Password (xxxx-xxxx-xxxx-xxxx): ").strip()
    if not password:
        print("❌ Password cannot be empty")
        return
    
    # Validate format
    if not all(c.isalnum() or c == '-' for c in password):
        print("⚠️  Password format looks unusual")
        response = timed_input("Are you sure this is correct? (y/n): ")
        if response is None or response.lower() != 'y':
            print("Setup cancelled")
            return
    
    # ... rest of function (saving credentials) ...
```

**New:**
```python
def cmd_setup(args):
    """Interactive or headless setup of credentials"""
    # Check if headless mode (CLI arguments provided)
    non_interactive = getattr(args, 'non_interactive', False)
    cli_username = getattr(args, 'username', None)
    cli_password = getattr(args, 'password', None)
    
    if cli_username and cli_password:
        # Headless mode: use CLI arguments
        email = cli_username.strip()
        password = cli_password.strip()
        
        if not email or not password:
            print("❌ Username and password cannot be empty")
            return
        
        # Validate email (but don't prompt in non-interactive mode)
        if not validate_email(email):
            if non_interactive:
                print("⚠️  Email format looks invalid but continuing (non-interactive mode)")
                logger.warning(f"Invalid email format in non-interactive setup: {email[:3]}***")
            else:
                print("❌ Invalid email format")
                return
        
    else:
        # Interactive mode: prompt user
        if non_interactive:
            print("❌ Non-interactive mode requires --username and --password")
            return
        
        print("\n🔧 iCalendar Sync Setup\n")
        print("To use iCalendar Sync, you need to configure your iCloud credentials.")
        print("⚠️  Use an App-Specific Password, NOT your regular Apple ID password.\n")
        print("Get it from: https://appleid.apple.com -> Sign-In & Security -> App-Specific Passwords\n")
        
        email = input("📧 iCloud Email: ").strip()
        if not email:
            print("❌ Email cannot be empty")
            return
        
        # Validate email
        if not validate_email(email):
            print("❌ Invalid email format")
            response = timed_input("Continue anyway? (y/n): ")
            if response is None or response.lower() != 'y':
                print("Setup cancelled")
                return
        
        password = getpass.getpass("🔑 App-Specific Password (xxxx-xxxx-xxxx-xxxx): ").strip()
        if not password:
            print("❌ Password cannot be empty")
            return
        
        # Validate format
        if not all(c.isalnum() or c == '-' for c in password):
            print("⚠️  Password format looks unusual")
            response = timed_input("Are you sure this is correct? (y/n): ")
            if response is None or response.lower() != 'y':
                print("Setup cancelled")
                return
    
    # Common path: save credentials (same for both interactive and headless)
    # Try to store in keyring first
    try:
        keyring.set_password('openclaw-icalendar', email, password)
        print("\n✅ Credentials saved securely to system keyring")
        logger.info("Credentials stored in keyring")
    except KeyringError:
        print("⚠️  Could not access system keyring, falling back to .env file")
        
        # Fallback to .env file with atomic write
        env_path = Path.home() / ".openclaw" / ".env"
        env_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Read existing lines
        lines = []
        if env_path.exists():
            with open(env_path, 'r') as f:
                lines = [l for l in f.readlines() 
                        if not l.startswith(('ICLOUD_USERNAME', 'ICLOUD_APP_PASSWORD'))]
        
        # Write atomically using temp file
        lines.append(f'ICLOUD_USERNAME="{email}"\n')
        lines.append(f'ICLOUD_APP_PASSWORD="{password}"\n')
        
        with tempfile.NamedTemporaryFile('w', delete=False, dir=env_path.parent) as tmp:
            tmp.writelines(lines)
            tmp_path = tmp.name
        
        shutil.move(tmp_path, str(env_path))
        os.chmod(env_path, 0o600)
        
        print(f"\n✅ Configuration saved securely to {env_path}")
    
    if not non_interactive:
        print("🚀 You can now use iCalendar Sync!\n")
```

**Key changes:**
1. Added support for `args.username`, `args.password`, `args.non_interactive`
2. If CLI args provided → skip prompts, use them directly
3. If `--non-interactive` flag → don't prompt user for confirmations
4. Preserved original interactive flow when no CLI args given

---

## Change 5: Update argument parser - Add setup arguments

**Line:** ~920-925 (in `main()` function, setup_parser section)  
**Old:**
```python
# Setup
setup_parser = subparsers.add_parser('setup', help='Configure iCloud credentials')
setup_parser.set_defaults(func=cmd_setup)
```

**New:**
```python
# Setup
setup_parser = subparsers.add_parser('setup', help='Configure iCloud credentials')
setup_parser.add_argument('--username', help='iCloud email (for non-interactive setup)')
setup_parser.add_argument('--password', help='App-Specific Password (for non-interactive setup)')
setup_parser.add_argument('--non-interactive', action='store_true',
                         help='Non-interactive mode (no prompts, use --username and --password)')
setup_parser.set_defaults(func=cmd_setup)
```

**Key change:** Added three optional arguments to `setup` command.

---

## Summary of Changes

| Change | Line(s) | Priority | Impact |
|--------|---------|----------|--------|
| Version strings | ~9, ~36 | LOW | Metadata only |
| `validate_calendar_name()` | ~147-153 | 🔴 HIGH | **Enables Cyrillic names** |
| `cmd_setup()` | ~789-856 | 🔴 HIGH | **Enables headless setup** |
| Setup arg parser | ~920-925 | 🔴 HIGH | **Enables headless setup** |

---

## Testing

### Test 1: Cyrillic calendar names
```bash
# Should now work (previously failed with "Invalid calendar name"):
icalendar-sync list
icalendar-sync get --calendar "Личный" --days 7
icalendar-sync create --calendar "Работа" --json '{...}'
```

### Test 2: Headless setup
```bash
# Non-interactive setup (for automation, Docker, CI/CD):
icalendar-sync setup \
  --username "user@icloud.com" \
  --password "xxxx-xxxx-xxxx-xxxx" \
  --non-interactive

# Should complete without prompts and save credentials
```

### Test 3: Module execution
```bash
# Should work without errors:
python -m icalendar_sync list
python -m icalendar_sync setup

# Should NOT show RuntimeWarning anymore
```

---

## Migration Notes

**Breaking changes:** None. All changes are backward compatible.

**New features:**
- Calendar names can now use Cyrillic, CJK, and other Unicode scripts
- Setup can be automated via CLI arguments
- Module can be executed via `python -m icalendar_sync`

**Deprecated:** None.

---

## Implementation

To apply this patch manually:

1. Open `skills/icalendar-sync/src/icalendar_sync/calendar.py`
2. Apply each change listed above
3. Verify changes with: `grep -n "__version__\|validate_calendar_name\|cmd_setup" calendar.py`
4. Test with Russian calendar names and headless setup

Or let me create the complete updated file...
