# ⚠️ Security Warnings for iCalendar Sync v2.2.14

**Last Updated:** February 12, 2026
**Severity Level:** CRITICAL - READ BEFORE USE

---

## 🚨 CRITICAL: Credential Storage

### ✅ RECOMMENDED: OS Keyring (Secure)

**Always use OS keyring for credential storage:**

```bash
# Interactive setup - stores in keyring
icalendar-sync setup
```

This stores your Apple app-specific password in:
- **macOS**: Keychain (encrypted, system-managed)
- **Windows**: Credential Manager (encrypted, system-managed)
- **Linux**: Secret Service - GNOME Keyring or KWallet (encrypted)

**Security:** ✅ Encrypted at rest, managed by OS, protected by user authentication

---

### ❌ DISCOURAGED: CLI Password Flag (Development Only)

The `--password` CLI flag exists for **headless automation** but has security risks:

```bash
# ⚠️  RISKY - password visible in process list and shell history
icalendar-sync setup --username user@icloud.com --password xxxx-xxxx-xxxx-xxxx --non-interactive
```

**Risks:**
- 🔴 Password stored in **shell history** (`~/.bash_history`, `~/.zsh_history`)
- 🔴 Password visible in **process list** (`ps aux`, `top`)
- 🔴 Password visible in **log files** (if command logged)
- 🔴 On multi-user systems, other users may see password

**When to use:**
- ✅ Single-user development environments
- ✅ Temporary testing/debugging
- ✅ CI/CD with proper secret injection (see below)

**When NOT to use:**
- ❌ Multi-user systems (shared servers, VMs)
- ❌ Production environments
- ❌ Systems with shell history enabled
- ❌ Systems with command logging

---

### ⚠️  FALLBACK: Plaintext .env File (High Risk)

If OS keyring is unavailable, credentials can fall back to `~/.openclaw/.env`:

```bash
# File: ~/.openclaw/.env (chmod 0600)
ICLOUD_USERNAME=user@icloud.com
ICLOUD_APP_PASSWORD=xxxx-xxxx-xxxx-xxxx
```

**Risks:**
- 🟡 Credentials stored in **plaintext on disk**
- 🟡 Vulnerable to **disk forensics** if system compromised
- 🟡 Accessible to **any process running as your user**
- 🟡 May be accidentally **copied to backups**

**Mitigations applied:**
- ✅ File permissions enforced: `chmod 0600` (owner read/write only)
- ✅ File location: `~/.openclaw/.env` (hidden, user home)
- ✅ Not created by default (only if keyring unavailable)

**When to use:**
- ✅ Development on headless servers (no GUI for keyring)
- ✅ Minimal Docker containers (without keyring support)
- ✅ CI/CD runners (without Secret Service daemon)

**When NOT to use:**
- ❌ Production environments with user data
- ❌ Multi-tenant systems
- ❌ Systems with untrusted users
- ❌ Any system where keyring CAN be configured

**Better alternatives:**
- ✅ **Docker**: Use Docker secrets (`docker secret create`)
- ✅ **Kubernetes**: Use Kubernetes secrets or external secrets operator
- ✅ **CI/CD**: Use platform secret stores (GitHub Secrets, GitLab CI Variables, etc.)
- ✅ **Cloud**: Use cloud provider secret managers (AWS Secrets Manager, Azure Key Vault, GCP Secret Manager)

---

## 🔐 Apple ID App-Specific Password

**CRITICAL:** You must use an **App-Specific Password**, NOT your main Apple ID password.

### How to generate:

1. Go to: https://appleid.apple.com/account/manage
2. Navigate to: **Security** → **App-Specific Passwords**
3. Click **Generate Password**
4. Label: "OpenClaw iCalendar Sync"
5. Copy the 16-character password: `xxxx-xxxx-xxxx-xxxx`
6. Store it via `icalendar-sync setup` (keyring)

