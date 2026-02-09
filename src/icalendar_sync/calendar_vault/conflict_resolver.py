"""
Conflict Resolver - Find free slots and detect conflicts across multi-agent calendars
"""

import logging
from typing import List, Dict, Tuple, Optional, Set
from datetime import datetime, timedelta
from dataclasses import dataclass
from collections import defaultdict

logger = logging.getLogger(__name__)


@dataclass
class TimeSlot:
    """Time slot with start and end times"""
    start: datetime
    end: datetime
    calendar: Optional[str] = None
    event_id: Optional[str] = None
    
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


@dataclass
class Conflict:
    """Represents a scheduling conflict"""
    time_slot: TimeSlot
    events: List[Dict]
    calendars: List[str]
    severity: str = "warning"  # warning, error, critical
    
    def __str__(self):
        return (
            f"Conflict: {len(self.events)} events overlap "
            f"from {self.time_slot.start} to {self.time_slot.end}"
        )


class ConflictResolver:
    """
    Detect conflicts and find free slots across calendars
    
    Features:
    - Multi-calendar conflict detection
    - Privacy-aware busy time checking
    - Free slot finding with duration constraints
    - Working hours consideration
    """
    
    def __init__(
        self,
        working_hours_start: int = 9,
        working_hours_end: int = 18,
        timezone: str = "UTC",
    ):
        """
        Initialize conflict resolver
        
        Args:
            working_hours_start: Start of working hours (24h format)
            working_hours_end: End of working hours (24h format)
            timezone: Timezone for calculations
        """
        self.working_hours_start = working_hours_start
        self.working_hours_end = working_hours_end
        self.timezone = timezone
    
    def find_conflicts(
        self,
        events: List[Dict],
        start_date: datetime,
        end_date: datetime,
    ) -> List[Conflict]:
        """
        Find all conflicts in events within date range
        
        Args:
            events: List of event dictionaries
            start_date: Start of search range
            end_date: End of search range
        
        Returns:
            List of detected conflicts
        """
        conflicts = []
        
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
            )
            
            # Only include slots in date range
            if slot.start < end_date and slot.end > start_date:
                slots.append((slot, event))
        
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
                conflicts.append(conflict)
        
        return conflicts
    
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
                slot = TimeSlot(start=current_time, end=end_date)
                
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
        """Split time slot into working hour segments"""
        segments = []
        current_date = slot.start.date()
        end_date = slot.end.date()
        
        while current_date <= end_date:
            # Working hours for this day
            day_start = datetime.combine(
                current_date,
                datetime.min.time().replace(hour=self.working_hours_start)
            )
            day_end = datetime.combine(
                current_date,
                datetime.min.time().replace(hour=self.working_hours_end)
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
            )
            
            if proposed_slot.overlaps(event_slot):
                conflicting.append(event)
        
        return (len(conflicting) == 0, conflicting if conflicting else None)
