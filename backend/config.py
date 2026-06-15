"""
配置文件
管理所有插件和系统的配置
"""

import os
from typing import Dict, Any
from dotenv import load_dotenv
from pydantic import BaseModel


load_dotenv()


class ServerConfig(BaseModel):
    """服务器配置"""
    host: str = os.getenv("SERVER_HOST", "localhost")
    port: int = int(os.getenv("SERVER_PORT", "8000"))
    debug: bool = os.getenv("DEBUG", "False").lower() == "true"


class AIConfig(BaseModel):
    """AI客服配置"""
    api_key: str = os.getenv("OPENAI_API_KEY", "")
    base_url: str = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    model: str = os.getenv("AI_MODEL", "gpt-3.5-turbo")
    temperature: float = float(os.getenv("AI_TEMPERATURE", "0.7"))
    max_tokens: int = int(os.getenv("AI_MAX_TOKENS", "1000"))


class TicketConfig(BaseModel):
    """工单配置"""
    timeout: int = int(os.getenv("TICKET_TIMEOUT", "30"))  # 分钟
    agent_response_time: int = int(os.getenv("AGENT_RESPONSE_TIME", "5"))  # 分钟
    auto_close_time: int = int(os.getenv("AUTO_CLOSE_TIME", "24"))  # 小时


class DatabaseConfig(BaseModel):
    """数据库配置"""
    url: str = os.getenv("DATABASE_URL", "sqlite:///./customer_service.db")


class Config:
    """总配置类"""
    
    def __init__(self):
        self.server = ServerConfig()
        self.ai = AIConfig()
        self.ticket = TicketConfig()
        self.database = DatabaseConfig()
        self.plugins: Dict[str, Dict[str, Any]] = {}
    
    def load_plugin_config(self, plugin_name: str) -> Dict[str, Any]:
        """
        加载插件配置
        
        Args:
            plugin_name: 插件名称
        
        Returns:
            Dict: 插件配置
        """
        # 从环境变量或配置文件加载
        config = {}
        
        # AI客服插件配置
        if plugin_name == "ai_service_plugin":
            config = {
                "api_key": self.ai.api_key,
                "base_url": self.ai.base_url,
                "model": self.ai.model,
                "temperature": self.ai.temperature,
                "max_tokens": self.ai.max_tokens
            }
        
        # 工单插件配置
        elif plugin_name == "ticket_plugin":
            config = {
                "timeout": self.ticket.timeout,
                "agent_response_time": self.ticket.agent_response_time,
                "auto_close_time": self.ticket.auto_close_time
            }
        
        # 存储插件配置
        elif plugin_name == "storage_plugin":
            config = {
                "database_url": self.database.url
            }
        
        return config
    
    def get_all_configs(self) -> Dict[str, Any]:
        """
        获取所有配置
        
        Returns:
            Dict: 所有配置
        """
        return {
            "server": self.server.dict(),
            "ai": self.ai.dict(),
            "ticket": self.ticket.dict(),
            "database": self.database.dict(),
            "plugins": self.plugins
        }


# 创建全局配置实例
config = Config()