"""
Plugins包初始化
"""

from backend.plugins.ai_service_plugin import AIServicePlugin
from backend.plugins.ticket_plugin import TicketPlugin

__all__ = ["AIServicePlugin", "TicketPlugin"]