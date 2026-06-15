"""
AI Customer Service Package
一个基于MCP协议的插件式AI客服系统
"""

__version__ = "1.0.0"
__author__ = "AI Customer Service Team"

from ai_customer_service.core.plugin_interface import PluginInterface, PluginInfo
from ai_customer_service.core.plugin_manager import PluginManager
from ai_customer_service.core.config_manager import ConfigManager

__all__ = [
    "PluginInterface",
    "PluginInfo",
    "PluginManager",
    "ConfigManager",
]
