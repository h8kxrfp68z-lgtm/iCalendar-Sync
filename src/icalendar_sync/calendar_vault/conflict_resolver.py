"""
Conflict Detection and Resolution Engine
Security hardened version with DoS protection and timezone support.
"""

import logging
from datetime import datetime, date, time, timedelta
from zoneinfo import ZoneInfo
from typing import List, Dict, Optional, Tuple, Set
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

# Security: DoS protection
MAX_DATE_RANGE_DAYS = 365
MAX_EVENTS_PER_CHECK = 1000


class ConflictType(Enum):
    """Types of calendar conflicts"""
    HARD_CONFLICT = "hard_conflict"      # Direct time overlap
    SOFT_CONFLICT = "soft_conflict"      # Adjacent events with no buffer
    TRAVEL_CONFLICT = "travel_conflict"  # Not enough travel time


@dataclass
class WorkingHours:
    """Working hours configuration"""
    start: time
    end: time
    timezone: str = "UTC"
    
    def get_timezone(self) -> ZoneInfo:
        """Get ZoneInfo object for timezone"""
        try:
            return ZoneInfo(self.timezone)
        except Exception as e:
            logger.warning(f"Invalid timezone {self.timezone}, falling back to UTC: {e}")
            return ZoneInfo("UTC")


@dataclass
class TimeSlot:
    """Time slot with start and end times"""
    start: datetime
    end: datetime
    calendar: Optional[str] = None
    event_id: Optional[str] = None
    timezone: str = "UTC"
    
    def __post_init__(self):
        """Ensure datetimes are timezone-aware"""
        tz = self._get_timezone()
        if self.start.tzinfo is None:
            self.start = self.start.replace(tzinfo=tz)
        if self.end.tzinfo is None:
            self.end = self.end.replace(tzinfo=tz)
    
    def _get_timezone(self) -> ZoneInfo:
        """Get ZoneInfo object"""
        try:
            return ZoneInfo(self.timezone)
        except Exception:
            return ZoneInfo("UTC")
    
    def overlaps(self, other: "TimeSlot") -> bool:
        """Check if this slot overlaps with another"""
        return self.start < other.end and other.start < self.end
    
    def contains(self, dt: datetime) -> bool:
        """Check if datetime falls within this slot"""
        return self.start <= dt < self.end
    
    @property
    def duration(self) -> timedelta:
        """Get slot duration"""
        return self.end - self.start
    
    def __hash__(self):
        """Make slot hashable for deduplication"""
        return hash((self.start, self.end, self.calendar, self.event_id))
    
    def __eq__(self, other):
        """Equality for deduplication"""
        if not isinstance(other, TimeSlot):
            return False
        return (self.start == other.start and 
                self.end == other.end and 
                self.calendar == other.calendar and
                self.event_id == other.event_id)


@dataclass
class Conflict:
    """Represents a scheduling conflict"""
    time_slot: TimeSlot
    events: List[Dict]
    calendars: List[str]
    severity: str = "warning"  # warning, error, critical
    
    def __hash__(self):
        """Make conflict hashable for deduplication"""
        # Create deterministic hash regardless of event order
        event_ids = tuple(sorted([e.get('id', str(e)) for e in self.events if e]))
        return hash((self.time_slot, event_ids, tuple(sorted(self.calendars)), self.severity))
    
    def __eq__(self, other):
        """Equality for deduplication"""
        if not isinstance(other, Conflict):
            return False
        # Conflicts are equal if they involve same events regardless of order
        self_ids = set(e.get('id', str(e)) for e in self.events if e)
        other_ids = set(e.get('id', str(e)) for e in other.events if e)
        return (self.time_slot == other.time_slot and 
                self_ids == other_ids and
                set(self.calendars) == set(other.calendars))
    
    def __str__(self):
        return (
            f"Conflict: {len(self.events)} events overlap "
            f"from {self.time_slot.start} to {self.time_slot.end}"
        )


