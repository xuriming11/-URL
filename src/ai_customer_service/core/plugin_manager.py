"""
插件管理器
负责插件的注册、加载、卸载和生命周期管理
支持插件自动发现
"""

import logging
import importlib
import inspect
from pathlib import Path
from typing import Dict, List, Optional, Type, Callable

from ai_customer_service.core.plugin_interface import PluginInterface, PluginInfo

logger = logging.getLogger(__name__)


class PluginManager:
    """
    插件管理器

    功能:
    - 插件注册/注销
    - 插件初始化/关闭
    - 插件自动发现
    - 插件状态管理
    """

    def __init__(self, plugin_dir: str = None):
        self.plugins: Dict[str, PluginInterface] = {}
        self.plugin_configs: Dict[str, Dict] = {}
        self.plugin_status: Dict[str, str] = {}  # registered, initialized, running, shutdown, disabled
        self.plugin_dir = plugin_dir or "plugins"

    def discover_plugins(self) -> List[str]:
        """
        自动发现插件

        从插件目录扫描所有 *_plugin.py 文件
        自动导入并注册实现了PluginInterface的类

        Returns:
            List[str]: 发现的插件名称列表
        """
        discovered = []
        plugin_path = Path(self.plugin_dir)

        if not plugin_path.exists():
            logger.warning(f"插件目录不存在: {self.plugin_dir}")
            return discovered

        # 扫描插件目录
        for file_path in plugin_path.glob("*_plugin.py"):
            module_name = file_path.stem

            try:
                # 动态导入模块
                spec = importlib.util.spec_from_file_location(module_name, file_path)
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)

                    # 查找实现了PluginInterface的类
                    for name, obj in inspect.getmembers(module, inspect.isclass):
                        if (issubclass(obj, PluginInterface) and
                            obj is not PluginInterface and
                            not name.startswith('_')):

                            # 注册插件
                            plugin_name = name.lower().replace('plugin', '').replace('_', '')
                            if not plugin_name.endswith('_plugin'):
                                plugin_name = f"{name.lower()}_plugin"

                            if plugin_name not in self.plugins:
                                self.register_plugin(
                                    plugin_name,
                                    obj(),
                                    config=self._load_plugin_config(plugin_name)
                                )
                                discovered.append(plugin_name)
                                logger.info(f"自动发现插件: {plugin_name} ({name})")

            except Exception as e:
                logger.error(f"加载插件 {module_name} 失败: {e}")

        return discovered

    def _load_plugin_config(self, plugin_name: str) -> Dict:
        """加载插件配置"""
        from ai_customer_service.core.config_manager import config

        plugin_config_key = f"{plugin_name.upper().replace('_', '_')}_CONFIG"
        config_str = config.get(plugin_config_key, "{}")

        try:
            import json
            return json.loads(config_str)
        except:
            return {}

    def register_plugin(
        self,
        plugin_name: str,
        plugin: PluginInterface,
        config: Dict = None
    ) -> bool:
        """
        注册插件

        Args:
            plugin_name: 插件名称
            plugin: 插件实例
            config: 插件配置

        Returns:
            bool: 注册是否成功
        """
        try:
            if plugin_name in self.plugins:
                logger.warning(f"插件 {plugin_name} 已存在，将被替换")

            self.plugins[plugin_name] = plugin
            self.plugin_configs[plugin_name] = config or {}
            self.plugin_status[plugin_name] = "registered"

            logger.info(f"插件 {plugin_name} 注册成功")
            return True

        except Exception as e:
            logger.error(f"注册插件 {plugin_name} 失败: {e}")
            return False

    def unregister_plugin(self, plugin_name: str) -> bool:
        """
        注销插件

        Args:
            plugin_name: 插件名称

        Returns:
            bool: 注销是否成功
        """
        if plugin_name not in self.plugins:
            logger.error(f"插件 {plugin_name} 未注册")
            return False

        try:
            # 如果插件在运行，先关闭
            if self.plugin_status.get(plugin_name) == "running":
                self.shutdown_plugin(plugin_name)

            del self.plugins[plugin_name]
            del self.plugin_configs[plugin_name]
            del self.plugin_status[plugin_name]

            logger.info(f"插件 {plugin_name} 已注销")
            return True

        except Exception as e:
            logger.error(f"注销插件 {plugin_name} 失败: {e}")
            return False

    def initialize_plugin(self, plugin_name: str) -> bool:
        """
        初始化插件

        Args:
            plugin_name: 插件名称

        Returns:
            bool: 初始化是否成功
        """
        if plugin_name not in self.plugins:
            logger.error(f"插件 {plugin_name} 未注册")
            return False

        try:
            plugin = self.plugins[plugin_name]
            config = self.plugin_configs.get(plugin_name, {})

            # 检查依赖
            valid, missing = plugin.validate_dependencies()
            if not valid:
                logger.error(f"插件 {plugin_name} 依赖缺失: {missing}")
                return False

            # 执行初始化
            success = plugin.initialize(config)

            if success:
                self.plugin_status[plugin_name] = "initialized"
                logger.info(f"插件 {plugin_name} 初始化成功")
            else:
                logger.error(f"插件 {plugin_name} 初始化失败")

            return success

        except Exception as e:
            logger.error(f"初始化插件 {plugin_name} 失败: {e}")
            return False

    def execute_plugin(
        self,
        plugin_name: str,
        input_data: Dict
    ) -> Optional[Dict]:
        """
        执行插件

        Args:
            plugin_name: 插件名称
            input_data: 输入数据

        Returns:
            Optional[Dict]: 执行结果
        """
        if plugin_name not in self.plugins:
            logger.error(f"插件 {plugin_name} 未注册")
            return None

        plugin = self.plugins[plugin_name]

        if self.plugin_status.get(plugin_name) != "initialized":
            if self.plugin_status.get(plugin_name) != "running":
                logger.error(f"插件 {plugin_name} 未初始化")
                return None

        try:
            # 标记为运行中
            self.plugin_status[plugin_name] = "running"

            # 执行插件
            result = plugin.execute(input_data)
            return result

        except Exception as e:
            logger.error(f"执行插件 {plugin_name} 失败: {e}")
            self.plugin_status[plugin_name] = "error"
            return None

    def shutdown_plugin(self, plugin_name: str) -> bool:
        """
        关闭插件

        Args:
            plugin_name: 插件名称

        Returns:
            bool: 关闭是否成功
        """
        if plugin_name not in self.plugins:
            logger.error(f"插件 {plugin_name} 未注册")
            return False

        try:
            plugin = self.plugins[plugin_name]
            success = plugin.shutdown()

            if success:
                self.plugin_status[plugin_name] = "shutdown"
                logger.info(f"插件 {plugin_name} 关闭成功")

            return success

        except Exception as e:
            logger.error(f"关闭插件 {plugin_name} 失败: {e}")
            return False

    def enable_plugin(self, plugin_name: str) -> bool:
        """启用插件"""
        if plugin_name not in self.plugins:
            return False

        plugin_info = self.plugins[plugin_name].get_info()
        plugin_info.enabled = True
        self.plugin_status[plugin_name] = "registered"
        return True

    def disable_plugin(self, plugin_name: str) -> bool:
        """禁用插件"""
        if plugin_name not in self.plugins:
            return False

        plugin_info = self.plugins[plugin_name].get_info()
        plugin_info.enabled = False
        self.plugin_status[plugin_name] = "disabled"
        return True

    def list_plugins(self) -> List[str]:
        """列出所有已注册插件"""
        return list(self.plugins.keys())

    def get_plugin_info(self, plugin_name: str) -> Optional[PluginInfo]:
        """获取插件信息"""
        if plugin_name in self.plugins:
            return self.plugins[plugin_name].get_info()
        return None

    def get_plugin_status(self, plugin_name: str) -> Optional[str]:
        """获取插件状态"""
        return self.plugin_status.get(plugin_name)

    def initialize_all(self) -> Dict[str, bool]:
        """初始化所有已注册插件"""
        results = {}
        for plugin_name in self.plugins:
            results[plugin_name] = self.initialize_plugin(plugin_name)
        return results

    def shutdown_all(self) -> Dict[str, bool]:
        """关闭所有插件"""
        results = {}
        for plugin_name in self.plugins:
            results[plugin_name] = self.shutdown_plugin(plugin_name)
        return results
