from datetime import datetime
from typing import List, Dict, Optional
import uuid

class Message:
    def __init__(self, role: str, content: str, timestamp: Optional[datetime] = None):
        self.role = role
        self.content = content
        self.timestamp = timestamp or datetime.now()
    
    def to_dict(self):
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat()
        }

class AgentState:
    def __init__(self, session_id: Optional[str] = None):
        self.session_id = session_id or str(uuid.uuid4())
        self.messages: List[Message] = []
        self.created_at = datetime.now()
        self.last_updated = datetime.now()
        self.context: Dict = {}
    
    def add_message(self, role: str, content: str):
        message = Message(role, content)
        self.messages.append(message)
        self.last_updated = datetime.now()
    
    def get_history(self, limit: Optional[int] = None) -> List[Dict]:
        history = [msg.to_dict() for msg in self.messages]
        if limit:
            return history[-limit:]
        return history
    
    def get_context(self) -> Dict:
        return self.context
    
    def set_context(self, key: str, value):
        self.context[key] = value
        self.last_updated = datetime.now()
    
    def clear(self):
        self.messages = []
        self.context = {}
        self.last_updated = datetime.now()
    
    def to_dict(self):
        return {
            "session_id": self.session_id,
            "messages": self.get_history(),
            "created_at": self.created_at.isoformat(),
            "last_updated": self.last_updated.isoformat(),
            "context": self.context
        }

class SessionManager:
    def __init__(self):
        self.sessions: Dict[str, AgentState] = {}
    
    def create_session(self) -> AgentState:
        state = AgentState()
        self.sessions[state.session_id] = state
        return state
    
    def get_session(self, session_id: str) -> Optional[AgentState]:
        return self.sessions.get(session_id)
    
    def update_session(self, session_id: str, state: AgentState):
        self.sessions[session_id] = state
        state.last_updated = datetime.now()
    
    def delete_session(self, session_id: str):
        if session_id in self.sessions:
            del self.sessions[session_id]
    
    def list_sessions(self) -> List[Dict]:
        return [state.to_dict() for state in self.sessions.values()]
    
    def get_session_count(self) -> int:
        return len(self.sessions)

session_manager = SessionManager()