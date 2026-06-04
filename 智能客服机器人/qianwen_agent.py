from typing import Optional
import dashscope
from config import config
from agent_state import AgentState
from memory_tools import remember_user_question, recall_related_info
from mock_data import get_customer_by_id, get_customer_order_history

dashscope.api_key = config.QIANWEN_API_KEY

def get_customer_info(customer_id: str) -> str:
    customer = get_customer_by_id(customer_id)
    if not customer:
        return ""
    
    orders = get_customer_order_history(customer_id)
    
    info = f"客户信息：\n"
    info += f"- 姓名：{customer['name']}\n"
    info += f"- VIP等级：{customer['vip_level']}\n"
    info += f"- 累计消费：¥{customer['total_spent']}\n"
    info += f"- 注册日期：{customer['register_date']}\n"
    
    if orders:
        info += f"\n订单历史（共{len(orders)}个订单）：\n"
        for order in orders[:3]:
            info += f"- 订单号：{order['order_id']}，金额：¥{order['total_amount']}，状态：{order['status']}\n"
        if len(orders) > 3:
            info += f"- ...还有{len(orders)-3}个订单\n"
    
    return info

def get_order_answer(customer_id: str, prompt: str) -> Optional[str]:
    order_keywords = ['订单', '商品', '购买', '购物', '消费', '买了', '买过', '发货', '物流', '退货', '退款', '退换']
    
    if not any(keyword in prompt for keyword in order_keywords):
        return None
    
    customer = get_customer_by_id(customer_id)
    if not customer:
        return None
    
    orders = get_customer_order_history(customer_id)
    
    answer = f"您好{customer['name']}，根据您的账户信息：\n\n"
    
    if '消费' in prompt or '多少钱' in prompt or '累计' in prompt:
        answer += f"您的累计消费金额为：¥{customer['total_spent']}"
        return answer
    
    if not orders:
        answer += "您目前没有订单记录。"
        return answer
    
    if '退货' in prompt or '退款' in prompt or '退换' in prompt:
        eligible_orders = [o for o in orders if o['status'] in ['shipped', 'completed']]
        
        if not eligible_orders:
            answer += "抱歉，您目前没有可退货的订单。\n"
            answer += "可退货订单需要是已发货或已完成状态。"
            return answer
        
        answer += "以下是您可申请退货的订单：\n"
        for order in eligible_orders:
            answer += f"\n订单号：{order['order_id']}\n"
            answer += f"下单时间：{order['order_date']}\n"
            answer += f"订单金额：¥{order['total_amount']}\n"
            answer += "购买商品：\n"
            for item in order['items']:
                answer += f"  - {item['product_name']} x {item['quantity']}\n"
        
        answer += "\n如需退货，请提供订单号，我将为您处理退货申请。"
        return answer
    
    if '订单' in prompt or '商品' in prompt or '买了' in prompt or '买过' in prompt:
        answer += f"您共有 {len(orders)} 个订单：\n"
        for order in orders:
            answer += f"\n订单号：{order['order_id']}\n"
            answer += f"下单时间：{order['order_date']}\n"
            answer += f"订单金额：¥{order['total_amount']}\n"
            answer += f"订单状态：{order['status']}\n"
            answer += "购买商品：\n"
            for item in order['items']:
                answer += f"  - {item['product_name']} x {item['quantity']}\n"
        return answer
    
    if '发货' in prompt or '物流' in prompt or '状态' in prompt:
        answer += "您的订单状态如下：\n"
        for order in orders:
            status_text = {
                'completed': '已完成',
                'shipped': '已发货',
                'processing': '处理中',
                'pending': '待付款'
            }.get(order['status'], order['status'])
            answer += f"订单号 {order['order_id']}：{status_text}\n"
        return answer
    
    return None

def build_prompt_with_history(state: AgentState, new_prompt: str, customer_id: str = None) -> str:
    history = state.get_history()
    prompt_parts = []
    
    system_prompt = """
你是一位专业、友好、有同理心的智能客服助手，名叫小助手。

## 你的角色与目标：
- 你是客户的贴心服务伙伴，始终保持微笑和耐心
- 用自然、亲切的语言与客户交流，就像面对面聊天一样
- 理解客户的真实需求，提供贴心的解决方案
- 让每个客户都感受到被重视和尊重

## 沟通风格：
- 使用温暖、友好的语气，避免生硬的机械感
- 适当使用表情符号增加亲和力，但不要过度
- 保持回答简洁明了，同时富有同理心
- 称呼客户的名字（如果知道的话），增加亲切感

## 核心原则：
1. **客户至上**：客户的需求是第一位的
2. **积极主动**：主动提供帮助和建议
3. **真诚透明**：如实告知客户情况
4. **专业可靠**：提供准确、有价值的信息

## 能力范围：
- 查询订单状态和历史
- 处理退货退款申请
- 解答产品相关问题
- 提供会员服务咨询
- 处理客户投诉和建议

## 禁忌事项：
- 不讨论敏感话题
- 不泄露客户隐私
- 不发表攻击性言论
- 不承诺无法兑现的事情

【当前客户信息】
"""
    
    if customer_id:
        customer_info = get_customer_info(customer_id)
        if customer_info:
            system_prompt += customer_info
        else:
            system_prompt += "暂无客户信息\n"
    else:
        system_prompt += "暂无客户信息\n"
    
    system_prompt += "\n【对话历史】\n"
    
    prompt_parts.append(system_prompt)
    
    for msg in history:
        role = "用户" if msg["role"] == "user" else "助手"
        prompt_parts.append(f"{role}: {msg['content']}")
    
    prompt_parts.append(f"用户: {new_prompt}")
    prompt_parts.append("助手:")
    
    return "\n".join(prompt_parts)

async def chat_with_qianwen(state: AgentState, prompt: str, customer_id: str = None) -> str:
    remember_user_question(state.session_id, prompt)
    
    if customer_id:
        order_answer = get_order_answer(customer_id, prompt)
        if order_answer:
            return order_answer
    
    related_info = recall_related_info(state.session_id, prompt)
    
    full_prompt = build_prompt_with_history(state, prompt, customer_id)
    
    if related_info:
        full_prompt = f"{related_info}\n\n{full_prompt}"
    
    response = dashscope.Generation.call(
        model=config.QIANWEN_MODEL_NAME,
        prompt=full_prompt,
        temperature=config.TEMPERATURE,
        max_tokens=config.MAX_TOKENS
    )
    
    if response.status_code == 200:
        result = response.output
        if hasattr(result, 'text') and result.text:
            return result.text.strip()
        raise Exception("Unexpected response format - no text field")
    else:
        raise Exception(f"API request failed: {response.message}")

def chat_with_qianwen_sync(state: AgentState, prompt: str, customer_id: str = None) -> str:
    remember_user_question(state.session_id, prompt)
    
    if customer_id:
        order_answer = get_order_answer(customer_id, prompt)
        if order_answer:
            return order_answer
    
    related_info = recall_related_info(state.session_id, prompt)
    
    full_prompt = build_prompt_with_history(state, prompt, customer_id)
    
    if related_info:
        full_prompt = f"{related_info}\n\n{full_prompt}"
    
    response = dashscope.Generation.call(
        model=config.QIANWEN_MODEL_NAME,
        prompt=full_prompt,
        temperature=config.TEMPERATURE,
        max_tokens=config.MAX_TOKENS
    )
    
    if response.status_code == 200:
        result = response.output
        if hasattr(result, 'text') and result.text:
            return result.text.strip()
        raise Exception("Unexpected response format - no text field")
    else:
        raise Exception(f"API request failed: {response.message}")