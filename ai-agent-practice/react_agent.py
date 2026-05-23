"""
ReAct Agent 核心循环实现
包含完整的思考-行动-观察循环
"""
import os
import re
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

class ToolExecutor:
    """
    工具执行器 - 管理和执行可用工具
    """
    
    def __init__(self):
        self.tools = {
            "search": {
                "description": "搜索网页信息，获取最新知识",
                "function": search
            }
        }
    
    def getAvailableTools(self):
        """返回所有可用工具的描述"""
        tool_descriptions = []
        for name, info in self.tools.items():
            tool_descriptions.append(f"- {name}: {info['description']}")
        return "\n".join(tool_descriptions)
    
    def execute(self, tool_name: str, tool_input: str) -> str:
        """执行指定工具"""
        if tool_name not in self.tools:
            return f"错误: 未知工具 '{tool_name}'"
        
        try:
            result = self.tools[tool_name]["function"](tool_input)
            return str(result)
        except Exception as e:
            return f"工具执行错误: {str(e)}"
    
    def getTool(self, tool_name: str):
        """获取指定工具的函数"""
        if tool_name in self.tools:
            return self.tools[tool_name]["function"]
        return None

class ReActAgent: 
    def __init__(self, llm_client: HelloAgentsLLM, tool_executor: ToolExecutor, max_steps: int = 5): 
        self.llm_client = llm_client 
        self.tool_executor = tool_executor 
        self.max_steps = max_steps 
        self.history = [] 

    def run(self, question: str): 
        """ 
        运行ReAct智能体来回答一个问题。 
        """ 
        self.history = []  # 每次运行时重置历史记录 
        current_step = 0 

        while current_step < self.max_steps: 
            current_step += 1 
            print(f"\n--- 第 {current_step} 步 ---") 

            # 1. 格式化提示词 
            tools_desc = self.tool_executor.getAvailableTools() 
            history_str = "\n".join(self.history) 
            prompt = REACT_PROMPT_TEMPLATE.format( 
                tools=tools_desc, 
                question=question, 
                history=history_str 
            ) 

            # 2. 调用LLM进行思考 
            print("🧠 正在思考...")
            messages = [{"role": "user", "content": prompt}] 
            response_text = self.llm_client.think(messages=messages) 
            
            if not response_text: 
                print("❌ 错误: LLM未能返回有效响应。") 
                break 

            # 3. 解析LLM的输出 
            thought, action = self._parse_output(response_text) 
            
            if thought: 
                print(f"💭 思考: {thought}") 

            if not action: 
                print("⚠️ 警告:未能解析出有效的Action，流程终止。") 
                break 

            # 4. 执行Action 
            if action.startswith("Finish"): 
                # 如果是Finish指令，提取最终答案并结束 
                final_answer_match = re.match(r"Finish\[(.*)\]", action)
                if final_answer_match:
                    final_answer = final_answer_match.group(1)
                else:
                    final_answer = action.replace("Finish", "").strip("[] ")
                print(f"🎉 最终答案: {final_answer}") 
                return final_answer 
            
            tool_name, tool_input = self._parse_action(action) 
            if not tool_name or not tool_input: 
                print(f"⚠️ 警告:无效的Action格式: {action}")
                self.history.append(f"步骤{current_step}: 无效Action格式")
                continue 

            print(f"🎬 行动: {tool_name}[{tool_input}]") 
            
            tool_function = self.tool_executor.getTool(tool_name) 
            if not tool_function: 
                observation = f"❌ 错误:未找到名为 '{tool_name}' 的工具。" 
            else: 
                observation = tool_function(tool_input) # 调用真实工具
            
            # 观察结果的整合
            print(f"👀 观察: {observation[:100]}..." if len(str(observation)) > 100 else f"👀 观察: {observation}") 
            
            # 将本轮的Action和Observation添加到历史记录中 
            self.history.append(f"Action: {action}") 
            self.history.append(f"Observation: {observation}") 

        # 循环结束 
        print("已达到最大步数，流程终止。") 
        return None

    def _parse_output(self, text: str): 
        """解析LLM的输出，提取Thought和Action。 
        """ 
        # Thought: 匹配到 Action: 或文本末尾 
        thought_match = re.search(r"Thought:\s*(.*?)(?=\nAction:|$)", text, re.DOTALL) 
        # Action: 匹配到文本末尾 
        action_match = re.search(r"Action:\s*(.*?)$", text, re.DOTALL) 
        thought = thought_match.group(1).strip() if thought_match else None 
        action = action_match.group(1).strip() if action_match else None 
        return thought, action 
 
    def _parse_action(self, action_text: str): 
        """解析Action字符串，提取工具名称和输入。 
        """ 
        match = re.match(r"(\w+)\[(.*)\]", action_text, re.DOTALL) 
        if match: 
            return match.group(1), match.group(2) 
        return None, None

# 测试 ReActAgent
if __name__ == "__main__":
    # 初始化组件
    llm_client = HelloAgentsLLM()
    tool_executor = ToolExecutor()
    agent = ReActAgent(llm_client, tool_executor, max_steps=5)
    
    print("=" * 60)
    print("🎬 ReAct Agent 核心循环演示")
    print("=" * 60)
    
    # 测试问题
    test_questions = [
        "什么是人工智能？",
        "今天的新闻是什么？"
    ]
    
    for question in test_questions:
        print(f"\n\n📝 用户问题: {question}")
        answer = agent.run(question)
        print("\n" + "=" * 60)
