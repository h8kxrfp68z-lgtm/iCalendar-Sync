# iCloud Calendar Sync v2.2.6

## Security Improvements

- Fixed metadata inconsistency in CLAWHUB_METADATA.yaml
- Added explicit required environment variables declaration (ICLOUD_USERNAME, ICLOUD_APP_PASSWORD)
- Enhanced SKILL.md with comprehensive security warnings
- Documented credential handling best practices
- Added warnings about CLI password exposure and plaintext .env file risks

## What's Fixed

- Registry metadata now correctly reflects required credentials
- Improved documentation for secure credential storage using OS keyring
- Added Docker secrets best practices
- Clarified app-specific password requirements

## Installation

```bash
./install.sh
Requirements
Python 3.8+

iCloud app-specific password (generated at https://appleid.apple.com/account/security)

OS keyring support or ability to use .env file for credentials

Release Date
February 12, 2026