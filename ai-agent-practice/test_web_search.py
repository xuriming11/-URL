"""
测试 SerpApi 网页搜索工具
"""
from dotenv import load_dotenv
import os

# 加载环境变量
load_dotenv()

# 导入搜索工具
from tools.web_search import search

def test_search():
    """测试搜索功能"""
    print("=" * 60)
    print("🔍 测试 SerpApi 网页搜索工具")
    print("=" * 60)
    
    # 检查API密钥
    api_key = os.getenv("SERPAPI_API_KEY")
    if not api_key or api_key == "your-serpapi-key":
        print("\n❌ 错误：SERPAPI_API_KEY 未配置！")
        print("\n请完成以下步骤：")
        print("1. 访问 https://serpapi.com/ 注册账号")
        print("2. 获取免费API密钥")
        print("3. 在 .env 文件中添加：SERPAPI_API_KEY=你的密钥")
        print("4. 重新运行此脚本")
        return
    
    # 执行搜索测试
    print(f"\n✅ SerpApi 已配置，API密钥: {api_key[:10]}...\n")
    
    # 测试搜索
    test_queries = [
        "人工智能最新发展",
        "Python教程"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n--- 测试 {i}: {query} ---")
        result = search(query)
        print(result)
        print()
    
    print("=" * 60)
    print("🎉 搜索工具测试完成！")
    print("=" * 60)

if __name__ == "__main__":
    test_search()
