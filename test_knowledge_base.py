import requests
import json

def test_knowledge_base():
    base_url = "http://localhost:8000"
    
    print("=== 测试知识库功能 ===")
    
    # 测试1: 获取知识库统计信息
    print("\n1. 测试 GET /api/knowledge/stats")
    try:
        response = requests.get(f"{base_url}/api/knowledge/stats")
        print(f"状态码: {response.status_code}")
        result = response.json()
        print(f"响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
    except Exception as e:
        print(f"失败: {e}")
    
    # 测试2: 添加文档到知识库
    print("\n2. 测试 POST /api/knowledge/add")
    test_document = """
    产品常见问题解答
    
    1. 如何注册账号？
    用户可以通过官网首页点击"注册"按钮，填写手机号码和验证码完成注册。注册成功后，系统会自动发送欢迎邮件。
    
    2. 如何修改密码？
    登录后，进入"个人中心"页面，点击"修改密码"按钮。输入原密码和新密码后，点击确认即可完成修改。
    
    3. 如何联系客服？
    您可以通过以下方式联系客服：
    - 在线客服：点击页面右下角的"在线客服"按钮
    - 电话客服：拨打400-123-4567
    - 邮件客服：发送邮件至support@example.com
    
    4. 退款政策
    购买产品后7天内，如对产品不满意，可申请全额退款。退款将在3-5个工作日内处理完成。
    
    5. 产品价格
    - 基础版：99元/月
    - 专业版：299元/月
    - 企业版：999元/月
    """
    
    try:
        payload = {
            "document_id": "faq_001",
            "content": test_document,
            "metadata": {
                "title": "产品常见问题解答",
                "category": "FAQ",
                "version": "1.0"
            }
        }
        response = requests.post(f"{base_url}/api/knowledge/add", json=payload)
        print(f"状态码: {response.status_code}")
        result = response.json()
        print(f"响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
    except Exception as e:
        print(f"失败: {e}")
    
    # 测试3: 获取文档列表
    print("\n3. 测试 GET /api/knowledge/documents")
    try:
        response = requests.get(f"{base_url}/api/knowledge/documents")
        print(f"状态码: {response.status_code}")
        result = response.json()
        print(f"响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
    except Exception as e:
        print(f"失败: {e}")
    
    # 测试4: 搜索知识库
    print("\n4. 测试 POST /api/knowledge/search")
    try:
        payload = {
            "query": "如何联系客服",
            "top_k": 3
        }
        response = requests.post(f"{base_url}/api/knowledge/search", json=payload)
        print(f"状态码: {response.status_code}")
        result = response.json()
        print(f"响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
    except Exception as e:
        print(f"失败: {e}")
    
    # 测试5: AI客服聊天（带知识库增强）
    print("\n5. 测试 POST /api/chat（知识库增强）")
    try:
        payload = {
            "session_id": "test_kb_session",
            "message": "我想了解一下退款政策"
        }
        response = requests.post(f"{base_url}/api/chat", json=payload)
        print(f"状态码: {response.status_code}")
        result = response.json()
        print(f"响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
        
        # 检查知识库是否被使用
        if result.get("knowledge_base_used"):
            print("\n✅ 知识库增强功能已启用！")
            print(f"知识来源: {result.get('knowledge_sources', [])}")
        else:
            print("\n⚠️ 知识库未被使用")
    except Exception as e:
        print(f"失败: {e}")
    
    # 测试6: 获取文档详情
    print("\n6. 测试 GET /api/knowledge/documents/{document_id}")
    try:
        response = requests.get(f"{base_url}/api/knowledge/documents/faq_001")
        print(f"状态码: {response.status_code}")
        result = response.json()
        print(f"响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
    except Exception as e:
        print(f"失败: {e}")
    
    # 测试7: 再次获取统计信息（查看变化）
    print("\n7. 测试 GET /api/knowledge/stats（查看变化）")
    try:
        response = requests.get(f"{base_url}/api/knowledge/stats")
        print(f"状态码: {response.status_code}")
        result = response.json()
        print(f"响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
    except Exception as e:
        print(f"失败: {e}")
    
    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    test_knowledge_base()