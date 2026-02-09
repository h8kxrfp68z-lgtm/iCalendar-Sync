"""
Privacy Engine - Masking and encryption for sensitive calendar data
Security hardened version with deepcopy.
"""

import logging
from copy import deepcopy
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
from datetime import datetime

logger = logging.getLogger(__name__)


class PrivacyLevel(Enum):
    """Privacy levels for events"""
    PUBLIC = "public"       # Visible to all
    SHARED = "shared"       # Visible to specific agents
    PRIVATE = "private"     # Visible only to owner
    MASKED = "masked"       # Shown as busy block only


@dataclass
class PrivacyMask:
    """Privacy masking for events"""
    level: PrivacyLevel
    masked_summary: str = "🔒 Private Event"
    masked_description: Optional[str] = None
    show_time: bool = True
    show_busy_status: bool = True
    show_location: bool = False
    show_attendees: bool = False
    show_details: bool = False


class PrivacyEngine:
    """
    Applies privacy masking to events based on access control
    
    Security: Uses deepcopy to prevent mutation of original events
    """
    
    # Default masks by privacy level
    DEFAULT_MASKS = {
        PrivacyLevel.PUBLIC: PrivacyMask(
            level=PrivacyLevel.PUBLIC,
            masked_summary=None,
            show_time=True,
            show_busy_status=True,
            show_location=True,
            show_attendees=True,
            show_details=True,
        ),
        PrivacyLevel.SHARED: PrivacyMask(
            level=PrivacyLevel.SHARED,
            masked_summary=None,
            show_time=True,
            show_busy_status=True,
            show_location=True,
            show_attendees=True,
            show_details=True,
        ),
        PrivacyLevel.PRIVATE: PrivacyMask(
            level=PrivacyLevel.PRIVATE,
            masked_summary="🔒 Private Event",
            show_time=False,
            show_busy_status=False,
            show_location=False,
            show_attendees=False,
            show_details=False,
        ),
        PrivacyLevel.MASKED: PrivacyMask(
            level=PrivacyLevel.MASKED,
            masked_summary="🔒 Busy",
            show_time=True,
            show_busy_status=True,
            show_location=False,
            show_attendees=False,
            show_details=False,
        ),
    }
    
    def __init__(self):
        self.custom_masks: Dict[str, PrivacyMask] = {}
    
    def apply_privacy_mask(
        self,
        event: Dict[str, Any],
        privacy_level: PrivacyLevel,
        custom_mask: Optional[PrivacyMask] = None,
    ) -> Dict[str, Any]:
        """
        Apply privacy mask to event
        
        Args:
            event: Event dictionary with standard fields (summary, description, etc)
            privacy_level: Privacy level to apply
            custom_mask: Optional custom mask instead of default
        
        Returns:
            Masked event dictionary (deep copy, original unchanged)
        """
        mask = custom_mask or self.DEFAULT_MASKS.get(privacy_level)
        if not mask:
            logger.warning(f"No mask found for privacy level: {privacy_level}")
            return deepcopy(event)
        
        # SECURITY: Use deepcopy to prevent mutation of original event
        masked_event = deepcopy(event)
        
        # Apply mask rules
        if mask.masked_summary:
            masked_event["summary"] = mask.masked_summary
        
        if not mask.show_details:
            masked_event.pop("description", None)
        
        if not mask.show_location:
            masked_event.pop("location", None)
        
        if not mask.show_attendees:
            masked_event.pop("attendees", None)
        
        if not mask.show_time:
            # Remove time info for maximum privacy
            masked_event.pop("start", None)
            masked_event.pop("end", None)
        
        # Add privacy marker
        masked_event["_privacy_level"] = privacy_level.value
        masked_event["_is_masked"] = True
        
        return masked_event
    
    def apply_agent_mask(
        self,
        event: Dict[str, Any],
        agent_has_access: bool,
        privacy_level: PrivacyLevel,
    ) -> Dict[str, Any]:
        """
        Apply appropriate mask based on agent access
        
        Args:
            event: Event dictionary
            agent_has_access: Whether agent has direct access to calendar
            privacy_level: Event privacy level
        
        Returns:
            Masked or unmasked event (always a copy)
        """
        if agent_has_access:
            # Agent has access, return copy of full event
            return deepcopy(event)
        
        # Agent doesn't have access, apply privacy mask
        if privacy_level in (PrivacyLevel.PRIVATE, PrivacyLevel.MASKED):
            return self.apply_privacy_mask(event, privacy_level)
        
        # For shared/public, return copy with full details
        return deepcopy(event)
    
    def get_busy_block(
        self,
        event: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Get event as busy block without details
        
        Useful for showing that time is occupied without revealing details
        """
        return {
            "summary": "🔒 Busy",
            "start": event.get("start"),
            "end": event.get("end"),
            "busy": True,
            "_is_busy_block": True,
        }
    
    def register_custom_mask(
        self,
        mask_name: str,
        mask: PrivacyMask,
    ):
        """Register custom privacy mask"""
        self.custom_masks[mask_name] = mask
        logger.info(f"Registered custom mask: {mask_name}")
    
    def get_custom_mask(self, mask_name: str) -> Optional[PrivacyMask]:
        """Get registered custom mask"""
        return self.custom_masks.get(mask_name)
