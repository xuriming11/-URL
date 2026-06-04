import requests

print('=== 测试客户数据 API ===')
r1 = requests.get('http://localhost:8000/api/customers')
data = r1.json()
print(f'客户列表: {len(data['customers'])} 个客户')

print('\n=== 获取 VIP 客户 ===')
r2 = requests.get('http://localhost:8000/api/customers?vip_level=gold')
data = r2.json()
names = [c['name'] for c in data['customers']]
print(f'黄金会员: {names}')

print('\n=== 获取产品分类 ===')
r3 = requests.get('http://localhost:8000/api/categories')
data = r3.json()
names = [c['name'] for c in data['categories']]
print(f'分类: {names}')

print('\n=== 搜索产品 ===')
r4 = requests.get('http://localhost:8000/api/products?keyword=耳机')
data = r4.json()
names = [p['name'] for p in data['products']]
print(f'搜索结果: {names}')

print('\n=== 获取客户订单历史 ===')
r5 = requests.get('http://localhost:8000/api/customers/C001/orders')
data = r5.json()
print(f'{data['customer_name']} 的订单数: {len(data['orders'])}')