class ConflictResolver:
    """
    Detects and resolves scheduling conflicts
    
    Security features:
    - DoS protection with MAX_DATE_RANGE_DAYS
    - Timezone-aware datetime handling
    - Event deduplication
    """
    
    def __init__(
        self,
        working_hours: Optional[WorkingHours] = None,
        timezone: str = "UTC",
    ):
        """
        Initialize conflict resolver
        
        Args:
            working_hours: Optional working hours for boundary checks
            timezone: Timezone for calculations
        """
        self.working_hours = working_hours or WorkingHours(
            start=time(9, 0),
            end=time(17, 0),
            timezone=timezone
        )
        self.timezone = timezone
        self.min_buffer_minutes = 15  # Minimum buffer between events
        self.travel_time_minutes = 30  # Default travel time
    
    def find_conflicts(
        self,
        events: List[Dict],
        start_date: datetime,
        end_date: datetime,
    ) -> List[Conflict]:
        """
        Find all conflicts in event list within date range
        
        Args:
            events: List of event dictionaries
            start_date: Start of search range
            end_date: End of search range
        
        Returns:
            List of detected conflicts (deduplicated)
            
        Raises:
            ValueError: If date range exceeds MAX_DATE_RANGE_DAYS
        """
        # Security: DoS protection
        if isinstance(start_date, datetime) and isinstance(end_date, datetime):
            date_range_days = (end_date - start_date).days
        else:
            date_range_days = (end_date - start_date).days if hasattr(start_date, 'days') else 0
            
        if date_range_days > MAX_DATE_RANGE_DAYS:
            raise ValueError(
                f"Date range ({date_range_days} days) exceeds maximum "
                f"allowed ({MAX_DATE_RANGE_DAYS} days)"
            )
        
        if len(events) > MAX_EVENTS_PER_CHECK:
            logger.warning(
                f"Event count ({len(events)}) exceeds recommended maximum "
                f"({MAX_EVENTS_PER_CHECK}). Performance may be affected."
            )
        
        conflicts: Set[Conflict] = set()  # Use set for automatic deduplication
        
        # Convert events to time slots
        slots = []
        for event in events:
            if not event.get("start") or not event.get("end"):
                continue
            
            slot = TimeSlot(
                start=event["start"],
                end=event["end"],
                calendar=event.get("calendar"),
                event_id=event.get("id"),
                timezone=event.get("timezone", self.timezone)
            )
            
            # Only include slots in date range
            if slot.start < end_date and slot.end > start_date:
                slots.append((slot, event))
        
        logger.info(
            f"Checking {len(slots)} events for conflicts "
            f"in range {start_date} to {end_date}"
        )
        
        # Check each pair for overlaps
        for i, (slot1, event1) in enumerate(slots):
            overlapping = []
            
            for slot2, event2 in slots[i+1:]:
                if slot1.overlaps(slot2):
                    overlapping.append(event2)
            
            if overlapping:
                conflict = Conflict(
                    time_slot=slot1,
                    events=[event1] + overlapping,
                    calendars=list(set(
                        [event1.get("calendar")] + 
                        [e.get("calendar") for e in overlapping]
                    )),
                    severity=self._assess_severity(event1, overlapping),
                )
                conflicts.add(conflict)  # Set automatically deduplicates
        
        conflicts_list = list(conflicts)
        logger.info(f"Found {len(conflicts_list)} unique conflicts")
        return conflicts_list
    
    def _assess_severity(
        self,
        event1: Dict,
        overlapping: List[Dict],
    ) -> str:
        """Assess conflict severity based on event properties"""
        # Critical if multiple busy events overlap
        busy_count = sum(
            1 for e in [event1] + overlapping 
            if e.get("busy", True)
        )
        
        if busy_count > 2:
            return "critical"
        elif busy_count > 1:
            return "error"
        else:
            return "warning"
    
    def find_free_slots(
        self,
        events: List[Dict],
        start_date: datetime,
        end_date: datetime,
        duration_minutes: int,
        only_working_hours: bool = True,
    ) -> List[TimeSlot]:
        """
        Find free time slots of given duration
        
        Args:
            events: List of events to consider
            start_date: Start of search range
            end_date: End of search range
            duration_minutes: Required slot duration in minutes
            only_working_hours: Only return slots within working hours
        
        Returns:
            List of free time slots
        """
        # Security: DoS protection
        date_range_days = (end_date - start_date).days
        if date_range_days > MAX_DATE_RANGE_DAYS:
            raise ValueError(
                f"Date range ({date_range_days} days) exceeds maximum "
                f"allowed ({MAX_DATE_RANGE_DAYS} days)"
            )
        
        required_duration = timedelta(minutes=duration_minutes)
        free_slots = []
        
        # Get all busy time slots
        busy_slots = self._get_busy_slots(events, start_date, end_date)
        
        # Sort by start time
        busy_slots.sort(key=lambda s: s.start)
        
        # Find gaps between busy slots
        current_time = start_date
        
        for busy_slot in busy_slots:
            # Check gap before this busy slot
            if current_time < busy_slot.start:
                gap_duration = busy_slot.start - current_time
                
                if gap_duration >= required_duration:
                    # Found a free slot
                    slot = TimeSlot(
                        start=current_time,
                        end=busy_slot.start,
                        timezone=self.timezone
                    )
                    
                    if only_working_hours:
                        # Split into working hour segments
                        free_slots.extend(
                            self._split_by_working_hours(slot, required_duration)
                        )
                    else:
                        free_slots.append(slot)
            
            # Move current time to end of busy slot
            current_time = max(current_time, busy_slot.end)
        
        # Check remaining time until end_date
        if current_time < end_date:
            gap_duration = end_date - current_time
            
            if gap_duration >= required_duration:
                slot = TimeSlot(start=current_time, end=end_date, timezone=self.timezone)
                
                if only_working_hours:
                    free_slots.extend(
                        self._split_by_working_hours(slot, required_duration)
                    )
                else:
                    free_slots.append(slot)
        
        return free_slots
    
    def _get_busy_slots(
        self,
        events: List[Dict],
        start_date: datetime,
        end_date: datetime,
    ) -> List[TimeSlot]:
        """Extract busy time slots from events"""
        busy_slots = []
        
        for event in events:
            if not event.get("start") or not event.get("end"):
                continue
            
            # Skip non-busy events
            if not event.get("busy", True):
                continue
            
            slot = TimeSlot(
                start=max(event["start"], start_date),
                end=min(event["end"], end_date),
                calendar=event.get("calendar"),
                event_id=event.get("id"),
                timezone=event.get("timezone", self.timezone)
            )
            
            # Only include if within date range
            if slot.start < slot.end:
                busy_slots.append(slot)
        
        return busy_slots
    
    def _split_by_working_hours(
        self,
        slot: TimeSlot,
        min_duration: timedelta,
    ) -> List[TimeSlot]:
        """Split time slot into working hour segments with timezone support"""
        segments = []
        tz = self.working_hours.get_timezone()
        
        current_date = slot.start.date()
        end_date = slot.end.date()
        
        # Security: Limit iteration range
        days_diff = (end_date - current_date).days
        if days_diff > MAX_DATE_RANGE_DAYS:
            logger.warning(f"Date range too large in _split_by_working_hours, limiting to {MAX_DATE_RANGE_DAYS} days")
            end_date = current_date + timedelta(days=MAX_DATE_RANGE_DAYS)
        
        while current_date <= end_date:
            # Working hours for this day (timezone-aware)
            day_start = datetime.combine(
                current_date,
                self.working_hours.start,
                tzinfo=tz
            )
            day_end = datetime.combine(
                current_date,
                self.working_hours.end,
                tzinfo=tz
            )
            
            # Intersect with slot
            segment_start = max(slot.start, day_start)
            segment_end = min(slot.end, day_end)
            
            # Check if segment is long enough
            if segment_start < segment_end:
                duration = segment_end - segment_start
                if duration >= min_duration:
                    segments.append(TimeSlot(
                        start=segment_start,
                        end=segment_end,
                        timezone=self.timezone
                    ))
            
            current_date += timedelta(days=1)
        
        return segments
    
    def get_busy_times(
        self,
        events: List[Dict],
        start_date: datetime,
        end_date: datetime,
        merge_adjacent: bool = True,
    ) -> List[TimeSlot]:
        """
        Get all busy times from events
        
        Args:
            events: List of events
            start_date: Start of range
            end_date: End of range
            merge_adjacent: Merge adjacent/overlapping busy slots
        
        Returns:
            List of busy time slots
        """
        busy_slots = self._get_busy_slots(events, start_date, end_date)
        
        if not merge_adjacent:
            return busy_slots
        
        # Merge overlapping/adjacent slots
        if not busy_slots:
            return []
        
        busy_slots.sort(key=lambda s: s.start)
        merged = [busy_slots[0]]
        
        for slot in busy_slots[1:]:
            last = merged[-1]
            
            # Check if overlapping or adjacent (within 5 minutes)
            if slot.start <= last.end + timedelta(minutes=5):
                # Merge slots
                merged[-1] = TimeSlot(
                    start=last.start,
                    end=max(last.end, slot.end),
                    timezone=self.timezone
                )
            else:
                merged.append(slot)
        
        return merged
    
    def check_availability(
        self,
        events: List[Dict],
        proposed_slot: TimeSlot,
    ) -> Tuple[bool, Optional[List[Dict]]]:
        """
        Check if proposed time slot is available
        
        Args:
            events: Existing events to check against
            proposed_slot: Proposed time slot
        
        Returns:
            Tuple of (is_available, conflicting_events)
        """
        conflicting = []
        
        for event in events:
            if not event.get("start") or not event.get("end"):
                continue
            
            event_slot = TimeSlot(
                start=event["start"],
                end=event["end"],
                timezone=event.get("timezone", self.timezone)
            )
            
            if proposed_slot.overlaps(event_slot):
                conflicting.append(event)
        
        return (len(conflicting) == 0, conflicting if conflicting else None)
