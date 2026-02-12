# OpenClaw Skills — skills branch

This branch contains ready-to-use skills and plugins for the OpenClaw framework. Each skill is packaged so it can be inspected independently and integrated into an OpenClaw installation or used standalone where applicable.

This repository is intended as a curated collection of skill implementations, examples, and metadata that make it easy to test, publish, and register skills with ClawHub/registry systems.

---

## Contents

- icalendar-sync/ — iCalendar Sync skill for OpenClaw (full CalDAV / iCloud integration)
- README.md — (this file) branch overview, usage and contribution notes
- Other skill directories (if present) — each skill contains its own README, skill.yaml and supporting files

For detailed documentation, examples, API usage and security notes for the calendar skill, see:
- icalendar-sync/README.md

---

## Purpose & Scope

This branch provides:

- A collection of self-contained OpenClaw skills and plugins, ready for evaluation and integration.
- Explicit metadata files so skills can be discovered and registered by ClawHub-style registries.
- Practical examples and runtime guidance for secure credential handling and headless (CI/agent) setup.

Each skill aims to include:
- A human-readable README describing features, requirements and usage.
- A skill.yaml or CLAWHUB_METADATA.yaml containing required metadata and declared environment variables.
- A clear license and change log.

---

## Highlight: icalendar-sync

The primary skill included in this branch is iCalendar Sync — a professional-grade iCloud/CalDAV calendar integration for OpenClaw.

Key points (see icalendar-sync/README.md for the authoritative details):
- Provides bidirectional calendar sync with iCloud via CalDAV.
- Supports event CRUD, recurring rules (RRULE), alarms, multiple calendars and Unicode calendar names (Cyrillic, CJK, Arabic, etc.).
- Includes CLI and Python module interfaces (python -m icalendar_sync).
- Security-oriented: keyring integration, input validation, SSL verification, log filtering and documented storage fallbacks.
- Headless / automated setup options for CI, Docker and OpenClaw agents.

Recommended next step: open icalendar-sync/README.md for complete installation, configuration and API examples.

---

## Repository structure (high level)

- icalendar-sync/
  - README.md — full skill documentation (usage, API, security)
  - src/icalendar_sync/ — implementation modules (calendar client, i18n, translations, CLI entrypoint)
  - skill.yaml, SKILL.md, CLAWHUB_METADATA.yaml — metadata and registry declarations
  - CHANGELOG.md, SECURITY_SCAN_NOTICE.md, BUGFIX_NOTES.md — release and security artefacts
- README.md — branch overview (this file)
- LICENSE — repository license (see skill folders for per-skill license details if present)

---

## Compatibility

- Target OpenClaw: 2.0 and above
- Python: 3.9+ recommended (see individual skill README for exact requirements)
- Platform: Cross-platform. Keyring backends supported on macOS (Keychain), Windows (Credential Manager) and common Linux secret services (GNOME Keyring, KWallet). A plaintext .env fallback is documented for development only.

---

## Installation (example for development)

Clone the parent OpenClaw repo or this repository and install the skill in editable mode to try locally:

```bash
# Clone the repo (or the OpenClaw parent repo if you want the full framework)
git clone https://github.com/h8kxrfp68z-lgtm/iCalendar-Sync.git
cd iCalendar-Sync/icalendar-sync

# Install in editable mode for development
pip install -e .
```

When packaged/published, skills may be available via pip or other distribution channels. Refer to each skill's README for exact packaging instructions.

---

## Quick usage pointers (icalendar-sync)

Refer to icalendar-sync/README.md for the full guide. Common commands:

- Interactive setup:
  icalendar-sync setup

- Headless setup (CI, automation — prefer environment variables or secret managers over CLI passwords):
  icalendar-sync setup --username "user@icloud.com" --password "app-specific-password" --non-interactive

- List calendars:
  icalendar-sync list

- Get events:
  icalendar-sync get --calendar "Work" --days 7

- Create events (JSON input supported):
  icalendar-sync create --calendar "Personal" --json event.json

- Module usage:
  python -m icalendar_sync list

API usage examples and schema definitions are in icalendar-sync/README.md and the code under src/icalendar_sync/.

---

## Credentials & Security

Security is a priority. Skills in this branch should declare required credentials explicitly in metadata files (skill.yaml / CLAWHUB_METADATA.yaml). Typical guidance:

- Preferred storage: OS keyring (Keychain, Credential Manager, Secret Service)
- Development fallback: ~/.openclaw/.env (must be file-permissions restricted, chmod 600). This is for development only and should never be used in production or shared environments.
- Avoid passing secrets on the command line in multi-user systems; use environment variables, Docker secrets or CI secret stores.

Required environment variables for the calendar skill:
- ICLOUD_USERNAME — Apple ID (email)
- ICLOUD_APP_PASSWORD — App-specific password from appleid.apple.com

See icalendar-sync/SECURITY_SCAN_NOTICE.md for the project's security response and risk considerations.

---

## Metadata & Registry

This branch aims to include multiple metadata formats to maximize registry discovery (examples included in icalendar-sync):
- skill.yaml
- SKILL.md
- CLAWHUB_METADATA.yaml
- Additional registry artifacts (clawhub.json, REGISTRY.yaml) where present

If you are integrating a skill into ClawHub or another registry, consult the skill's metadata files for required fields and declared credentials.

---

## Contributing

Contributions are welcome. Please follow these guidelines:

- Open an issue to discuss major changes or feature proposals first.
- Fork the repo and create topic branches for changes.
- Ensure code is linted and tests (if present) pass.
- Update CHANGELOG.md and the skill-level README when adding features or fixing bugs.
- Provide clear metadata (skill.yaml / CLAWHUB_METADATA.yaml) for any new skill added to this branch.
- Respect the repository license; include SPDX headers where appropriate.

Suggested PR checklist:
- README and SKILL.md updated where behavior changes
- Tests added or updated
- Security implications documented if new credentials or network interactions are introduced

---

## Releases & Changelog

See each skill folder for its changelog (e.g., icalendar-sync/CHANGELOG.md) and release notes. This top-level branch collects skill revisions but per-skill versioning is authoritative.

---

## License

Each skill should include a LICENSE or declare its license in the skill metadata. Check the LICENSE file next to the skill folder (e.g., icalendar-sync/LICENSE) for license details. If there is a top-level LICENSE, it applies to repository-wide assets not otherwise licensed.

---

## Support & Reporting Security Issues

- For bugs and feature requests, open an issue in this repository (or the parent OpenClaw repository if more appropriate).
- For security issues, follow the disclosure instructions in the skill's SECURITY.md or SECURITY_SCAN_NOTICE.md file. Do not post sensitive security details in public issues — follow the project's security disclosure policy.

---

This file was updated via GitHub Copilot Chat Assistant.