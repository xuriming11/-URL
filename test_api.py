import requests
import json

def test_api():
    base_url = "http://localhost:8000"
    
    print("=== 测试AI客服系统 API ===")
    
    # 测试1: 获取系统状态
    print("\n1. 测试 /api/status")
    try:
        response = requests.get(f"{base_url}/api/status")
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.json()}")
    except Exception as e:
        print(f"失败: {e}")
    
    # 测试2: AI客服聊天
    print("\n2. 测试 /api/chat")
    try:
        payload = {"session_id": "test_session_001", "message": "你好"}
        response = requests.post(f"{base_url}/api/chat", json=payload)
        print(f"状态码: {response.status_code}")
        result = response.json()
        print(f"响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
    except Exception as e:
        print(f"失败: {e}")
    
    # 测试3: AI客服聊天 - 转人工
    print("\n3. 测试 /api/chat - 转人工")
    try:
        payload = {"session_id": "test_session_001", "message": "转人工"}
        response = requests.post(f"{base_url}/api/chat", json=payload)
        print(f"状态码: {response.status_code}")
        result = response.json()
        print(f"响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
    except Exception as e:
        print(f"失败: {e}")
    
    # 测试4: 创建工单
    print("\n4. 测试 POST /api/tickets")
    try:
        payload = {
            "session_id": "test_session_001",
            "customer_id": "customer_001",
            "reason": "客户不满意，要求转人工"
        }
        response = requests.post(f"{base_url}/api/tickets", json=payload)
        print(f"状态码: {response.status_code}")
        result = response.json()
        print(f"响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
        
        if result.get("success") and "ticket_id" in result:
            ticket_id = result["ticket_id"]
            
            # 测试5: 获取工单列表
            print("\n5. 测试 GET /api/tickets")
            response = requests.get(f"{base_url}/api/tickets")
            print(f"状态码: {response.status_code}")
            result = response.json()
            print(f"响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
            
            # 测试6: 获取单个工单
            print(f"\n6. 测试 GET /api/tickets/{ticket_id}")
            response = requests.get(f"{base_url}/api/tickets/{ticket_id}")
            print(f"状态码: {response.status_code}")
            result = response.json()
            print(f"响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
            
            # 测试7: 更新工单状态
            print(f"\n7. 测试 PUT /api/tickets/{ticket_id}")
            payload = {"status": "processing", "agent_id": "agent_001"}
            response = requests.put(f"{base_url}/api/tickets/{ticket_id}", json=payload)
            print(f"状态码: {response.status_code}")
            result = response.json()
            print(f"响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
            
            # 测试8: 删除工单
            print(f"\n8. 测试 DELETE /api/tickets/{ticket_id}")
            response = requests.delete(f"{base_url}/api/tickets/{ticket_id}")
            print(f"状态码: {response.status_code}")
            result = response.json()
            print(f"响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
    
    except Exception as e:
        print(f"失败: {e}")
    
    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    test_api()