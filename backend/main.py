"""
FastAPI主文件
整合所有插件，提供API接口
"""

import logging
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from typing import Dict, Any
import uvicorn

from backend.plugin_manager import PluginManager
from backend.config import config
from backend.plugins.ai_service_plugin import AIServicePlugin
from backend.plugins.ticket_plugin import TicketPlugin
from backend.plugins.knowledge_base_plugin import KnowledgeBasePlugin


# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


# 创建FastAPI应用
app = FastAPI(title="AI客服系统", version="1.0.0")


# 创建插件管理器
plugin_manager = PluginManager()


# 初始化插件
def initialize_plugins():
    """初始化所有插件"""
    
    # 注册AI客服插件
    ai_plugin = AIServicePlugin()
    ai_config = config.load_plugin_config("ai_service_plugin")
    plugin_manager.register_plugin("ai_service_plugin", ai_plugin, ai_config)
    plugin_manager.initialize_plugin("ai_service_plugin")
    
    # 注册工单插件
    ticket_plugin = TicketPlugin()
    ticket_config = config.load_plugin_config("ticket_plugin")
    plugin_manager.register_plugin("ticket_plugin", ticket_plugin, ticket_config)
    plugin_manager.initialize_plugin("ticket_plugin")
    
    # 注册知识库插件
    kb_plugin = KnowledgeBasePlugin()
    kb_config = config.load_plugin_config("knowledge_base_plugin")
    plugin_manager.register_plugin("knowledge_base_plugin", kb_plugin, kb_config)
    plugin_manager.initialize_plugin("knowledge_base_plugin")
    
    # 关联知识库插件到AI客服插件
    ai_plugin.set_knowledge_base(kb_plugin)
    
    logger.info("所有插件初始化完成")


# 启动时初始化插件
@app.on_event("startup")
async def startup_event():
    """应用启动事件"""
    initialize_plugins()
    logger.info("AI客服系统启动成功")


