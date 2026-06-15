"""
AI客服插件
提供智能客服响应功能，集成知识库增强
"""

import logging
from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from ai_customer_service.core.plugin_interface import PluginInterface, PluginInfo


logger = logging.getLogger(__name__)


class AIServicePlugin(PluginInterface):
    """AI客服插件"""

    # 转人工触发配置
    TRANSFER_CONFIG = {
        "max_turns_before_suggest": 3,
        "satisfaction_threshold": 0.5,
        "min_turns_for_satisfaction_trigger": 2,
    }

    def __init__(self):
        self.llm = None
        self.conversation_history = []
        self.conversation_turns = 0
        self.use_mock = False
        self.system_prompt = """
你是一个专业的AI客服助手，负责为客户提供友好、专业的服务。

你的职责：
1. 理解客户的问题并提供准确的回答
2. 保持友好和专业的态度
3. 如果无法解决问题，建议客户转人工客服
4. 记录重要的客户信息

回复要求：
- 语言简洁明了
- 避免使用技术术语
- 提供具体的解决方案
- 如果客户不满意，主动建议转人工
- 如果客户明确要求转人工或人工客服，直接确认并结束对话
"""

    def initialize(self, config: Dict[str, Any]) -> bool:
        """初始化AI客服插件"""
        try:
            from ai_customer_service.core.config_manager import config as global_config

            api_key = global_config.get("openai_api_key", "")

            if not api_key or api_key.strip() == "" or api_key == "your-api-key-here":
                self.use_mock = True
                logger.info("未配置API密钥，使用模拟模式")
                return True

            model_name = global_config.get("model_name", "gpt-3.5-turbo")
            temperature = global_config.get("temperature", 0.7)

            self.llm = ChatOpenAI(
                model=model_name,
                temperature=temperature,
                api_key=api_key
            )

            logger.info(f"AI客服插件初始化成功 (模型: {model_name})")
            return True

        except Exception as e:
            logger.error(f"AI客服插件初始化失败: {e}")
            self.use_mock = True
            logger.info("AI客服插件初始化成功（模拟模式）")
            return True

    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行AI客服功能"""
        try:
            user_message = input_data.get("message", "")
            session_id = input_data.get("session_id", "")

            if not user_message:
                return {"success": False, "error": "消息不能为空"}

            if self.use_mock:
                user_requested_transfer = self._check_transfer_request(user_message)
                mock_response = self._get_mock_response(user_message)
                self.conversation_turns += 1

                self.conversation_history.append(HumanMessage(content=user_message))
                self.conversation_history.append(AIMessage(content=mock_response))

                satisfaction_level = self._analyze_satisfaction(user_message, mock_response)
                should_transfer = self._should_suggest_transfer(satisfaction_level)

                return {
                    "success": True,
                    "response": mock_response,
                    "session_id": session_id,
                    "satisfaction_level": satisfaction_level,
                    "should_transfer": should_transfer,
                    "conversation_turns": self.conversation_turns,
                    "user_requested_transfer": user_requested_transfer,
                    "transfer_suggestion": self._get_transfer_suggestion(),
                    "mode": "mock"
                }

            messages = [
                SystemMessage(content=self.system_prompt),
                HumanMessage(content=user_message)
            ]

            if self.conversation_history:
                messages.extend(self.conversation_history[-10:])

            response = self.llm.invoke(messages)

            user_requested_transfer = self._check_transfer_request(user_message)
            self.conversation_turns += 1

            self.conversation_history.append(HumanMessage(content=user_message))
            self.conversation_history.append(AIMessage(content=response.content))

            satisfaction_level = self._analyze_satisfaction(user_message, response.content)
            should_transfer = self._should_suggest_transfer(satisfaction_level)

            return {
                "success": True,
                "response": response.content,
                "session_id": session_id,
                "satisfaction_level": satisfaction_level,
                "should_transfer": should_transfer,
                "conversation_turns": self.conversation_turns,
                "user_requested_transfer": user_requested_transfer,
                "transfer_suggestion": self._get_transfer_suggestion(),
                "mode": "real"
            }

        except Exception as e:
            logger.error(f"AI客服执行失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "response": "抱歉，我暂时无法回答您的问题，建议您转人工客服。"
            }

    def _get_mock_response(self, user_message: str) -> str:
        """获取模拟响应"""
        mock_responses = {
            "你好": "您好！我是AI客服，很高兴为您服务！请问有什么可以帮助您的？",
            "hello": "Hello! How can I assist you today?",
            "谢谢": "不客气！如果您还有其他问题，随时欢迎再来咨询。",
            "转人工": "好的，正在为您转接人工客服，请稍等...",
            "人工客服": "好的，正在为您创建工单，客服人员会尽快联系您。",
            "不满意": "非常抱歉给您带来不好的体验，我已经为您转接人工客服处理。",
            "帮助": "请问您需要哪方面的帮助呢？我可以协助您解决常见问题。",
            "问题": "请详细描述您的问题，我会尽力为您解答。",
            "订单": "关于订单的问题，我可以帮您查询订单状态、物流信息等。",
            "退款": "如果您需要退款，请提供订单号，我会协助您处理。",
            "投诉": "非常抱歉您遇到了问题，我会立即为您转接人工客服处理投诉。"
        }

        for keyword, response in mock_responses.items():
            if keyword in user_message:
                return response

        return f"您好！感谢您的咨询。您说的是：\"{user_message}\"。这是一个模拟响应，当配置了API密钥后，将提供更智能的回答。如需转人工客服，请回复\"转人工\"。"

    def shutdown(self) -> bool:
        """关闭AI客服插件"""
        try:
            self.conversation_history = []
            logger.info("AI客服插件关闭成功")
            return True
        except Exception as e:
            logger.error(f"AI客服插件关闭失败: {e}")
            return False

    def get_info(self) -> PluginInfo:
        """获取插件信息"""
        return PluginInfo(
            name="ai_service_plugin",
            version="1.0.0",
            description="AI客服智能响应插件",
            author="AI客服团队",
            dependencies=["langchain", "langchain-openai"]
        )

    def get_dependencies(self) -> list:
        """获取依赖"""
        return ["langchain", "langchain_openai"]

    def _analyze_satisfaction(self, user_message: str, ai_response: str) -> float:
        """分析客户满意度"""
        positive = ["谢谢", "好的", "明白了", "解决了", "满意", "很好", "太棒了", "感谢", "正确"]
        negative = ["不满意", "没用", "不懂", "还是不行", "不行", "不可以", "没有用", "垃圾", "太差"]

        for keyword in negative:
            if keyword in user_message:
                return 0.2

        for keyword in positive:
            if keyword in user_message:
                return 0.8

        return 0.5

    def _check_transfer_request(self, user_message: str) -> bool:
        """检查用户是否主动要求转人工"""
        transfer_keywords = ["转人工", "人工客服", "人工", "转人工服务", "找客服", "要人工", "接人工"]
        for keyword in transfer_keywords:
            if keyword in user_message:
                return True
        return False

    def _should_suggest_transfer(self, satisfaction_level: float) -> bool:
        """判断是否应该建议转人工"""
        cfg = self.TRANSFER_CONFIG

        if (self.conversation_turns >= cfg["max_turns_before_suggest"] and
                satisfaction_level < cfg["satisfaction_threshold"]):
            return True

        if (self.conversation_turns >= cfg["min_turns_for_satisfaction_trigger"] and
                satisfaction_level < cfg["satisfaction_threshold"]):
            return True

        return False

    def _get_transfer_suggestion(self) -> str:
        """获取转人工建议文本"""
        cfg = self.TRANSFER_CONFIG

        if self.conversation_turns >= cfg["max_turns_before_suggest"]:
            return "您已与AI客服交流了多轮，如果您的问题仍未解决，我可以为您转接人工客服。"

        if self.conversation_turns >= cfg["min_turns_for_satisfaction_trigger"]:
            return "看起来您可能对当前回答不太满意，需要为您转接人工客服吗？"

        return ""

    def clear_history(self, session_id: str = None):
        """清除对话历史"""
        self.conversation_history = []
        self.conversation_turns = 0
