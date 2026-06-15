"""
工单管理插件
处理客户转人工请求和工单流程
"""

import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from backend.plugin_interface import PluginInterface, PluginInfo
from backend.config import config


logger = logging.getLogger(__name__)


class Ticket:
    """工单模型"""
    
    def __init__(self, session_id: str, customer_id: str, reason: str):
        self.id = str(uuid.uuid4())
        self.session_id = session_id
        self.customer_id = customer_id
        self.reason = reason
        self.status = "pending"  # pending, accepted, closed
        self.created_at = datetime.now()
        self.accepted_at = None
        self.closed_at = None
        self.agent_id = None
        self.priority = "normal"  # low, normal, high, urgent


class TicketPlugin(PluginInterface):
    """工单管理插件"""
    
    def __init__(self):
        self.tickets: Dict[str, Ticket] = {}
        self.pending_tickets: List[str] = []
        self.timeout = config.ticket.timeout
    
    def initialize(self, config: Dict[str, Any]) -> bool:
        """
        初始化工单插件
        
        Args:
            config: 插件配置
        
        Returns:
            bool: 初始化是否成功
        """
        try:
            self.timeout = config.get("timeout", 30)
            logger.info("工单管理插件初始化成功")
            return True
            
        except Exception as e:
            logger.error(f"工单管理插件初始化失败: {e}")
            return False
    
    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行工单操作
        
        Args:
            input_data: 输入数据
        
        Returns:
            Dict: 执行结果
        """
        action = input_data.get("action", "")
        
        if action == "create_ticket":
            return self.create_ticket(input_data)
        elif action == "accept_ticket":
            return self.accept_ticket(input_data)
        elif action == "close_ticket":
            return self.close_ticket(input_data)
        elif action == "get_pending_tickets":
            return self.get_pending_tickets()
        elif action == "get_ticket_info":
            return self.get_ticket_info(input_data)
        else:
            return {"error": "Unknown action"}
    
    def shutdown(self) -> bool:
        """
        关闭工单插件
        
        Returns:
            bool: 关闭是否成功
        """
        try:
            # 自动关闭所有待处理工单
            for ticket_id in self.pending_tickets:
                self.close_ticket({"ticket_id": ticket_id, "reason": "系统关闭"})
            
            logger.info("工单管理插件关闭成功")
            return True
            
        except Exception as e:
            logger.error(f"工单管理插件关闭失败: {e}")
            return False
    
    def get_info(self) -> PluginInfo:
        """
        获取插件信息
        
        Returns:
            PluginInfo: 插件信息
        """
        return PluginInfo(
            name="ticket_plugin",
            version="1.0.0",
            description="工单管理插件",
            author="AI客服团队",
            dependencies=[]
        )
    
    def create_ticket(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        创建工单
        
        Args:
            input_data: 包含session_id, customer_id, reason
        
        Returns:
            Dict: 创建结果
        """
        try:
            session_id = input_data.get("session_id", "")
            customer_id = input_data.get("customer_id", "")
            reason = input_data.get("reason", "客户主动要求转人工")
            
            # 创建工单
            ticket = Ticket(session_id, customer_id, reason)
            
            # 保存工单
            self.tickets[ticket.id] = ticket
            self.pending_tickets.append(ticket.id)
            
            logger.info(f"创建工单成功: {ticket.id}")
            
            return {
                "success": True,
                "ticket_id": ticket.id,
                "status": ticket.status,
                "created_at": ticket.created_at.isoformat(),
                "message": "工单创建成功，等待客服接入"
            }
            
        except Exception as e:
            logger.error(f"创建工单失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def accept_ticket(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        客服接入工单
        
        Args:
            input_data: 包含ticket_id, agent_id
        
        Returns:
            Dict: 接入结果
        """
        try:
            ticket_id = input_data.get("ticket_id", "")
            agent_id = input_data.get("agent_id", "")
            
            if ticket_id not in self.tickets:
                return {"error": "工单不存在"}
            
            ticket = self.tickets[ticket_id]
            
            if ticket.status != "pending":
                return {"error": "工单已被处理"}
            
            # 更新工单状态
            ticket.status = "accepted"
            ticket.accepted_at = datetime.now()
            ticket.agent_id = agent_id
            
            # 从待处理列表移除
            if ticket_id in self.pending_tickets:
                self.pending_tickets.remove(ticket_id)
            
            logger.info(f"客服 {agent_id} 接入工单 {ticket_id}")
            
            return {
                "success": True,
                "ticket_id": ticket_id,
                "status": ticket.status,
                "agent_id": agent_id,
                "accepted_at": ticket.accepted_at.isoformat(),
                "message": "客服已接入，开始服务"
            }
            
        except Exception as e:
            logger.error(f"接入工单失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def close_ticket(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        关闭工单
        
        Args:
            input_data: 包含ticket_id, reason
        
        Returns:
            Dict: 关闭结果
        """
        try:
            ticket_id = input_data.get("ticket_id", "")
            reason = input_data.get("reason", "服务完成")
            
            if ticket_id not in self.tickets:
                return {"error": "工单不存在"}
            
            ticket = self.tickets[ticket_id]
            
            # 更新工单状态
            ticket.status = "closed"
            ticket.closed_at = datetime.now()
            
            # 从待处理列表移除
            if ticket_id in self.pending_tickets:
                self.pending_tickets.remove(ticket_id)
            
            logger.info(f"工单 {ticket_id} 已关闭")
            
            return {
                "success": True,
                "ticket_id": ticket_id,
                "status": ticket.status,
                "closed_at": ticket.closed_at.isoformat(),
                "message": "工单已关闭"
            }
            
        except Exception as e:
            logger.error(f"关闭工单失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_pending_tickets(self) -> Dict[str, Any]:
        """
        获取待处理工单列表
        
        Returns:
            Dict: 待处理工单列表
        """
        pending_list = []
        
        for ticket_id in self.pending_tickets:
            ticket = self.tickets[ticket_id]
            
            # 检查是否超时
            if datetime.now() - ticket.created_at > timedelta(minutes=self.timeout):
                # 自动关闭超时工单
                self.close_ticket({"ticket_id": ticket_id, "reason": "超时自动关闭"})
                continue
            
            pending_list.append({
                "ticket_id": ticket.id,
                "session_id": ticket.session_id,
                "customer_id": ticket.customer_id,
                "reason": ticket.reason,
                "created_at": ticket.created_at.isoformat(),
                "priority": ticket.priority
            })
        
        return {
            "success": True,
            "pending_tickets": pending_list,
            "count": len(pending_list)
        }
    
    def get_ticket_info(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        获取工单详情
        
        Args:
            input_data: 包含ticket_id
        
        Returns:
            Dict: 工单详情
        """
        ticket_id = input_data.get("ticket_id", "")
        
        if ticket_id not in self.tickets:
            return {"error": "工单不存在"}
        
        ticket = self.tickets[ticket_id]
        
        return {
            "success": True,
            "ticket_info": {
                "ticket_id": ticket.id,
                "session_id": ticket.session_id,
                "customer_id": ticket.customer_id,
                "reason": ticket.reason,
                "status": ticket.status,
                "created_at": ticket.created_at.isoformat(),
                "accepted_at": ticket.accepted_at.isoformat() if ticket.accepted_at else None,
                "closed_at": ticket.closed_at.isoformat() if ticket.closed_at else None,
                "agent_id": ticket.agent_id,
                "priority": ticket.priority
            }
        }