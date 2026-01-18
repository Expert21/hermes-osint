"""
Session Store for Hermes Agent.

Handles saving and loading conversation sessions to disk.
Sessions are stored as JSON files in ~/.hermes/sessions/
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
from dataclasses import asdict

logger = logging.getLogger(__name__)


# SECURITY: Session schema for validation
SESSION_SCHEMA = {
    "required_fields": ["session_id", "messages"],
    "allowed_roles": {"user", "assistant", "tool", "system"},
    "max_messages": 1000,  # Prevent excessively large sessions
    "max_content_length": 100000,  # Per-message content limit
}


class SessionStore:
    """
    Persists agent sessions to disk.
    
    Sessions include:
    - Conversation messages
    - Metadata (model, timestamp, etc.)
    - Context summary if available
    """
    
    DEFAULT_DIR = Path.home() / ".hermes" / "sessions"
    
    def __init__(self, sessions_dir: Optional[Path] = None):
        """
        Initialize the session store.
        
        Args:
            sessions_dir: Custom directory for sessions
        """
        self.sessions_dir = sessions_dir or self.DEFAULT_DIR
        self._ensure_dir()
    
    def _ensure_dir(self):
        """Create sessions directory if needed."""
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
    
    def _session_path(self, session_id: str) -> Path:
        """Get path for a session file."""
        # Sanitize session_id
        safe_id = "".join(c for c in session_id if c.isalnum() or c in "-_")
        return self.sessions_dir / f"{safe_id}.json"
    
    def save(
        self,
        session_id: str,
        messages: List[Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Save a session to disk.
        
        Args:
            session_id: Unique name for the session
            messages: List of AgentMessage objects
            metadata: Optional metadata (model, config, etc.)
            
        Returns:
            True if save successful
        """
        metadata = metadata or {}
        
        # Convert messages to dicts
        message_dicts = []
        for msg in messages:
            if hasattr(msg, '__dict__'):
                msg_dict = {
                    "role": msg.role,
                    "content": msg.content,
                    "name": getattr(msg, "name", None),
                }
                message_dicts.append(msg_dict)
            elif isinstance(msg, dict):
                message_dicts.append(msg)
        
        session_data = {
            "session_id": session_id,
            "saved_at": datetime.now().isoformat(),
            "messages": message_dicts,
            "message_count": len(message_dicts),
            "metadata": metadata
        }
        
        try:
            path = self._session_path(session_id)
            with open(path, "w") as f:
                json.dump(session_data, f, indent=2, default=str)
            logger.info(f"Saved session '{session_id}' to {path}")
            return True
        except Exception as e:
            logger.error(f"Failed to save session: {e}")
            return False
    
    def load(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Load a session from disk.
        
        Args:
            session_id: Name of session to load
            
        Returns:
            Session dict with messages and metadata, or None
        """
        path = self._session_path(session_id)
        
        if not path.exists():
            logger.warning(f"Session '{session_id}' not found")
            return None
        
        try:
            with open(path) as f:
                data = json.load(f)
            
            # SECURITY: Validate session schema
            self._validate_session_schema(data)
            
            logger.info(f"Loaded session '{session_id}' ({data.get('message_count', 0)} messages)")
            return data
        except ValueError as ve:
            logger.error(f"Session validation failed for '{session_id}': {ve}")
            return None
        except Exception as e:
            logger.error(f"Failed to load session: {e}")
            return None
    
    def _validate_session_schema(self, data: Dict[str, Any]) -> None:
        """
        Validate session data against schema.
        
        SECURITY: Prevents malicious session files from injecting
        content into the agent context.
        
        Raises:
            ValueError: If validation fails
        """
        # Check required fields
        for field in SESSION_SCHEMA["required_fields"]:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")
        
        # Validate messages is a list
        messages = data.get("messages", [])
        if not isinstance(messages, list):
            raise ValueError("messages must be a list")
        
        # Check message count limit
        if len(messages) > SESSION_SCHEMA["max_messages"]:
            raise ValueError(f"Too many messages: {len(messages)} exceeds max {SESSION_SCHEMA['max_messages']}")
        
        # Validate each message
        for i, msg in enumerate(messages):
            if not isinstance(msg, dict):
                raise ValueError(f"Message {i} must be a dict")
            
            # Validate role
            role = msg.get("role", "")
            if role not in SESSION_SCHEMA["allowed_roles"]:
                raise ValueError(f"Invalid role in message {i}: '{role}'")
            
            # Validate content length
            content = msg.get("content", "")
            if isinstance(content, str) and len(content) > SESSION_SCHEMA["max_content_length"]:
                raise ValueError(f"Message {i} content too long: {len(content)} chars")
    
    def list_sessions(self) -> List[Dict[str, Any]]:
        """
        List all saved sessions.
        
        Returns:
            List of session info dicts (id, saved_at, message_count)
        """
        sessions = []
        
        for path in self.sessions_dir.glob("*.json"):
            try:
                with open(path) as f:
                    data = json.load(f)
                sessions.append({
                    "session_id": data.get("session_id", path.stem),
                    "saved_at": data.get("saved_at", "unknown"),
                    "message_count": data.get("message_count", 0),
                })
            except Exception:
                continue
        
        # Sort by date, newest first
        sessions.sort(key=lambda x: x.get("saved_at", ""), reverse=True)
        return sessions
    
    def delete(self, session_id: str) -> bool:
        """
        Delete a saved session.
        
        Args:
            session_id: Name of session to delete
            
        Returns:
            True if deleted successfully
        """
        path = self._session_path(session_id)
        
        if not path.exists():
            return False
        
        try:
            path.unlink()
            logger.info(f"Deleted session '{session_id}'")
            return True
        except Exception as e:
            logger.error(f"Failed to delete session: {e}")
            return False
    
    def exists(self, session_id: str) -> bool:
        """Check if a session exists."""
        return self._session_path(session_id).exists()
