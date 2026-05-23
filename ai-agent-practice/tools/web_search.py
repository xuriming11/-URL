import os
import sys

def search(query: str) -> str: 
    """ 
    网页搜索引擎工具。
    支持两种模式：
    1. SerpApi模式（需要API密钥）
    2. 本地模拟模式（无需API密钥，用于开发测试）
    """ 
    print(f"🔍 正在执行网页搜索: {query}") 
    
    # 检查是否配置了SerpApi
    api_key = os.getenv("SERPAPI_API_KEY")
    
    if api_key and api_key != "your-serpapi-key":
        return _search_with_serpapi(query, api_key)
    else:
        return _search_mock(query)

def _search_with_serpapi(query: str, api_key: str) -> str:
    """使用SerpApi进行真实搜索"""
    try:
        from serpapi import SerpApiClient
        
        params = { 
            "engine": "google", 
            "q": query, 
            "api_key": api_key, 
            "gl": "cn", 
            "hl": "zh-cn", 
        } 
        
        client = SerpApiClient(params) 
        results = client.get_dict() 
        
        # 智能解析搜索结果
        if "answer_box_list" in results: 
            return "\n".join(results["answer_box_list"]) 
        if "answer_box" in results and "answer" in results["answer_box"]: 
            return results["answer_box"]["answer"] 
        if "knowledge_graph" in results and "description" in results["knowledge_graph"]: 
            return results["knowledge_graph"]["description"] 
        if "organic_results" in results and results["organic_results"]: 
            snippets = [ 
                f"[{i+1}] {res.get('title', '')}\n{res.get('snippet', '')}" 
                for i, res in enumerate(results["organic_results"][:3]) 
            ] 
            return "\n\n".join(snippets) 
        
        return f"对不起，没有找到关于 '{query}' 的信息。" 
 
    except Exception as e: 
        return f"搜索时发生错误: {e}"

def _search_mock(query: str) -> str:
    """
    本地模拟搜索（用于开发测试）
    当没有配置SerpApi时使用此模式
    """
    # 模拟搜索结果数据库
    mock_results = {
        "人工智能": """
人工智能（Artificial Intelligence，AI）是计算机科学的一个分支，致力于研究、开发用于模拟、延伸和扩展人的智能的理论、方法、技术及应用系统。

发展历程：
1. 1956年：达特茅斯会议，AI概念诞生
2. 1980年代：专家系统盛行
3. 2010年代：深度学习革命
4. 2020年代：大语言模型时代

主要技术方向：
- 机器学习
- 深度学习
- 自然语言处理
- 计算机视觉
- 强化学习
        """,
        "Python教程": """
Python是一种高级通用编程语言，以简洁优雅的语法著称。

学习资源：
1. 官方文档：https://docs.python.org/3/
2. Python教程：https://www.w3schools.com/python/
3. 菜鸟教程：https://www.runoob.com/python/python-tutorial.html

入门步骤：
1. 安装Python解释器
2. 学习基本语法（变量、数据类型、控制流程）
3. 掌握函数和模块
4. 实践项目练习
        """,
        "天气": """
当前天气模拟：
- 北京：晴，25°C
- 上海：多云，28°C
- 广州：小雨，30°C

建议：出门前查看当地天气预报获取准确信息。
        """,
        "新闻": """
今日模拟新闻摘要：
1. 科技巨头发布新一代AI模型，性能提升30%
2. 新能源汽车销量持续增长，市场份额突破20%
3. 全球气候变化会议达成重要共识

获取最新新闻请访问新闻网站。
        """
    }
    
    # 查找匹配结果
    for keyword, result in mock_results.items():
        if keyword in query or query in keyword:
            return f"📚 搜索结果（模拟模式）:\n{result}"
    
    # 默认返回
    return f"""📚 搜索结果（模拟模式）:

关于 '{query}' 的信息：

由于当前未配置SerpApi，使用模拟数据。如需真实搜索，请：
1. 访问 https://serpapi.com/ 注册账号
2. 获取API密钥
3. 在 .env 文件中设置 SERPAPI_API_KEY=你的密钥
"""

# 测试函数
if __name__ == "__main__":
    print(search("人工智能"))
