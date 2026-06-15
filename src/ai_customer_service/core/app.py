"""
FastAPI应用创建函数
"""

import logging
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse

from ai_customer_service.core.plugin_manager import PluginManager
from ai_customer_service.core.config_manager import ConfigManager

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """创建FastAPI应用"""
    app = FastAPI(
        title="AI客服系统",
        version="1.0.0",
        description="基于MCP协议的插件式AI客服系统"
    )

    # 创建插件管理器
    plugin_manager = PluginManager()

    # 发现并注册插件
    discovered = plugin_manager.discover_plugins()
    logger.info(f"发现 {len(discovered)} 个插件")

    # 初始化所有插件
    plugin_manager.initialize_all()

    # 存储到app state
    app.state.plugin_manager = plugin_manager

    # 挂载静态文件
    try:
        app.mount("/static", StaticFiles(directory="frontend"), name="static")
    except:
        pass

    # 主页
    @app.get("/", response_class=HTMLResponse)
    async def root():
        """主页"""
        try:
            with open("frontend/index.html", "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            return """
            <html>
                <head><title>AI客服系统</title></head>
                <body>
                    <h1>AI客服系统</h1>
                    <p>前端文件未找到，请确保frontend目录存在</p>
                    <p>API文档: <a href="/docs">/docs</a></p>
                </body>
            </html>
            """

    # 聊天API
    @app.post("/api/chat")
    async def chat(request: dict):
        """处理聊天消息"""
        plugin_manager = request.app.state.plugin_manager

        session_id = request.get("session_id", "")
        message = request.get("message", "")

        # 使用AI客服插件处理
        result = plugin_manager.execute_plugin("ai_service_plugin", {
            "session_id": session_id,
            "message": message
        })

        return result or {"success": False, "error": "插件执行失败"}

    # 转人工API
    @app.post("/api/request-human")
    async def request_human(request: dict):
        """请求转人工"""
        plugin_manager = request.app.state.plugin_manager

        result = plugin_manager.execute_plugin("ticket_plugin", {
            "action": "create_ticket",
            "session_id": request.get("session_id", ""),
            "customer_id": request.get("customer_id", ""),
            "reason": request.get("reason", "")
        })

        return result or {"success": False, "error": "工单创建失败"}

    # 系统状态
    @app.get("/api/status")
    async def status():
        """获取系统状态"""
        plugin_manager = request.app.state.plugin_manager
        plugins = []

        for name in plugin_manager.list_plugins():
            info = plugin_manager.get_plugin_info(name)
            status = plugin_manager.get_plugin_status(name)
            plugins.append({
                "name": info.name if info else name,
                "version": info.version if info else "unknown",
                "status": status,
                "enabled": info.enabled if info else True
            })

        return {
            "status": "running",
            "plugins_count": len(plugins),
            "plugins": plugins
        }

    return app