# 关闭时清理插件
@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭事件"""
    for plugin_name in plugin_manager.list_plugins():
        plugin_manager.shutdown_plugin(plugin_name)
    logger.info("AI客服系统关闭成功")


# API请求模型
class ChatRequest(BaseModel):
    """聊天请求模型"""
    session_id: str
    message: str


class TransferRequest(BaseModel):
    """转人工请求模型"""
    session_id: str
    customer_id: str
    reason: str = "客户主动要求转人工"


class AcceptTicketRequest(BaseModel):
    """接入工单请求模型"""
    ticket_id: str
    agent_id: str


class CloseTicketRequest(BaseModel):
    """关闭工单请求模型"""
    ticket_id: str
    reason: str = "服务完成"


# 知识库请求模型
class AddDocumentRequest(BaseModel):
    """添加文档请求模型"""
    document_id: str
    content: str
    metadata: Dict[str, Any] = {}


class SearchRequest(BaseModel):
    """搜索请求模型"""
    query: str
    top_k: int = 5


class DeleteDocumentRequest(BaseModel):
    """删除文档请求模型"""
    document_id: str


# API路由

@app.get("/", response_class=HTMLResponse)
async def root():
    """返回前端页面"""
    try:
        with open("frontend/index.html", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return HTMLResponse(content="<h1>AI客服系统</h1><p>前端页面未找到</p>", status_code=404)


@app.post("/api/chat")
async def chat(request: ChatRequest):
    """
    处理客户聊天消息
    
    Args:
        request: 聊天请求
    
    Returns:
        JSONResponse: AI响应结果
    """
    try:
        # 执行AI客服插件
        result = plugin_manager.execute_plugin(
            "ai_service_plugin",
            {
                "session_id": request.session_id,
                "message": request.message
            }
        )
        
        return JSONResponse(content=result)
        
    except Exception as e:
        logger.error(f"处理聊天消息失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/request-human")
async def request_human(request: TransferRequest):
    """
    客户请求转人工
    
    Args:
        request: 转人工请求
    
    Returns:
        JSONResponse: 工单创建结果
    """
    try:
        # 执行工单插件创建工单
        result = plugin_manager.execute_plugin(
            "ticket_plugin",
            {
                "action": "create_ticket",
                "session_id": request.session_id,
                "customer_id": request.customer_id,
                "reason": request.reason
            }
        )
        
        return JSONResponse(content=result)
        
    except Exception as e:
        logger.error(f"转人工请求失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/tickets")
async def get_tickets():
    """
    获取待处理工单列表
    
    Returns:
        JSONResponse: 待处理工单列表
    """
    try:
        result = plugin_manager.execute_plugin(
            "ticket_plugin",
            {"action": "get_pending_tickets"}
        )
        
        return JSONResponse(content=result)
        
    except Exception as e:
        logger.error(f"获取工单列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/tickets/{ticket_id}")
async def get_ticket_info(ticket_id: str):
    """
    获取工单详情
    
    Args:
        ticket_id: 工单ID
    
    Returns:
        JSONResponse: 工单详情
    """
    try:
        result = plugin_manager.execute_plugin(
            "ticket_plugin",
            {
                "action": "get_ticket_info",
                "ticket_id": ticket_id
            }
        )
        
        return JSONResponse(content=result)
        
    except Exception as e:
        logger.error(f"获取工单详情失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/tickets/accept")
async def accept_ticket(request: AcceptTicketRequest):
    """
    客服接入工单
    
    Args:
        request: 接入工单请求
    
    Returns:
        JSONResponse: 接入结果
    """
    try:
        result = plugin_manager.execute_plugin(
            "ticket_plugin",
            {
                "action": "accept_ticket",
                "ticket_id": request.ticket_id,
                "agent_id": request.agent_id
            }
        )
        
        return JSONResponse(content=result)
        
    except Exception as e:
        logger.error(f"接入工单失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/tickets/close")
async def close_ticket(request: CloseTicketRequest):
    """
    关闭工单
    
    Args:
        request: 关闭工单请求
    
    Returns:
        JSONResponse: 关闭结果
    """
    try:
        result = plugin_manager.execute_plugin(
            "ticket_plugin",
            {
                "action": "close_ticket",
                "ticket_id": request.ticket_id,
                "reason": request.reason
            }
        )
        
        return JSONResponse(content=result)
        
    except Exception as e:
        logger.error(f"关闭工单失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/status")
async def get_status():
    """
    获取系统状态
    
    Returns:
        JSONResponse: 系统状态信息
    """
    try:
        plugins = plugin_manager.list_plugins()
        health_status = plugin_manager.health_check_all()
        
        return JSONResponse(content={
            "success": True,
            "plugins": plugins,
            "health_status": health_status,
            "server": config.server.dict()
        })
        
    except Exception as e:
        logger.error(f"获取系统状态失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 知识库API ====================

@app.post("/api/knowledge/add")
async def add_document(request: AddDocumentRequest):
    """
    添加文档到知识库
    
    Args:
        request: 添加文档请求
    
    Returns:
        JSONResponse: 添加结果
    """
    try:
        result = plugin_manager.execute_plugin(
            "knowledge_base_plugin",
            {
                "action": "add_document",
                "document_id": request.document_id,
                "content": request.content,
                "metadata": request.metadata
            }
        )
        
        return JSONResponse(content=result)
        
    except Exception as e:
        logger.error(f"添加文档失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/knowledge/search")
async def search_knowledge(request: SearchRequest):
    """
    搜索知识库
    
    Args:
        request: 搜索请求
    
    Returns:
        JSONResponse: 搜索结果（包含父块完整内容）
    """
    try:
        result = plugin_manager.execute_plugin(
            "knowledge_base_plugin",
            {
                "action": "search",
                "query": request.query,
                "top_k": request.top_k
            }
        )
        
        return JSONResponse(content=result)
        
    except Exception as e:
        logger.error(f"搜索知识库失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/knowledge/documents")
async def list_documents():
    """
    获取知识库文档列表
    
    Returns:
        JSONResponse: 文档列表
    """
    try:
        result = plugin_manager.execute_plugin(
            "knowledge_base_plugin",
            {"action": "list_documents"}
        )
        
        return JSONResponse(content=result)
        
    except Exception as e:
        logger.error(f"获取文档列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/knowledge/documents/{document_id}")
async def get_document(document_id: str):
    """
    获取文档详情
    
    Args:
        document_id: 文档ID
    
    Returns:
        JSONResponse: 文档详情
    """
    try:
        result = plugin_manager.execute_plugin(
            "knowledge_base_plugin",
            {
                "action": "get_document",
                "document_id": document_id
            }
        )
        
        return JSONResponse(content=result)
        
    except Exception as e:
        logger.error(f"获取文档详情失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/knowledge/documents/{document_id}")
async def delete_document(document_id: str):
    """
    删除文档
    
    Args:
        document_id: 文档ID
    
    Returns:
        JSONResponse: 删除结果
    """
    try:
        result = plugin_manager.execute_plugin(
            "knowledge_base_plugin",
            {
                "action": "delete_document",
                "document_id": document_id
            }
        )
        
        return JSONResponse(content=result)
        
    except Exception as e:
        logger.error(f"删除文档失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/knowledge/stats")
async def get_knowledge_stats():
    """
    获取知识库统计信息
    
    Returns:
        JSONResponse: 统计信息
    """
    try:
        result = plugin_manager.execute_plugin(
            "knowledge_base_plugin",
            {"action": "get_stats"}
        )
        
        return JSONResponse(content=result)
        
    except Exception as e:
        logger.error(f"获取知识库统计失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# 挂载静态文件
app.mount("/static", StaticFiles(directory="frontend"), name="static")


# 主函数
def main():
    """启动服务器"""
    uvicorn.run(
        app,
        host=config.server.host,
        port=config.server.port,
        log_level="info"
    )


if __name__ == "__main__":
    main()