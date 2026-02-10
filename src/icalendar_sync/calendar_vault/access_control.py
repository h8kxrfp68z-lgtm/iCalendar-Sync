"""
Access Control Engine for Multi-Agent Calendar Management

Implements role-based access control (RBAC) and agent permissions.
Security hardened version with case-insensitive calendar lookup.
"""

import logging
import os
from pathlib import Path
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
        """Check if agent can access specific calendar (case-insensitive)"""
        normalized = calendar_name.strip().lower()
        return normalized in [c.strip().lower() for c in self.calendars]
    
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


class ConfigValidationError(ValueError):
    """Raised when configuration validation fails"""
    pass


class PathValidationError(ValueError):
    """Raised when path validation fails"""
    pass


class CalendarVault:
    """
    Multi-agent calendar access control system
    
    Manages:
    - Agent permissions and role-based access
    - Calendar access policies
    - Privacy masking for restricted events
    - Conflict detection across all calendars
    
    Security features:
    - Path traversal protection
    - Configuration validation
    - Safe YAML/JSON loading
    - Case-insensitive calendar name lookup
    """
    
    def __init__(self, config: Dict):
        """
        Initialize Calendar Vault from config
        
        Args:
            config: Dict with agents and calendars configuration
            
        Raises:
            ConfigValidationError: If config structure is invalid
        """
        self.config = config
        self.agents: Dict[str, AgentPermissions] = {}
        self.calendars: Dict[str, Calendar] = {}
        self._calendar_name_map: Dict[str, str] = {}  # lowercase -> original
        self._validate_config()
        self._load_configuration()
    
    def _normalize_calendar_name(self, name: str) -> str:
        """
        Normalize calendar name to lowercase for case-insensitive comparison
        
        Args:
            name: Calendar name
        
        Returns:
            Normalized (lowercase) calendar name
        """
        return name.strip().lower()
    
    def _validate_config(self):
        """Validate configuration structure"""
        if not isinstance(self.config, dict):
            raise ConfigValidationError("Config must be a dictionary")
        
        if 'agents' not in self.config:
            raise ConfigValidationError("Missing 'agents' key in config")
        
        if 'calendars' not in self.config:
            raise ConfigValidationError("Missing 'calendars' key in config")
        
        if not isinstance(self.config['agents'], list):
            raise ConfigValidationError("'agents' must be a list")
        
        if not isinstance(self.config['calendars'], list):
            raise ConfigValidationError("'calendars' must be a list")
        
        # Validate agent structure
        for i, agent in enumerate(self.config['agents']):
            if not isinstance(agent, dict):
                raise ConfigValidationError(f"Agent {i} must be a dictionary")
            if 'id' not in agent:
                raise ConfigValidationError(f"Agent {i} missing 'id' field")
            if not isinstance(agent.get('calendars', []), list):
                raise ConfigValidationError(f"Agent {i} 'calendars' must be a list")
        
        # Validate calendar structure
        for i, cal in enumerate(self.config['calendars']):
            if not isinstance(cal, dict):
                raise ConfigValidationError(f"Calendar {i} must be a dictionary")
            if 'name' not in cal:
                raise ConfigValidationError(f"Calendar {i} missing 'name' field")
            if 'privacy_level' in cal and cal['privacy_level'] not in ['public', 'shared', 'private', 'masked']:
                raise ConfigValidationError(f"Calendar {i} has invalid privacy_level")
    
    def _load_configuration(self):
        """Load agents and calendars from config with case-insensitive names"""
        # Load agents (with normalized calendar names)
        for agent_data in self.config.get("agents", []):
            normalized_calendars = [
                self._normalize_calendar_name(cal) 
                for cal in agent_data.get("calendars", [])
            ]
            agent = AgentPermissions(
                agent_id=agent_data["id"],
                calendars=normalized_calendars,
                can_create_events=agent_data.get("can_create_events", True),
                can_edit_events=agent_data.get("can_edit_events", True),
                can_delete_events=agent_data.get("can_delete_events", True),
                can_view_busy=agent_data.get("can_view_busy", True),
            )
            self.agents[agent.agent_id] = agent
            logger.info(f"Loaded agent: {agent.agent_id} with access to {len(agent.calendars)} calendars")
        
        # Load calendars (with normalization)
        for cal_data in self.config.get("calendars", []):
            original_name = cal_data["name"]
            normalized_name = self._normalize_calendar_name(original_name)
            
            calendar = Calendar(
                name=normalized_name,
                icloud_name=cal_data.get("icloud_name", original_name),
                privacy_level=PrivacyLevel(cal_data.get("privacy_level", "shared")),
                accessible_by=cal_data.get("accessible_by", []),
            )
            self.calendars[normalized_name] = calendar
            self._calendar_name_map[normalized_name] = original_name
            logger.info(f"Loaded calendar: {original_name} (privacy: {calendar.privacy_level.value})")
    
    @staticmethod
    def _validate_path(file_path: str, allowed_dir: Optional[str] = None) -> Path:
        """
        Validate file path to prevent path traversal attacks
        
        Args:
            file_path: Path to validate
            allowed_dir: Optional base directory to restrict access to
            
        Returns:
            Validated Path object
            
        Raises:
            PathValidationError: If path is invalid or outside allowed directory
        """
        try:
            # Convert to Path and resolve to absolute path
            path = Path(file_path).resolve()
            
            # Check if file exists
            if not path.exists():
                raise PathValidationError(f"File not found: {file_path}")
            
            # Check if it's a file (not directory)
            if not path.is_file():
                raise PathValidationError(f"Path is not a file: {file_path}")
            
            # Check for path traversal patterns
            if '..' in str(file_path):
                raise PathValidationError("Path traversal detected: '..' not allowed")
            
            # If allowed_dir is specified, verify path is within it
            if allowed_dir:
                allowed_path = Path(allowed_dir).resolve()
                if not str(path).startswith(str(allowed_path)):
                    raise PathValidationError(
                        f"Path {file_path} is outside allowed directory {allowed_dir}"
                    )
            
            return path
            
        except (OSError, RuntimeError) as e:
            raise PathValidationError(f"Invalid path: {e}")
    
    def get_accessible_calendars(self, agent_id: str) -> List[str]:
        """Get list of calendars accessible to agent"""
        if agent_id not in self.agents:
            logger.warning(f"Agent {agent_id} not found")
            return []
        
        return self.agents[agent_id].calendars
    
    def can_access_calendar(self, agent_id: str, calendar_name: str) -> bool:
        """Check if agent can access specific calendar (case-insensitive)"""
        if agent_id not in self.agents:
            return False
        
        normalized_name = self._normalize_calendar_name(calendar_name)
        return self.agents[agent_id].has_calendar_access(normalized_name)
    
    def get_icloud_calendar_name(self, calendar_name: str) -> Optional[str]:
        """Get iCloud calendar name from vault calendar name (case-insensitive)"""
        normalized_name = self._normalize_calendar_name(calendar_name)
        if normalized_name not in self.calendars:
            return None
        return self.calendars[normalized_name].icloud_name
    
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
        Validate if agent can perform action on calendar (case-insensitive)
        
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
        
        # Check calendar exists (case-insensitive)
        normalized_name = self._normalize_calendar_name(calendar_name)
        if normalized_name not in self.calendars:
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
    def from_yaml(yaml_path: str, allowed_dir: Optional[str] = None) -> "CalendarVault":
        """
        Load vault configuration from YAML file
        
        Args:
            yaml_path: Path to YAML config file
            allowed_dir: Optional directory to restrict file access to
            
        Returns:
            CalendarVault instance
            
        Raises:
            PathValidationError: If path is invalid
            ConfigValidationError: If config structure is invalid
        """
        import yaml
        
        # Validate path
        validated_path = CalendarVault._validate_path(yaml_path, allowed_dir)
        
        try:
            with open(validated_path, 'r') as f:
                config = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ConfigValidationError(f"Invalid YAML: {e}")
        except OSError as e:
            raise ConfigValidationError(f"Cannot read file: {e}")
        
        return CalendarVault(config)
    
    @staticmethod
    def from_json(json_path: str, allowed_dir: Optional[str] = None) -> "CalendarVault":
        """
        Load vault configuration from JSON file
        
        Args:
            json_path: Path to JSON config file
            allowed_dir: Optional directory to restrict file access to
            
        Returns:
            CalendarVault instance
            
        Raises:
            PathValidationError: If path is invalid
            ConfigValidationError: If config structure is invalid
        """
        # Validate path
        validated_path = CalendarVault._validate_path(json_path, allowed_dir)
        
        try:
            with open(validated_path, 'r') as f:
                config = json.load(f)
        except json.JSONDecodeError as e:
            raise ConfigValidationError(f"Invalid JSON: {e}")
        except OSError as e:
            raise ConfigValidationError(f"Cannot read file: {e}")
        
        return CalendarVault(config)
