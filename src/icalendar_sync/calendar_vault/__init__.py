"""
Family Calendar Vault - Multi-Agent Privacy-First Calendar Management

Enables multiple AI agents to manage shared and private calendars with:
- Role-based access control
- Privacy masking for restricted events
- Smart conflict detection without revealing sensitive data
- Multi-provider support (iCloud, Google Calendar, Outlook)
"""

from .access_control import CalendarVault, AgentPermissions
from .privacy_engine import PrivacyMask, PrivacyLevel
from .conflict_resolver import ConflictResolver

__version__ = "3.0.0"
__all__ = [
    "CalendarVault",
    "AgentPermissions", 
    "PrivacyMask",
    "PrivacyLevel",
    "ConflictResolver",
]
