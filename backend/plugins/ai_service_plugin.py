"""
AI客服插件
提供智能客服响应功能，集成知识库增强
"""

import logging
from typing import Dict, Any, Optional
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from backend.plugin_interface import PluginInterface, PluginInfo
from backend.config import config


logger = logging.getLogger(__name__)


class AIServicePlugin(PluginInterface):
    """AI客服插件"""
    
    # 转人工触发配置
    TRANSFER_CONFIG = {
        "max_turns_before_suggest": 3,      # 3轮后建议转人工
        "satisfaction_threshold": 0.5,       # 满意度阈值50%
        "min_turns_for_satisfaction_trigger": 2,  # 至少2轮对话才触发满意度判断
    }
    
    def __init__(self):
        self.llm = None
        self.conversation_history = []
        self.conversation_turns = 0  # 对话轮次计数
        self.use_mock = False
        self.knowledge_base_plugin = None  # 知识库插件引用
        self.use_knowledge_base = True  # 是否使用知识库增强
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
- 优先使用知识库中的信息回答问题
"""
    
    def initialize(self, config: Dict[str, Any]) -> bool:
        """
        初始化AI客服插件
        
        Args:
            config: 插件配置
        
        Returns:
            bool: 初始化是否成功
        """
        try:
            api_key = config.get("api_key")
            
            # 配置知识库使用
            self.use_knowledge_base = config.get("use_knowledge_base", True)
            
            # 如果没有API密钥，使用模拟模式
            if not api_key or api_key.strip() == "":
                self.use_mock = True
                logger.info("未配置API密钥，使用模拟模式")
                logger.info("AI客服插件初始化成功（模拟模式）")
                return True
            
            # 初始化LangChain LLM
            self.llm = ChatOpenAI(
                model=config.get("model", "gpt-3.5-turbo"),
                temperature=config.get("temperature", 0.7),
                max_tokens=config.get("max_tokens", 1000),
                api_key=api_key,
                base_url=config.get("base_url")
            )
            
            logger.info("AI客服插件初始化成功")
            return True
            
        except Exception as e:
            logger.error(f"AI客服插件初始化失败: {e}")
            # 失败时回退到模拟模式
            self.use_mock = True
            logger.info("回退到模拟模式")
            return True
    
    def set_knowledge_base(self, knowledge_base_plugin):
        """
        设置知识库插件引用
        
        Args:
            knowledge_base_plugin: 知识库插件实例
        """
        self.knowledge_base_plugin = knowledge_base_plugin
        logger.info("知识库插件已关联")
    
    def _search_knowledge_base(self, query: str, top_k: int = 3) -> Optional[Dict[str, Any]]:
        """
        从知识库检索相关信息
        
        Args:
            query: 查询文本
            top_k: 返回数量
        
        Returns:
            Optional[Dict]: 检索结果
        """
        if not self.knowledge_base_plugin or not self.use_knowledge_base:
            return None
        
        try:
            result = self.knowledge_base_plugin.execute({
                "action": "search",
                "query": query,
                "top_k": top_k
            })
            
            if result.get("success") and result.get("results"):
                return result
            
        except Exception as e:
            logger.error(f"知识库检索失败: {e}")
        
        return None
    
    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行AI客服响应
        
        Args:
            input_data: 包含客户消息的输入数据
        
        Returns:
            Dict: AI响应结果
        """
        try:
            # 获取客户消息
            user_message = input_data.get("message", "")
            session_id = input_data.get("session_id", "")
            
            # 检查是否用户主动要求转人工
            user_requested_transfer = self._check_transfer_request(user_message)
            
            # 从知识库检索相关信息
            kb_result = self._search_knowledge_base(user_message)
            kb_context = ""
            kb_sources = []
            
            if kb_result and kb_result.get("results"):
                # 构建知识库上下文
                kb_context = "\n\n【知识库相关信息】\n"
                for i, item in enumerate(kb_result["results"], 1):
                    kb_context += f"{i}. {item['parent_content']}\n"
                    kb_sources.append({
                        "parent_id": item.get("parent_id"),
                        "rerank_score": item.get("rerank_score"),
                        "matched_child": item.get("matched_child")
                    })
            
            # 模拟模式响应
            if self.use_mock:
                # 如果有知识库结果，优先使用
                if kb_context:
                    mock_response = self._get_knowledge_enhanced_mock_response(user_message, kb_context)
                else:
                    mock_response = self._get_mock_response(user_message)
                
                # 更新轮次计数
                self.conversation_turns += 1
                
                # 保存对话历史
                self.conversation_history.append(HumanMessage(content=user_message))
                self.conversation_history.append(AIMessage(content=mock_response))
                
                # 分析客户满意度
                satisfaction_level = self._analyze_satisfaction(user_message, mock_response)
                
                # 判断是否建议转人工（不包含用户主动请求）
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
                    "knowledge_base_used": bool(kb_context),
                    "knowledge_sources": kb_sources,
                    "mode": "mock"
                }
            
            # 构建消息历史
            enhanced_prompt = self.system_prompt
            if kb_context:
                enhanced_prompt += f"\n\n以下是知识库中检索到的相关信息，请优先参考这些内容回答：\n{kb_context}"
            
            messages = [
                SystemMessage(content=enhanced_prompt),
                HumanMessage(content=user_message)
            ]
            
            # 添加历史对话
            if self.conversation_history:
                messages.extend(self.conversation_history[-10:])  # 只保留最近10条
            
            # 调用AI模型
            response = self.llm.invoke(messages)
            
            # 更新轮次计数
            self.conversation_turns += 1
            
            # 保存对话历史
            self.conversation_history.append(HumanMessage(content=user_message))
            self.conversation_history.append(AIMessage(content=response.content))
            
            # 分析客户满意度
            satisfaction_level = self._analyze_satisfaction(user_message, response.content)
            
            # 判断是否建议转人工（不包含用户主动请求）
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
                "knowledge_base_used": bool(kb_context),
                "knowledge_sources": kb_sources,
                "mode": "real"
            }
            
        except Exception as e:
            logger.error(f"AI客服执行失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "response": "抱歉，我暂时无法回答您的问题，建议您转人工客服。"
            }
    
    def _get_knowledge_enhanced_mock_response(self, user_message: str, kb_context: str) -> str:
        """
        获取知识库增强的模拟响应
        
        Args:
            user_message: 客户消息
            kb_context: 知识库上下文
        
        Returns:
            str: 增强的模拟响应
        """
        # 提取知识库中的关键信息
        kb_info = kb_context.replace("\n\n【知识库相关信息】\n", "").strip()
        
        # 如果知识库有相关信息，使用它
        if kb_info:
            return f"根据我们的知识库信息，关于您的问题：\n\n{kb_info}\n\n如果您需要更详细的信息或有其他问题，请随时告诉我。如需转人工客服，请回复\"转人工\"。"
        
        # 否则使用默认模拟响应
        return self._get_mock_response(user_message)
    
    def _get_mock_response(self, user_message: str) -> str:
        """
        获取模拟响应
        
        Args:
            user_message: 客户消息
        
        Returns:
            str: 模拟响应
        """
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
        
        # 查找匹配的响应
        for keyword, response in mock_responses.items():
            if keyword in user_message:
                return response
        
        # 默认响应
        return f"您好！感谢您的咨询。您说的是：\"{user_message}\"。这是一个模拟响应，当配置了API密钥后，将提供更智能的回答。如需转人工客服，请回复\"转人工\"。"
    
    def shutdown(self) -> bool:
        """
        关闭AI客服插件
        
        Returns:
            bool: 关闭是否成功
        """
        try:
            # 清理对话历史
            self.conversation_history = []
            
            logger.info("AI客服插件关闭成功")
            return True
            
        except Exception as e:
            logger.error(f"AI客服插件关闭失败: {e}")
            return False
    
    def get_info(self) -> PluginInfo:
        """
        获取插件信息
        
        Returns:
            PluginInfo: 插件信息
        """
        return PluginInfo(
            name="ai_service_plugin",
            version="1.0.0",
            description="AI客服智能响应插件",
            author="AI客服团队",
            dependencies=["langchain", "langchain-openai"]
        )
    
    def _analyze_satisfaction(self, user_message: str, ai_response: str) -> float:
        """
        分析客户满意度
        
        Args:
            user_message: 客户消息
            ai_response: AI响应
        
        Returns:
            float: 满意度评分 (0-1)
        """
        # 满意度分析关键词
        satisfaction_keywords = {
            "positive": ["谢谢", "好的", "明白了", "解决了", "满意", "很好", "太棒了", "感谢", "正确"],
            "negative": ["不满意", "没用", "不懂", "还是不行", "不行", "不可以", "没有用", "垃圾", "太差"]
        }
        
        # 检查负面关键词
        for keyword in satisfaction_keywords["negative"]:
            if keyword in user_message:
                return 0.2
        
        # 检查正面关键词
        for keyword in satisfaction_keywords["positive"]:
            if keyword in user_message:
                return 0.8
        
        # 默认满意度
        return 0.5
    
    def _check_transfer_request(self, user_message: str) -> bool:
        """
        检查用户是否主动要求转人工
        
        Args:
            user_message: 客户消息
        
        Returns:
            bool: 是否主动要求转人工
        """
        transfer_keywords = ["转人工", "人工客服", "人工", "转人工服务", "找客服", "要人工", "接人工"]
        
        for keyword in transfer_keywords:
            if keyword in user_message:
                return True
        
        return False
    
    def _should_suggest_transfer(self, satisfaction_level: float) -> bool:
        """
        判断是否应该建议转人工
        
        触发条件（满足任一即建议）：
        1. 轮次触发：对话达到3轮且满意度<50%
        2. 满意度触发：满意度<50%且对话>=2轮
        
        Args:
            satisfaction_level: 满意度评分
        
        Returns:
            bool: 是否建议转人工
        """
        cfg = self.TRANSFER_CONFIG
        
        # 轮次触发：达到最大轮次且满意度低于阈值
        if (self.conversation_turns >= cfg["max_turns_before_suggest"] and 
            satisfaction_level < cfg["satisfaction_threshold"]):
            return True
        
        # 满意度触发：满意度低且达到最小轮次
        if (self.conversation_turns >= cfg["min_turns_for_satisfaction_trigger"] and 
            satisfaction_level < cfg["satisfaction_threshold"]):
            return True
        
        return False
    
    def _get_transfer_suggestion(self) -> str:
        """
        获取转人工建议文本
        
        Returns:
            str: 建议文本，如果没有建议则返回空字符串
        """
        cfg = self.TRANSFER_CONFIG
        
        if self.conversation_turns >= cfg["max_turns_before_suggest"]:
            return "您已与AI客服交流了多轮，如果您的问题仍未解决，我可以为您转接人工客服。"
        
        if self.conversation_turns >= cfg["min_turns_for_satisfaction_trigger"]:
            return "看起来您可能对当前回答不太满意，需要为您转接人工客服吗？"
        
        return ""
    
    def clear_history(self, session_id: str = None):
        """
        清除对话历史
        
        Args:
            session_id: 会话ID（可选）
        """
        self.conversation_history = []
        self.conversation_turns = 0  # 重置轮次计数