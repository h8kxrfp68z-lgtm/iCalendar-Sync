"""
Access Control Engine for Multi-Agent Calendar Management

Implements role-based access control (RBAC) and agent permissions.
"""

import logging
from typing import List, Dict, Optional, Set
from dataclasses import dataclass, field
from enum import Enum
import json
import hashlib

logger = logging.getLogger(__name__)


class PrivacyLevel(Enum):
    """Privacy levels for calendar events and calendars"""
    PUBLIC = "public"           # Visible to all agents
    SHARED = "shared"           # Visible to agents with explicit access
    PRIVATE = "private"         # Visible only to owner agent
    MASKED = "masked"          # Visible as busy-block to allowed agents


@dataclass
class AgentPermissions:
    """Defines what calendars and events an agent can access"""
    agent_id: str
    calendars: List[str] = field(default_factory=list)  # Calendar names agent can access
    can_create_events: bool = True
    can_edit_events: bool = True
    can_delete_events: bool = True
    can_view_busy: bool = True  # Can see masked events as busy blocks
    
    def has_calendar_access(self, calendar_name: str) -> bool:
        """Check if agent can access specific calendar"""
        return calendar_name in self.calendars
    
    def can_perform_action(self, action: str) -> bool:
        """Check if agent can perform action"""
        actions = {
            "create": self.can_create_events,
            "edit": self.can_edit_events,
            "delete": self.can_delete_events,
            "view": True,
            "view_busy": self.can_view_busy,
        }
        return actions.get(action, False)


@dataclass
class Calendar:
    """Calendar configuration"""
    name: str
    icloud_name: str
    privacy_level: PrivacyLevel = PrivacyLevel.SHARED
    accessible_by: List[str] = field(default_factory=list)  # Agent IDs


class CalendarVault:
    """
    Multi-agent calendar access control system
    
    Manages:
    - Agent permissions and role-based access
    - Calendar access policies
    - Privacy masking for restricted events
    - Conflict detection across all calendars
    """
    
    def __init__(self, config: Dict):
        """
        Initialize Calendar Vault from config
        
        Args:
            config: Dict with agents and calendars configuration
        """
        self.config = config
        self.agents: Dict[str, AgentPermissions] = {}
        self.calendars: Dict[str, Calendar] = {}
        self._load_configuration()
    
    def _load_configuration(self):
        """Load agents and calendars from config"""
        # Load agents
        for agent_data in self.config.get("agents", []):
            agent = AgentPermissions(
                agent_id=agent_data["id"],
                calendars=agent_data.get("calendars", []),
                can_create_events=agent_data.get("can_create_events", True),
                can_edit_events=agent_data.get("can_edit_events", True),
                can_delete_events=agent_data.get("can_delete_events", True),
                can_view_busy=agent_data.get("can_view_busy", True),
            )
            self.agents[agent.agent_id] = agent
            logger.info(f"Loaded agent: {agent.agent_id} with access to {len(agent.calendars)} calendars")
        
        # Load calendars
        for cal_data in self.config.get("calendars", []):
            calendar = Calendar(
                name=cal_data["name"],
                icloud_name=cal_data.get("icloud_name", cal_data["name"]),
                privacy_level=PrivacyLevel(cal_data.get("privacy_level", "shared")),
                accessible_by=cal_data.get("accessible_by", []),
            )
            self.calendars[calendar.name] = calendar
            logger.info(f"Loaded calendar: {calendar.name} (privacy: {calendar.privacy_level.value})")
    
    def get_accessible_calendars(self, agent_id: str) -> List[str]:
        """Get list of calendars accessible to agent"""
        if agent_id not in self.agents:
            logger.warning(f"Agent {agent_id} not found")
            return []
        
        return self.agents[agent_id].calendars
    
    def can_access_calendar(self, agent_id: str, calendar_name: str) -> bool:
        """Check if agent can access specific calendar"""
        if agent_id not in self.agents:
            return False
        
        return self.agents[agent_id].has_calendar_access(calendar_name)
    
    def get_icloud_calendar_name(self, calendar_name: str) -> Optional[str]:
        """Get iCloud calendar name from vault calendar name"""
        if calendar_name not in self.calendars:
            return None
        return self.calendars[calendar_name].icloud_name
    
    def get_agent_permissions(self, agent_id: str) -> Optional[AgentPermissions]:
        """Get permissions for specific agent"""
        return self.agents.get(agent_id)
    
    def list_agents(self) -> List[str]:
        """List all registered agents"""
        return list(self.agents.keys())
    
    def list_calendars(self, agent_id: Optional[str] = None) -> Dict[str, List[str]]:
        """
        List calendars with privacy info
        
        If agent_id provided, return only accessible calendars
        """
        if agent_id:
            accessible = self.get_accessible_calendars(agent_id)
            return {
                "accessible": accessible,
                "total_calendars": len(self.calendars),
            }
        
        return {name: cal.accessible_by for name, cal in self.calendars.items()}
    
    def validate_access(self, agent_id: str, calendar_name: str, action: str) -> bool:
        """
        Validate if agent can perform action on calendar
        
        Args:
            agent_id: Agent identifier
            calendar_name: Calendar name
            action: Action type (view, create, edit, delete)
        
        Returns:
            True if action is permitted, False otherwise
        """
        # Check agent exists
        if agent_id not in self.agents:
            logger.warning(f"Unknown agent: {agent_id}")
            return False
        
        # Check calendar exists
        if calendar_name not in self.calendars:
            logger.warning(f"Unknown calendar: {calendar_name}")
            return False
        
        # Check agent has access to calendar
        if not self.can_access_calendar(agent_id, calendar_name):
            logger.warning(f"Agent {agent_id} has no access to {calendar_name}")
            return False
        
        # Check agent can perform action
        agent = self.agents[agent_id]
        if not agent.can_perform_action(action):
            logger.warning(f"Agent {agent_id} cannot perform action: {action}")
            return False
        
        return True
    
    @staticmethod
    def from_yaml(yaml_path: str) -> "CalendarVault":
        """Load vault configuration from YAML file"""
        import yaml
        with open(yaml_path, 'r') as f:
            config = yaml.safe_load(f)
        return CalendarVault(config)
    
    @staticmethod
    def from_json(json_path: str) -> "CalendarVault":
        """Load vault configuration from JSON file"""
        with open(json_path, 'r') as f:
            config = json.load(f)
        return CalendarVault(config)
