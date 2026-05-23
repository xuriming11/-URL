from dotenv import load_dotenv
import os

# 加载环境变量
load_dotenv()

# 获取AI服务提供商配置
ai_provider = os.getenv("AI_PROVIDER", "openai").lower()

def test_dashscope():
    """测试阿里云通义千问"""
    try:
        # 尝试新版API导入方式
        try:
            from dashscope import Generation
        except ImportError:
            from dashscope.api import Generation
        
        api_key = os.getenv("DASHSCOPE_API_KEY")
        
        if not api_key or api_key == "your-dashscope-key":
            print("❌ 通义千问：请先在.env文件中设置 DASHSCOPE_API_KEY")
            print("访问 https://dashscope.console.aliyun.com/ 获取API密钥")
            return False

        print(f"正在连接通义千问... (API Key: {api_key[:10]}...)")
        
        # 使用Generation API
        response = Generation.call(
            model="qwen-plus",
            prompt="你好！请说一句中文问候语",
            timeout=30
        )
        
        if response.status_code == 200:
            print("✅ 阿里云通义千问连接成功！")
            print("AI回复:", response.output.text)
            return True
        else:
            print(f"❌ API返回错误: {response.message}")
            return False
            
    except ImportError as e:
        print(f"❌ 导入错误: {str(e)}")
        print("请先安装dashscope: pip install dashscope")
        return False
    except Exception as e:
        print(f"❌ 通义千问连接失败: {str(e)}")
        return False

def test_openai():
    """测试OpenAI API"""
    try:
        from openai import OpenAI
        
        api_key = os.getenv("OPENAI_API_KEY")
        api_base = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
        
        if not api_key or api_key == "your-api-key-here":
            print("❌ OpenAI：请先设置 OPENAI_API_KEY")
            return False

        client = OpenAI(api_key=api_key, base_url=api_base)
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "你是一个乐于助人的助手"},
                {"role": "user", "content": "你好！请说一句中文问候语"}
            ],
            max_tokens=50,
            timeout=30
        )
        print("✅ OpenAI API连接成功！")
        print("AI回复:", response.choices[0].message.content.strip())
        return True
    except Exception as e:
        print(f"❌ OpenAI连接失败: {str(e)}")
        return False

if __name__ == "__main__":
    print(f"正在测试 {ai_provider} AI服务...\n")
    
    success = False
    if ai_provider == "openai":
        success = test_openai()
    elif ai_provider == "dashscope":
        success = test_dashscope()
    else:
        print(f"❌ 未知的AI提供商: {ai_provider}")
        print("支持的提供商: openai, dashscope")
    
    if success:
        print("\n🎉 AI服务配置成功！可以开始AI Agent实战了。")
    else:
        print("\n💡 请检查API密钥配置和网络连接")
