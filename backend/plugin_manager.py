"""
插件管理器
负责插件的注册、加载、卸载和生命周期管理
"""

import logging
from typing import Dict, List, Optional
from backend.plugin_interface import PluginInterface, PluginInfo


logger = logging.getLogger(__name__)


class PluginManager:
    """插件管理器"""
    
    def __init__(self):
        self.plugins: Dict[str, PluginInterface] = {}
        self.plugin_configs: Dict[str, Dict] = {}
        self.plugin_status: Dict[str, str] = {}  # initialized, running, shutdown
    
    def register_plugin(self, plugin_name: str, plugin: PluginInterface, config: Dict = None) -> bool:
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
            # 检查插件是否已存在
            if plugin_name in self.plugins:
                logger.warning(f"插件 {plugin_name} 已存在，将被替换")
            
            # 注册插件
            self.plugins[plugin_name] = plugin
            self.plugin_configs[plugin_name] = config or {}
            self.plugin_status[plugin_name] = "registered"
            
            logger.info(f"插件 {plugin_name} 注册成功")
            return True
            
        except Exception as e:
            logger.error(f"注册插件 {plugin_name} 失败: {e}")
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
            config = self.plugin_configs[plugin_name]
            
            # 执行初始化
            success = plugin.initialize(config)
            
            if success:
                self.plugin_status[plugin_name] = "initialized"
                logger.info(f"插件 {plugin_name} 初始化成功")
            else:
                logger.error(f"插件 {plugin_name} 初始化失败")
            
            return success
            
        except Exception as e:
            logger.error(f"初始化插件 {plugin_name} 时发生错误: {e}")
            return False
    
    def execute_plugin(self, plugin_name: str, input_data: Dict) -> Dict:
        """
        执行插件
        
        Args:
            plugin_name: 插件名称
            input_data: 输入数据
        
        Returns:
            Dict: 执行结果
        """
        if plugin_name not in self.plugins:
            logger.error(f"插件 {plugin_name} 未注册")
            return {"error": "Plugin not registered"}
        
        # 允许initialized或running状态的插件执行
        status = self.plugin_status.get(plugin_name, "unknown")
        if status not in ["initialized", "running"]:
            logger.error(f"插件 {plugin_name} 未初始化，当前状态: {status}")
            return {"error": "Plugin not initialized"}
        
        try:
            plugin = self.plugins[plugin_name]
            result = plugin.execute(input_data)
            
            self.plugin_status[plugin_name] = "running"
            logger.info(f"插件 {plugin_name} 执行成功")
            
            return result
            
        except Exception as e:
            logger.error(f"执行插件 {plugin_name} 时发生错误: {e}")
            return {"error": str(e)}
    
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
            else:
                logger.error(f"插件 {plugin_name} 关闭失败")
            
            return success
            
        except Exception as e:
            logger.error(f"关闭插件 {plugin_name} 时发生错误: {e}")
            return False
    
    def unload_plugin(self, plugin_name: str) -> bool:
        """
        卸载插件
        
        Args:
            plugin_name: 插件名称
        
        Returns:
            bool: 卸载是否成功
        """
        if plugin_name not in self.plugins:
            logger.error(f"插件 {plugin_name} 未注册")
            return False
        
        try:
            # 先关闭插件
            self.shutdown_plugin(plugin_name)
            
            # 移除插件
            del self.plugins[plugin_name]
            del self.plugin_configs[plugin_name]
            del self.plugin_status[plugin_name]
            
            logger.info(f"插件 {plugin_name} 卸载成功")
            return True
            
        except Exception as e:
            logger.error(f"卸载插件 {plugin_name} 时发生错误: {e}")
            return False
    
    def get_plugin_info(self, plugin_name: str) -> Optional[PluginInfo]:
        """
        获取插件信息
        
        Args:
            plugin_name: 插件名称
        
        Returns:
            PluginInfo: 插件信息
        """
        if plugin_name not in self.plugins:
            return None
        
        return self.plugins[plugin_name].get_info()
    
    def list_plugins(self) -> List[str]:
        """
        列出所有插件
        
        Returns:
            List[str]: 插件名称列表
        """
        return list(self.plugins.keys())
    
    def get_plugin_status(self, plugin_name: str) -> str:
        """
        获取插件状态
        
        Args:
            plugin_name: 插件名称
        
        Returns:
            str: 插件状态
        """
        return self.plugin_status.get(plugin_name, "unknown")
    
    def health_check_all(self) -> Dict[str, bool]:
        """
        对所有插件进行健康检查
        
        Returns:
            Dict[str, bool]: 各插件的健康状态
        """
        health_status = {}
        
        for plugin_name, plugin in self.plugins.items():
            health_status[plugin_name] = plugin.health_check()
        
        return health_status