**Why:**
- ✅ Can be revoked independently (doesn't affect main account)
- ✅ Limited scope (only CalDAV access)
- ✅ Doesn't bypass 2FA on main account
- ✅ Can be regenerated if compromised

**Never:**
- ❌ Use your main Apple ID password
- ❌ Share app-specific passwords between services
- ❌ Commit app-specific passwords to version control

---

## 🐳 Docker / Container Security

### ❌ BAD: Environment Variables

```dockerfile
# ❌ INSECURE - visible in docker inspect, logs, etc.
ENV ICLOUD_USERNAME=user@icloud.com
ENV ICLOUD_APP_PASSWORD=xxxx-xxxx-xxxx-xxxx
```

**Risks:**
- 🔴 Visible in `docker inspect`
- 🔴 Visible in orchestrator UIs (Kubernetes dashboard, etc.)
- 🔴 May be logged to container logs
- 🔴 Inherited by child processes

### ✅ GOOD: Docker Secrets

```bash
# Create secrets
echo "user@icloud.com" | docker secret create icloud_username -
echo "xxxx-xxxx-xxxx-xxxx" | docker secret create icloud_password -

# Use in docker-compose.yml
services:
  openclaw:
    image: openclaw:latest
    secrets:
      - icloud_username
      - icloud_password
```

Then read secrets in container:
```bash
export ICLOUD_USERNAME=$(cat /run/secrets/icloud_username)
export ICLOUD_APP_PASSWORD=$(cat /run/secrets/icloud_password)
```

### ✅ GOOD: External Secrets Manager

```yaml
# Example: Kubernetes with External Secrets Operator
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: icalendar-sync-secrets
spec:
  secretStoreRef:
    name: aws-secrets-manager
  target:
    name: icalendar-creds
  data:
    - secretKey: ICLOUD_USERNAME
      remoteRef:
        key: openclaw/icalendar/username
    - secretKey: ICLOUD_APP_PASSWORD
      remoteRef:
        key: openclaw/icalendar/password
```

---

## 🔧 CI/CD Security

### ❌ BAD: Hardcoded Credentials

```yaml
# ❌ INSECURE - visible in logs, repo history
jobs:
  test:
    runs-on: ubuntu-latest
    env:
      ICLOUD_USERNAME: user@icloud.com
      ICLOUD_APP_PASSWORD: xxxx-xxxx-xxxx-xxxx
```

### ✅ GOOD: Platform Secrets

**GitHub Actions:**
```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - name: Run tests
        env:
          ICLOUD_USERNAME: ${{ secrets.ICLOUD_USERNAME }}
          ICLOUD_APP_PASSWORD: ${{ secrets.ICLOUD_PASSWORD }}
        run: pytest tests/
```

**GitLab CI:**
```yaml
test:
  script:
    - export ICLOUD_USERNAME=$ICLOUD_USERNAME
    - export ICLOUD_APP_PASSWORD=$ICLOUD_PASSWORD
    - pytest tests/
  variables:
    ICLOUD_USERNAME:
      vault: production/icalendar/username@secret
    ICLOUD_PASSWORD:
      vault: production/icalendar/password@secret
```

---

## 📋 Security Checklist

Before deploying to production, verify:

- [ ] Using Apple **app-specific password** (NOT main password)
- [ ] Credentials stored in **OS keyring** (macOS/Windows/Linux)
- [ ] `~/.openclaw/.env` file **does NOT exist** (or deleted after keyring setup)
- [ ] Never used `--password` CLI flag on multi-user systems
- [ ] Shell history cleared if `--password` was used: `history -c && history -w`
- [ ] Docker/Kubernetes using **secrets**, not environment variables
- [ ] CI/CD using **platform secrets**, not hardcoded values
- [ ] No credentials committed to **version control** (check `.gitignore`)
- [ ] App-specific password can be **revoked** if compromised
- [ ] Regularly **rotate** app-specific passwords (every 90 days)

---

## 🛡️ Incident Response

### If credentials are compromised:

1. **Revoke immediately:**
   - Go to: https://appleid.apple.com/account/manage
   - Security → App-Specific Passwords
   - Revoke the compromised password

2. **Generate new password:**
   - Create new app-specific password
   - Update via `icalendar-sync setup`

3. **Audit access:**
   - Check iCloud account activity
   - Review recent calendar modifications
   - Check for unauthorized devices in Apple ID settings

4. **Clean up:**
   - Delete `~/.openclaw/.env` if exists
   - Clear shell history: `history -c && history -w`
   - Rotate passwords on other services (if reused)

---

## 📞 Security Contact

If you discover a security vulnerability in this skill:

- **Email:** contact@clawhub.ai
- **GitHub Issues:** https://github.com/h8kxrfp68z-lgtm/iCalendar-Sync/issues (for non-sensitive issues)
- **Private disclosure:** Use GitHub Security Advisories for sensitive vulnerabilities

---

## 📚 References

- [Apple ID App-Specific Passwords](https://support.apple.com/en-us/HT204397)
- [Docker Secrets Documentation](https://docs.docker.com/engine/swarm/secrets/)
- [Kubernetes Secrets Best Practices](https://kubernetes.io/docs/concepts/configuration/secret/)
- [OWASP Secrets Management Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html)

---

**Version:** 2.2.14
**Last Security Review:** February 12, 2026
**Skill Maintainer:** Black_Temple
