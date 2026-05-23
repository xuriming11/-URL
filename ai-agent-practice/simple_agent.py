"""
简单的AI Agent框架 - ReAct风格
结合LLM思考和工具使用
"""
import os
from dotenv import load_dotenv
from HelloAgentsLLM import HelloAgentsLLM
from tools.web_search import search

# 加载环境变量
load_dotenv()

# ReAct 提示词模板
REACT_PROMPT_TEMPLATE = """
请注意，你是一个有能力调用外部工具的智能助手。

可用工具如下:
{tools}

请严格按照以下格式进行回应:

Thought: 你的思考过程，用于分析问题、拆解任务和规划下一步行动。
Action: 你决定采取的行动，必须是以下格式之一:
- `{{tool_name}}[{{tool_input}}]` :调用一个可用工具。
- `Finish[最终答案]` :当你认为已经获得最终答案时。

当你收集到足够的信息，能够回答用户的最终问题时，你必须在Action:字段后使用 Finish[最终答案] 来输出最终答案。

现在，请开始解决以下问题:
Question: {question}
History: {history}
"""

class SimpleAgent:
    """
    一个简单的AI Agent，能够：
    1. 思考问题
    2. 决定是否需要搜索
    3. 调用工具获取信息
    4. 给出最终答案
    """
    
    def __init__(self):
        self.llm = HelloAgentsLLM()
        self.tools = {
            "search": {
                "description": "搜索网页信息，获取最新知识",
                "function": search
            }
        }
    
    def _format_tools(self):
        """将工具列表格式化为提示词中的描述"""
        tool_descriptions = []
        for name, info in self.tools.items():
            tool_descriptions.append(f"- {name}: {info['description']}")
        return "\n".join(tool_descriptions)
    
    def run(self, user_query: str, max_steps: int = 5):
        """
        运行Agent处理用户查询
        """
        print(f"🤖 用户提问: {user_query}")
        print("-" * 60)
        
        # 初始化历史记录
        history = ""
        
        # 思考-行动循环
        for step in range(max_steps):
            print(f"\n🔄 步骤 {step + 1}/{max_steps}")
            
            # 构建提示词
            prompt = REACT_PROMPT_TEMPLATE.format(
                tools=self._format_tools(),
                question=user_query,
                history=history
            )
            
            messages = [
                {"role": "system", "content": prompt}
            ]
            
            # 1. 思考阶段
            print("🧠 思考中...")
            response = self.llm.think(messages, temperature=0.1)
            
            if not response:
                print("❌ LLM调用失败")
                break
            
            # 2. 解析响应
            # 提取 Thought 和 Action
            thought = ""
            action = ""
            
            if "Thought:" in response:
                thought_start = response.find("Thought:") + 7
                action_start = response.find("Action:")
                if action_start > 0:
                    thought = response[thought_start:action_start].strip()
                else:
                    thought = response[thought_start:].strip()
            
            if "Action:" in response:
                action_start = response.find("Action:") + 7
                action = response[action_start:].strip()
            
            # 打印思考过程
            if thought:
                print(f"\n💭 思考: {thought}")
            
            # 3. 执行动作
            if action.startswith("Finish["):
                # 提取最终答案
                answer = action[7:-1].strip()
                print(f"\n✅ 最终回答: {answer}")
                break
            
            elif "[" in action and "]" in action:
                # 调用工具
                tool_name = action[:action.index("[")].strip()
                tool_input = action[action.index("[")+1 : action.index("]")].strip()
                
                print(f"\n🔍 调用工具: {tool_name}({tool_input})")
                
                if tool_name in self.tools:
                    tool_result = self.tools[tool_name]["function"](tool_input)
                    print(f"📊 工具返回: {tool_result[:100]}..." if len(tool_result) > 100 else f"📊 工具返回: {tool_result}")
                    
                    # 更新历史记录
                    history += f"\n工具调用: {tool_name}[{tool_input}]\n工具结果: {tool_result}"
                else:
                    print(f"❌ 未知工具: {tool_name}")
                    history += f"\n错误: 未知工具 {tool_name}"
            else:
                # 默认直接回答
                print(f"\n✅ 回答: {action}")
                break
        
        print("\n" + "-" * 60)
        print("🎯 Agent执行完成")

# 测试Agent
if __name__ == "__main__":
    agent = SimpleAgent()
    
    print("=" * 60)
    print("🎬 ReAct风格AI Agent演示")
    print("=" * 60)
    
    # 测试问题
    test_queries = [
        "什么是人工智能？",
        "Python是什么？"
    ]
    
    for query in test_queries:
        print(f"\n\n📝 问题: {query}")
        agent.run(query)
        print("\n" + "=" * 60)
