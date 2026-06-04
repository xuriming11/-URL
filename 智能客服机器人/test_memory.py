import requests

print('=== 测试关键词记忆功能 ===')

r1 = requests.post('http://localhost:8000/chat_sync', json={'prompt': '我想买一台笔记本电脑，预算8000元'})
session_id = r1.json()['session_id']
print(f'会话ID: {session_id}')
response = r1.json()['response']
print(f'响应: {response[:50]}...')

r2 = requests.post('http://localhost:8000/chat_sync', json={'prompt': '推荐一些适合编程的型号', 'session_id': session_id})
response = r2.json()['response']
print(f'响应: {response[:50]}...')

r3 = requests.post('http://localhost:8000/chat_sync', json={'prompt': '有没有性价比高的选择？', 'session_id': session_id})
response = r3.json()['response']
print(f'响应: {response[:50]}...')

print('\n=== 查看记忆中的关键词 ===')
r4 = requests.get('http://localhost:8000/memory/keywords')
print(f'关键词列表: {r4.json()}')

print('\n=== 搜索关键词「笔记本」===')
r5 = requests.get('http://localhost:8000/memory/search?keyword=笔记本')
print(f'搜索结果: {r5.json()}')

print('\n=== 关键词统计 ===')
r6 = requests.get('http://localhost:8000/memory/keywords/stats')
print(f'统计结果: {r6.json()}')