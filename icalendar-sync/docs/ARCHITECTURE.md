# Architecture Documentation

**iCalendar Sync for OpenClaw**  
**Version:** 2.2.0

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Component Architecture](#component-architecture)
3. [Security Architecture](#security-architecture)
4. [Data Flow](#data-flow)
5. [Threading Model](#threading-model)
6. [Extension Points](#extension-points)
7. [Performance Considerations](#performance-considerations)

---

## System Overview

### Design Principles

1. **Security First** - All design decisions prioritize security
2. **Zero Trust** - No implicit trust between components
3. **Fail Secure** - Errors deny access rather than grant it
4. **Auditability** - All actions are logged and traceable
5. **Modularity** - Components are loosely coupled
6. **Extensibility** - Easy to add new features

### High-Level Architecture

```
┌──────────────────────────────────────────────┐
│                OpenClaw Core                         │
│  (Agent Manager, Skill Loader, Event Bus)            │
└──────────────────────┬──────────────────────┘
                       │
                       │ Skill API
                       │
┌──────────────────┬─┴──────────────────────────┐
│  CLI Interface  │   iCalendar Sync Skill         │
│  calendar.py    │   (Entry Point)                │
└────────┬───────┘                              │
         │                                       │
         └────────────┬────────────────────────┘
                      │
                      ↓
         ┌──────────────────────────────┐
         │   Security Middleware         │
         │   (Rate Limiter, Validator)  │
         └───────────┬──────────────────┘
                    │
         ┌──────────┬┴───────────┐
         │            │              │
         ↓            ↓              ↓
  ┌───────────┐ ┌─────────────┐ ┌───────────┐
  │ Calendar  │ │   Conflict   │ │  Privacy   │
  │   Vault   │ │   Resolver  │ │  Engine    │
  │  (RBAC)   │ │ (Detection)│ │ (Masking)  │
  └────┬──────┘ └────┬────────┘ └───┬───────┘
       │             │              │
       └─────────┬─┴──────────────┘
                    │
                    ↓
         ┌────────────────────────┐
         │  iCloud Connector       │
         │  (CalDAV Client)        │
         └──────────┬─────────────┘
                    │
                    │ HTTPS/CalDAV
                    │
         ┌──────────┴─────────────┐
         │   iCloud CalDAV API     │
         │   (Apple Servers)       │
         └────────────────────────┘
```

---

## Component Architecture

### 1. Calendar Vault (Access Control)

**File:** `src/icalendar_sync/calendar_vault/access_control.py`

**Responsibilities:**
- Agent authentication and authorization
- Role-Based Access Control (RBAC)
- Calendar-level permissions
- Configuration validation

**Key Classes:**

```python
class CalendarVault:
    agents: Dict[str, AgentPermissions]
    calendars: Dict[str, Calendar]
    _calendar_name_map: Dict[str, str]  # Case-insensitive lookup
    
    def validate_access(agent_id, calendar, action) -> bool
    def get_accessible_calendars(agent_id) -> List[str]
    def can_access_calendar(agent_id, calendar) -> bool
```

**Security Features:**
- Path traversal protection
- Config validation (structure, types, values)
- Case-insensitive calendar names (v2.2.0)
- Safe YAML/JSON loading

**Access Control Matrix:**

```
              │ View │ Create │ Edit │ Delete │ View Busy │
──────────────┼──────┼────────┼──────┼────────┼───────────┤
Admin         │  ✓   │   ✓    │  ✓   │   ✓    │     ✓     │
Editor        │  ✓   │   ✓    │  ✓*  │   ✓*   │     ✓     │
Contributor   │  ✓   │   ✓    │  ✗   │   ✗    │     ✓     │
Viewer        │  ✓   │   ✗    │  ✗   │   ✗    │     ✓     │
Busy-Only     │  ✗   │   ✗    │  ✗   │   ✗    │     ✓     │

* Only own events
```

### 2. Conflict Resolver

**File:** `src/icalendar_sync/calendar_vault/conflict_resolver.py`

**Responsibilities:**
- Detect scheduling conflicts
- Find free time slots
- Calculate busy times
- Handle recurrence rules

**Key Classes:**

```python
class ConflictResolver:
    working_hours: WorkingHours
    timezone: str
    min_buffer_minutes: int = 15
    travel_time_minutes: int = 30
    
    def find_conflicts(events, start, end) -> List[Conflict]
    def find_free_slots(events, start, end, duration) -> List[TimeSlot]
    def check_availability(events, proposed_slot) -> Tuple[bool, Optional[List]]
```

**Conflict Types:**

1. **Hard Conflict** - Direct time overlap
   ```
   Event A: |------|
   Event B:    |------|
   Overlap:    |--|  ← CONFLICT
   ```

2. **Soft Conflict** - No buffer between events
   ```
   Event A: |------|
   Event B:         |------|
   Buffer:         0  ← WARNING
   ```

3. **Travel Conflict** - Insufficient travel time
   ```
   Event A @ Office: |------|
   Event B @ Home:           |------|
   Travel needed: 30 min
   Gap: 15 min  ← CONFLICT
   ```

**DoS Protection (v2.2.0):**
- `MAX_DATE_RANGE_DAYS = 365`
- `MAX_EVENTS_PER_CHECK = 1000`
- Warning logs for large queries

### 3. Privacy Engine

**File:** `src/icalendar_sync/calendar_vault/privacy_engine.py`

**Responsibilities:**
- Event masking based on privacy levels
- Sensitive data filtering
- Agent-specific event views

**Key Classes:**

```python
class PrivacyEngine:
    def mask_event(event, privacy_level) -> Dict
    def filter_events(events, agent_id, calendar_config) -> List[Dict]
    def apply_privacy_rules(events, rules) -> List[Dict]
```

**Privacy Levels:**

| Level | Description | What Agent Sees |
|-------|-------------|----------------|
| `PUBLIC` | Open to all | Full event details |
| `SHARED` | Restricted list | Full details if in `accessible_by` |
| `PRIVATE` | Owner only | "Busy" if not owner |
| `MASKED` | Always hidden | "Busy" block only |

**Masking Rules:**

```python
# Original event
event = {
    "summary": "Doctor Appointment",
    "start": datetime(...),
    "end": datetime(...),
    "location": "Medical Center",
    "description": "Annual checkup",
    "attendees": ["doctor@clinic.com"]
}

# Masked event (PRIVATE/MASKED level)
masked = {
    "summary": "Busy",
    "start": datetime(...),
    "end": datetime(...),
    "busy": True
    # All other fields removed
}
```

### 4. Rate Limiter

**File:** `src/icalendar_sync/calendar_vault/rate_limiter.py`

**Responsibilities:**
- Prevent API abuse
- Track per-agent call rates
- Implement token bucket algorithm

**Implementation:**

```python
class RateLimiter:
    max_calls: int = 10
    time_window: int = 60  # seconds
    _buckets: Dict[str, List[float]]  # agent_id -> timestamps
    
    def check_rate_limit(agent_id: str) -> bool:
        # Token bucket algorithm
        now = time.time()
        window_start = now - self.time_window
        
        # Remove old timestamps
        self._buckets[agent_id] = [
            ts for ts in self._buckets[agent_id]
            if ts > window_start
        ]
        
        # Check if under limit
        if len(self._buckets[agent_id]) < self.max_calls:
            self._buckets[agent_id].append(now)
            return True
        
        return False
```

**Configuration:**

```yaml
rate_limiting:
  enabled: true
  max_calls: 10
  time_window: 60  # seconds
  per_agent: true
```

### 5. iCloud Connector

**File:** `src/icalendar_sync/icloud_connector.py`

**Responsibilities:**
- CalDAV client implementation
- Connection pooling
- SSL/TLS enforcement
- Credential management

**Key Features:**

```python
class iCloudConnector:
    _connection_cache: Dict[str, caldav.DAVClient]
    _cache_lock: threading.Lock
    
    def connect() -> caldav.DAVClient:
        # Thread-safe connection caching
        with self._cache_lock:
            if not self._connection_cache.get(username):
                client = caldav.DAVClient(
                    url="https://caldav.icloud.com",
                    username=username,
                    password=password,
                    ssl_verify_cert=True  # Enforced
                )
                self._connection_cache[username] = client
            return self._connection_cache[username]
```

**SSL/TLS Configuration:**

```python
# SSL verification always enabled
ssl_verify_cert = True  # Cannot be disabled

# Supported protocols
tls_versions = ["TLSv1.2", "TLSv1.3"]

# Certificate validation
cert_validation = "strict"  # Rejects self-signed
```

---

## Security Architecture

### Defense in Depth

iCalendar Sync implements multiple security layers:

```
┌──────────────────────────────────────────────┐
│          Layer 6: Audit Logging                     │
├──────────────────────────────────────────────┤
│          Layer 5: Privacy Masking                   │
├──────────────────────────────────────────────┤
│          Layer 4: Authorization (RBAC)              │
├──────────────────────────────────────────────┤
│          Layer 3: Rate Limiting                     │
├──────────────────────────────────────────────┤
│          Layer 2: Input Validation                  │
├──────────────────────────────────────────────┤
│          Layer 1: Authentication                    │
└──────────────────────────────────────────────┘
```

### Trust Boundaries

```
Untrusted Zone          Trust Boundary          Trusted Zone
│                             │                        │
│  AI Agent Input              │   CalendarVault        │
│  - Commands                  │   - Access Control     │
│  - Parameters                │   - Validation         │
│  - Calendar names            │                        │
│                             │                        │
│                          [VALIDATION]               │
│                          [AUTHORIZATION]            │
│                          [RATE LIMIT]               │
│                             │                        │
│                             │   iCloudConnector      │
│                             │   - Secure API calls   │
│                             │   - SSL/TLS only       │
│                             │                        │
└─────────────────────────────┴────────────────────────┘
```

---

## Data Flow

### Event Creation Flow

```
1. Agent Request
   │
   ↓
2. Rate Limit Check
   │
   ├───> [DENIED] Rate limit exceeded
   │
   ↓
3. Input Validation
   │
   ├───> [DENIED] Invalid input
   │
   ↓
4. Access Control
   │
   ├───> [DENIED] No permission
   │
   ↓
5. Conflict Detection
   │
   ├───> [WARNING] Conflict found
   │
   ↓
6. iCloud API Call
   │
   ├───> [ERROR] API failure
   │
   ↓
7. Success Response
   │
   ↓
8. Audit Log Entry
```

### Event Retrieval Flow

```
1. Agent Request
   │
   ↓
2. Rate Limit Check
   │
   ↓
3. Access Control
   │
   ↓
4. iCloud Sync
   │
   ↓
5. Privacy Filtering
   │
   ├───> PUBLIC events: Full details
   ├───> SHARED events: Check accessible_by
   ├───> PRIVATE events: Mask if not owner
   └───> MASKED events: Always mask
   │
   ↓
6. Return Filtered Events
```

---

## Threading Model

### Connection Caching

```python
class iCloudConnector:
    _connection_cache = {}  # Shared across threads
    _cache_lock = threading.Lock()  # Protects cache
    
    def get_connection(username):
        with self._cache_lock:  # Atomic cache access
            if username not in self._connection_cache:
                self._connection_cache[username] = create_client()
            return self._connection_cache[username]
```

### Thread Safety Guarantees

1. **Connection Cache** - Protected by lock
2. **Rate Limiter** - Per-agent tracking (isolated)
3. **Conflict Resolver** - Stateless (safe)
4. **Privacy Engine** - Deep copy events (safe)

---

## Extension Points

### Adding New Calendar Providers

```python
class BaseCalendarConnector(ABC):
    @abstractmethod
    def connect(self, credentials):
        pass
    
    @abstractmethod
    def get_events(self, calendar, start, end):
        pass
    
    @abstractmethod
    def create_event(self, calendar, event):
        pass

# Implement for Google Calendar
class GoogleCalendarConnector(BaseCalendarConnector):
    def connect(self, credentials):
        # OAuth2 flow
        pass
    
    def get_events(self, calendar, start, end):
        # Google Calendar API
        pass
```

### Custom Privacy Rules

```python
class CustomPrivacyEngine(PrivacyEngine):
    def apply_custom_rule(self, event, rule):
        # Example: Mask events with specific keywords
        if rule.get("keyword_masking"):
            keywords = rule["keywords"]
            if any(kw in event["summary"].lower() for kw in keywords):
                return self.mask_event(event, PrivacyLevel.MASKED)
        return event
```

### Plugin System

```python
# Future: Plugin architecture
class SkillPlugin:
    def on_event_created(self, event):
        # Hook: Post-creation
        pass
    
    def on_conflict_detected(self, conflicts):
        # Hook: Conflict notification
        pass
```

---

## Performance Considerations

### Caching Strategy

1. **Connection Cache** - Reuse CalDAV clients (reduces auth overhead)
2. **Event Cache** - Store recent queries (TTL: 5 minutes)
3. **Calendar List Cache** - Cache available calendars (TTL: 1 hour)

### Optimization Techniques

1. **Batch Operations** - Group API calls
2. **Lazy Loading** - Fetch only when needed
3. **Parallel Queries** - Multiple calendars simultaneously
4. **Compression** - gzip for large responses

### Bottlenecks

1. **Network Latency** - iCloud API is primary bottleneck
2. **Conflict Detection** - O(n²) for n events
3. **Privacy Filtering** - O(n) per event

**Mitigation:**
- Use connection pooling
- Limit date ranges
- Cache frequently accessed data
- Implement pagination

---

**Version:** 2.2.0  
**Last Updated:** February 11, 2026
