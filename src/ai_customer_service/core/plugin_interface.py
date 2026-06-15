"""
插件基础接口定义
所有插件必须实现此接口
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from pydantic import BaseModel


class PluginInfo(BaseModel):
    """插件信息模型"""
    name: str
    version: str
    description: str
    author: str = ""
    dependencies: List[str] = []
    enabled: bool = True


class PluginInterface(ABC):
    """插件基础接口"""

    @abstractmethod
    def initialize(self, config: Dict[str, Any]) -> bool:
        """
        初始化插件

        Args:
            config: 插件配置字典

        Returns:
            bool: 初始化是否成功
        """
        pass

    @abstractmethod
    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行插件功能

        Args:
            input_data: 输入数据

        Returns:
            Dict[str, Any]: 输出结果
        """
        pass

    @abstractmethod
    def shutdown(self) -> bool:
        """
        关闭插件

        Returns:
            bool: 关闭是否成功
        """
        pass

    @abstractmethod
    def get_info(self) -> PluginInfo:
        """
        获取插件信息

        Returns:
            PluginInfo: 插件信息对象
        """
        pass

    def health_check(self) -> bool:
        """
        健康检查

        Returns:
            bool: 插件是否健康
        """
        return True

    def get_dependencies(self) -> List[str]:
        """
        获取插件依赖

        Returns:
            List[str]: 依赖列表
        """
        return []

    def validate_dependencies(self) -> tuple[bool, List[str]]:
        """
        验证依赖是否满足

        Returns:
            (是否满足, 缺失的依赖列表)
        """
        missing = []
        for dep in self.get_dependencies():
            try:
                __import__(dep)
            except ImportError:
                missing.append(dep)
        return len(missing) == 0, missing
