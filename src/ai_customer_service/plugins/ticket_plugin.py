"""
工单插件
处理人工客服转接和工单管理
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from ai_customer_service.core.plugin_interface import PluginInterface, PluginInfo


logger = logging.getLogger(__name__)


class TicketPlugin(PluginInterface):
    """工单插件"""

    def __init__(self):
        self.tickets = {}
        self.ticket_counter = 1000

    def initialize(self, config: Dict[str, Any]) -> bool:
        """初始化工单系统"""
        try:
            logger.info("工单插件初始化成功")
            return True
        except Exception as e:
            logger.error(f"工单插件初始化失败: {e}")
            return False

    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行工单操作"""
        action = input_data.get("action", "create_ticket")

        if action == "create_ticket":
            return self._create_ticket(input_data)
        elif action == "get_ticket":
            return self._get_ticket(input_data)
        elif action == "list_tickets":
            return self._list_tickets(input_data)
        elif action == "accept_ticket":
            return self._accept_ticket(input_data)
        elif action == "close_ticket":
            return self._close_ticket(input_data)
        else:
            return {"success": False, "error": f"未知操作: {action}"}

    def _create_ticket(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """创建工单"""
        session_id = input_data.get("session_id", "")
        customer_id = input_data.get("customer_id", "")
        reason = input_data.get("reason", "")

        self.ticket_counter += 1
        ticket_id = f"T{self.ticket_counter}"

        ticket = {
            "ticket_id": ticket_id,
            "session_id": session_id,
            "customer_id": customer_id,
            "reason": reason,
            "status": "pending",
            "created_at": datetime.now().isoformat(),
            "accepted_at": None,
            "closed_at": None,
            "agent_id": None
        }

        self.tickets[ticket_id] = ticket

        return {
            "success": True,
            "ticket_id": ticket_id,
            "status": "pending",
            "message": "工单已创建，等待客服接入"
        }

    def _get_ticket(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """获取工单详情"""
        ticket_id = input_data.get("ticket_id", "")

        if ticket_id not in self.tickets:
            return {"success": False, "error": "工单不存在"}

        return {
            "success": True,
            "ticket_info": self.tickets[ticket_id]
        }

    def _list_tickets(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """列出工单"""
        status = input_data.get("status", "")

        tickets = list(self.tickets.values())

        if status:
            tickets = [t for t in tickets if t["status"] == status]

        return {
            "success": True,
            "tickets": tickets,
            "count": len(tickets)
        }

    def _accept_ticket(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """客服接单"""
        ticket_id = input_data.get("ticket_id", "")
        agent_id = input_data.get("agent_id", "agent_001")

        if ticket_id not in self.tickets:
            return {"success": False, "error": "工单不存在"}

        ticket = self.tickets[ticket_id]
        ticket["status"] = "accepted"
        ticket["accepted_at"] = datetime.now().isoformat()
        ticket["agent_id"] = agent_id

        return {
            "success": True,
            "ticket_id": ticket_id,
            "status": "accepted",
            "message": f"客服 {agent_id} 已接单"
        }

    def _close_ticket(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """关闭工单"""
        ticket_id = input_data.get("ticket_id", "")

        if ticket_id not in self.tickets:
            return {"success": False, "error": "工单不存在"}

        ticket = self.tickets[ticket_id]
        ticket["status"] = "closed"
        ticket["closed_at"] = datetime.now().isoformat()

        return {
            "success": True,
            "ticket_id": ticket_id,
            "status": "closed",
            "message": "工单已关闭"
        }

    def shutdown(self) -> bool:
        """关闭工单系统"""
        logger.info("工单插件关闭成功")
        return True

    def get_info(self) -> PluginInfo:
        """获取插件信息"""
        return PluginInfo(
            name="ticket_plugin",
            version="1.0.0",
            description="工单管理插件，处理人工客服转接",
            author="AI客服团队",
            dependencies=[]
        )

    def get_dependencies(self) -> list:
        """获取依赖"""
        return []
