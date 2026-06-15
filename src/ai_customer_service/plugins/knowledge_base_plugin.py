"""
知识库插件
提供FAQ管理和文档检索功能
"""

import logging
from typing import Dict, Any, List, Optional
from ai_customer_service.core.plugin_interface import PluginInterface, PluginInfo


logger = logging.getLogger(__name__)


class KnowledgeBasePlugin(PluginInterface):
    """知识库插件"""

    def __init__(self):
        self.faq_data = []
        self.categories = {}
        self._init_default_knowledge()

    def initialize(self, config: Dict[str, Any]) -> bool:
        """初始化知识库"""
        try:
            logger.info("知识库插件初始化成功")
            return True
        except Exception as e:
            logger.error(f"知识库插件初始化失败: {e}")
            return False

    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行知识库操作"""
        action = input_data.get("action", "search")

        if action == "search":
            return self._search(input_data)
        elif action == "add_faq":
            return self._add_faq(input_data)
        elif action == "list_categories":
            return self._list_categories(input_data)
        else:
            return {"success": False, "error": f"未知操作: {action}"}

    def _init_default_knowledge(self):
        """初始化默认知识"""
        self.faq_data = [
            {
                "id": 1,
                "question": "如何申请退款？",
                "answer": "请在订单详情页点击'申请退款'，填写退款原因后提交。退款将在1-7个工作日内原路返回。",
                "category": "退款"
            },
            {
                "id": 2,
                "question": "订单什么时候发货？",
                "answer": "一般情况下，订单付款后24小时内发货。节假日可能会有延迟，请关注物流信息更新。",
                "category": "物流"
            },
            {
                "id": 3,
                "question": "如何修改收货地址？",
                "answer": "订单付款前可以自行修改地址。付款后如需修改，请联系客服处理。",
                "category": "订单"
            },
            {
                "id": 4,
                "question": "支持哪些支付方式？",
                "answer": "我们支持支付宝、微信支付、银行卡支付、信用卡支付等多种方式。",
                "category": "支付"
            },
            {
                "id": 5,
                "question": "如何联系人工客服？",
                "answer": "您可以点击页面上的'转人工'按钮，或者发送'人工客服'关键字联系我们。",
                "category": "咨询"
            }
        ]

        self.categories = {
            "退款": ["申请退款", "退款进度", "退款到账"],
            "物流": ["发货时间", "物流查询", "收货地址"],
            "订单": ["订单修改", "订单取消", "订单合并"],
            "支付": ["支付方式", "支付失败", "发票开具"],
            "咨询": ["人工客服", "工作时间", "联系方式"]
        }

    def _search(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """搜索知识库"""
        query = input_data.get("query", "")
        category = input_data.get("category", "")

        results = []

        for faq in self.faq_data:
            if query.lower() in faq["question"].lower() or query.lower() in faq["answer"].lower():
                if not category or faq["category"] == category:
                    results.append(faq)

        return {
            "success": True,
            "results": results,
            "count": len(results)
        }

    def _add_faq(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """添加FAQ"""
        question = input_data.get("question", "")
        answer = input_data.get("answer", "")
        category = input_data.get("category", "未分类")

        if not question or not answer:
            return {"success": False, "error": "问题和答案不能为空"}

        faq_id = len(self.faq_data) + 1
        new_faq = {
            "id": faq_id,
            "question": question,
            "answer": answer,
            "category": category
        }

        self.faq_data.append(new_faq)

        return {
            "success": True,
            "faq": new_faq
        }

    def _list_categories(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """列出所有分类"""
        return {
            "success": True,
            "categories": list(self.categories.keys()),
            "count": len(self.categories)
        }

    def shutdown(self) -> bool:
        """关闭知识库"""
        logger.info("知识库插件关闭成功")
        return True

    def get_info(self) -> PluginInfo:
        """获取插件信息"""
        return PluginInfo(
            name="knowledge_base_plugin",
            version="1.0.0",
            description="知识库管理插件，提供FAQ和文档检索",
            author="AI客服团队",
            dependencies=[]
        )

    def get_dependencies(self) -> list:
        """获取依赖"""
        return []
