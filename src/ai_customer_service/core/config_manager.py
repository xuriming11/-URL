"""
配置管理器
统一管理所有配置
"""

import os
import json
from pathlib import Path
from typing import Any, Dict, Optional
from dotenv import load_dotenv


class ConfigManager:
    """
    统一配置管理器

    支持:
    - .env 文件读取
    - 环境变量
    - 默认值
    - JSON配置
    """

    _instance = None
    _config: Dict[str, Any] = {}
    _loaded = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not ConfigManager._loaded:
            self.load()

    def load(self):
        """加载所有配置"""
        # 加载.env文件
        env_path = Path(".env")
        if env_path.exists():
            load_dotenv(env_path)
        else:
            # 尝试从包目录加载
            package_env = Path(__file__).parent.parent.parent.parent / ".env"
            if package_env.exists():
                load_dotenv(package_env)

        ConfigManager._loaded = True

    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置值

        优先级: 环境变量 > .env > 默认值

        Args:
            key: 配置键
            default: 默认值

        Returns:
            配置值
        """
        # 尝试从环境变量获取
        value = os.getenv(key)
        if value is not None:
            return self._parse_value(value)

        # 返回默认值
        return default

    def _parse_value(self, value: str) -> Any:
        """解析配置值类型"""
        # 布尔值
        if value.lower() in ("true", "yes", "1"):
            return True
        if value.lower() in ("false", "no", "0"):
            return False

        # JSON对象/数组
        if value.startswith("{") or value.startswith("["):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                pass

        # 数字
        try:
            if "." in value:
                return float(value)
            return int(value)
        except ValueError:
            pass

        return value

    def set(self, key: str, value: Any):
        """设置配置值（仅影响内存）"""
        ConfigManager._config[key] = value

    def get_all(self) -> Dict[str, Any]:
        """获取所有配置"""
        return {
            "openai_api_key": self.get("openai_api_key", ""),
            "openai_base_url": self.get("openai_base_url", ""),
            "model_name": self.get("model_name", "gpt-3.5-turbo"),
            "temperature": self.get("temperature", 0.7),
            "max_tokens": self.get("max_tokens", 2000),
            "plugin_dir": self.get("plugin_dir", "plugins"),
            "log_level": self.get("log_level", "INFO"),
        }

    @staticmethod
    def init_config_file():
        """初始化配置文件"""
        env_content = '''# AI客服系统配置文件
# 复制此文件为 .env 并填入您的配置

# ====================
# 必需配置
# ====================

# OpenAI API密钥 (从 https://platform.openai.com 获取)
OPENAI_API_KEY=your-api-key-here

# 或者使用国内代理 (如 硅基流动 / DeepSeek)
# OPENAI_BASE_URL=https://api.deepseek.com/v1

# ====================
# 可选配置
# ====================

# 模型名称 (默认: gpt-3.5-turbo)
MODEL_NAME=gpt-3.5-turbo

# 温度参数 (0-1, 默认: 0.7)
TEMPERATURE=0.7

# 最大Token数 (默认: 2000)
MAX_TOKENS=2000

# 插件目录 (默认: plugins)
PLUGIN_DIR=plugins

# 日志级别 (DEBUG, INFO, WARNING, ERROR)
LOG_LEVEL=INFO
'''

        env_path = Path(".env")
        if not env_path.exists():
            with open(env_path, "w", encoding="utf-8") as f:
                f.write(env_content)
            return True
        return False


# 全局配置实例
config = ConfigManager()
