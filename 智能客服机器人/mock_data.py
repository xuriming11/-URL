from typing import List, Dict, Optional
from datetime import datetime, timedelta
import random

customers = [
    {
        "id": "C001",
        "name": "张三",
        "phone": "13800138001",
        "email": "zhangsan@example.com",
        "address": "北京市朝阳区建国路88号",
        "register_date": "2024-01-15",
        "vip_level": "gold",
        "total_spent": 28600.00
    },
    {
        "id": "C002",
        "name": "李四",
        "phone": "13800138002",
        "email": "lisi@example.com",
        "address": "上海市浦东新区陆家嘴环路1000号",
        "register_date": "2024-03-20",
        "vip_level": "silver",
        "total_spent": 12500.00
    },
    {
        "id": "C003",
        "name": "王五",
        "phone": "13800138003",
        "email": "wangwu@example.com",
        "address": "广州市天河区珠江新城",
        "register_date": "2024-05-10",
        "vip_level": "gold",
        "total_spent": 45800.00
    },
    {
        "id": "C004",
        "name": "赵六",
        "phone": "13800138004",
        "email": "zhaoliu@example.com",
        "address": "深圳市南山区科技园",
        "register_date": "2024-06-18",
        "vip_level": "bronze",
        "total_spent": 3200.00
    },
    {
        "id": "C005",
        "name": "孙七",
        "phone": "13800138005",
        "email": "sunqi@example.com",
        "address": "杭州市西湖区文三路",
        "register_date": "2024-07-22",
        "vip_level": "gold",
        "total_spent": 56200.00
    },
    {
        "id": "C006",
        "name": "周八",
        "phone": "13800138006",
        "email": "zhouba@example.com",
        "address": "成都市锦江区春熙路",
        "register_date": "2024-08-05",
        "vip_level": "silver",
        "total_spent": 8900.00
    },
    {
        "id": "C007",
        "name": "吴九",
        "phone": "13800138007",
        "email": "wujiu@example.com",
        "address": "武汉市江汉区解放大道",
        "register_date": "2024-09-12",
        "vip_level": "bronze",
        "total_spent": 1500.00
    },
    {
        "id": "C008",
        "name": "郑十",
        "phone": "13800138008",
        "email": "zhengshi@example.com",
        "address": "南京市鼓楼区新街口",
        "register_date": "2024-10-08",
        "vip_level": "gold",
        "total_spent": 78900.00
    },
    {
        "id": "C009",
        "name": "钱十一",
        "phone": "13800138009",
        "email": "qianshiyi@example.com",
        "address": "西安市雁塔区科技路",
        "register_date": "2024-11-01",
        "vip_level": "silver",
        "total_spent": 15600.00
    },
    {
        "id": "C010",
        "name": "刘十二",
        "phone": "13800138010",
        "email": "liushier@example.com",
        "address": "重庆市渝中区解放碑",
        "register_date": "2024-11-15",
        "vip_level": "gold",
        "total_spent": 95200.00
    },
    {
        "id": "C011",
        "name": "陈十三",
        "phone": "13800138011",
        "email": "chenshisan@example.com",
        "address": "天津市和平区南京路",
        "register_date": "2024-12-01",
        "vip_level": "bronze",
        "total_spent": 2800.00
    },
    {
        "id": "C012",
        "name": "杨十四",
        "phone": "13800138012",
        "email": "yangshisi@example.com",
        "address": "苏州市工业园区金鸡湖大道",
        "register_date": "2024-12-10",
        "vip_level": "silver",
        "total_spent": 18900.00
    },
    {
        "id": "C013",
        "name": "黄十五",
        "phone": "13800138013",
        "email": "huangshiwu@example.com",
        "address": "厦门市思明区中山路",
        "register_date": "2025-01-05",
        "vip_level": "gold",
        "total_spent": 67500.00
    },
    {
        "id": "C014",
        "name": "林十六",
        "phone": "13800138014",
        "email": "linshiliu@example.com",
        "address": "长沙市芙蓉区五一广场",
        "register_date": "2025-01-20",
        "vip_level": "bronze",
        "total_spent": 4200.00
    },
    {
        "id": "C015",
        "name": "何十七",
        "phone": "13800138015",
        "email": "heshishi@example.com",
        "address": "青岛市市南区五四广场",
        "register_date": "2025-02-01",
        "vip_level": "gold",
        "total_spent": 88000.00
    },
    {
        "id": "C016",
        "name": "马十八",
        "phone": "13800138016",
        "email": "mashiba@example.com",
        "address": "大连市中山区人民路",
        "register_date": "2025-02-15",
        "vip_level": "silver",
        "total_spent": 22300.00
    }
]

products = [
    {
        "id": "P001",
        "name": "笔记本电脑 Pro",
        "category": "电子产品",
        "price": 8999.00,
        "stock": 156,
        "description": "高性能商务笔记本，搭载最新处理器",
        "brand": "TechPro"
    },
    {
        "id": "P002",
        "name": "无线蓝牙耳机",
        "category": "电子产品",
        "price": 599.00,
        "stock": 892,
        "description": "主动降噪，长续航",
        "brand": "SoundMax"
    },
    {
        "id": "P003",
        "name": "机械键盘",
        "category": "外设",
        "price": 399.00,
        "stock": 423,
        "description": "RGB背光，青轴手感",
        "brand": "KeyMaster"
    },
    {
        "id": "P004",
        "name": "游戏鼠标",
        "category": "外设",
        "price": 299.00,
        "stock": 567,
        "description": "高精度传感器，可编程按键",
        "brand": "GameStar"
    },
    {
        "id": "P005",
        "name": "便携显示器",
        "category": "电子产品",
        "price": 1299.00,
        "stock": 89,
        "description": "15.6英寸，1080P分辨率",
        "brand": "ViewTech"
    },
    {
        "id": "P006",
        "name": "USB-C扩展坞",
        "category": "配件",
        "price": 459.00,
        "stock": 312,
        "description": "7合1多功能扩展",
        "brand": "ConnectX"
    },
    {
        "id": "P007",
        "name": "无线充电器",
        "category": "配件",
        "price": 159.00,
        "stock": 745,
        "description": "15W快充，支持多设备",
        "brand": "PowerUp"
    },
    {
        "id": "P008",
        "name": "人体工学椅",
        "category": "办公家具",
        "price": 1899.00,
        "stock": 45,
        "description": "透气网布，可调节腰托",
        "brand": "ErgoFit"
    },
    {
        "id": "P009",
        "name": "显示器支架",
        "category": "办公家具",
        "price": 359.00,
        "stock": 234,
        "description": "双臂设计，自由升降",
        "brand": "StandPro"
    },
    {
        "id": "P010",
        "name": "降噪耳机",
        "category": "电子产品",
        "price": 1599.00,
        "stock": 167,
        "description": "头戴式，深度降噪",
        "brand": "SoundMax"
    }
]

orders = [
    {
        "id": "O0001",
        "customer_id": "C001",
        "items": [{"product_id": "P001", "quantity": 1, "price": 8999.00}],
        "total_amount": 8999.00,
        "status": "completed",
        "order_date": "2024-11-01 10:30:00",
        "shipping_address": "北京市朝阳区建国路88号"
    },
    {
        "id": "O0002",
        "customer_id": "C001",
        "items": [{"product_id": "P003", "quantity": 1, "price": 399.00}, {"product_id": "P004", "quantity": 1, "price": 299.00}],
        "total_amount": 698.00,
        "status": "completed",
        "order_date": "2024-11-15 14:20:00",
        "shipping_address": "北京市朝阳区建国路88号"
    },
    {
        "id": "O0003",
        "customer_id": "C003",
        "items": [{"product_id": "P001", "quantity": 2, "price": 8999.00}],
        "total_amount": 17998.00,
        "status": "completed",
        "order_date": "2024-11-05 09:15:00",
        "shipping_address": "广州市天河区珠江新城"
    },
    {
        "id": "O0004",
        "customer_id": "C005",
        "items": [{"product_id": "P008", "quantity": 1, "price": 1899.00}, {"product_id": "P009", "quantity": 1, "price": 359.00}],
        "total_amount": 2258.00,
        "status": "shipped",
        "order_date": "2024-11-20 16:45:00",
        "shipping_address": "杭州市西湖区文三路"
    },
    {
        "id": "O0005",
        "customer_id": "C008",
        "items": [{"product_id": "P001", "quantity": 1, "price": 8999.00}, {"product_id": "P010", "quantity": 1, "price": 1599.00}, {"product_id": "P006", "quantity": 1, "price": 459.00}],
        "total_amount": 11057.00,
        "status": "processing",
        "order_date": "2024-11-22 08:30:00",
        "shipping_address": "南京市鼓楼区新街口"
    },
    {
        "id": "O0006",
        "customer_id": "C002",
        "items": [{"product_id": "P002", "quantity": 2, "price": 599.00}],
        "total_amount": 1198.00,
        "status": "pending",
        "order_date": "2024-11-23 11:00:00",
        "shipping_address": "上海市浦东新区陆家嘴环路1000号"
    },
    {
        "id": "O0007",
        "customer_id": "C004",
        "items": [{"product_id": "P007", "quantity": 3, "price": 159.00}],
        "total_amount": 477.00,
        "status": "completed",
        "order_date": "2024-11-18 13:20:00",
        "shipping_address": "深圳市南山区科技园"
    },
    {
        "id": "O0008",
        "customer_id": "C006",
        "items": [{"product_id": "P005", "quantity": 1, "price": 1299.00}],
        "total_amount": 1299.00,
        "status": "shipped",
        "order_date": "2024-11-21 17:50:00",
        "shipping_address": "成都市锦江区春熙路"
    }
]

categories = [
    {"id": "CAT001", "name": "电子产品", "description": "各类电子设备"},
    {"id": "CAT002", "name": "外设", "description": "电脑外设配件"},
    {"id": "CAT003", "name": "配件", "description": "各类配件"},
    {"id": "CAT004", "name": "办公家具", "description": "办公相关家具"}
]

def get_all_customers() -> List[Dict]:
    return customers

def get_customer_by_id(customer_id: str) -> Optional[Dict]:
    return next((c for c in customers if c["id"] == customer_id), None)

def get_customers_by_vip_level(vip_level: str) -> List[Dict]:
    return [c for c in customers if c["vip_level"] == vip_level]

def search_customers(keyword: str) -> List[Dict]:
    keyword = keyword.lower()
    return [c for c in customers if keyword in c["name"].lower() or keyword in c["phone"] or keyword in c["email"].lower()]

def get_all_products() -> List[Dict]:
    return products

def get_product_by_id(product_id: str) -> Optional[Dict]:
    return next((p for p in products if p["id"] == product_id), None)

def get_products_by_category(category: str) -> List[Dict]:
    return [p for p in products if p["category"] == category]

def search_products(keyword: str) -> List[Dict]:
    keyword = keyword.lower()
    return [p for p in products if keyword in p["name"].lower() or keyword in p["description"].lower()]

def get_all_orders() -> List[Dict]:
    return orders

def get_order_by_id(order_id: str) -> Optional[Dict]:
    return next((o for o in orders if o["id"] == order_id), None)

def get_orders_by_customer(customer_id: str) -> List[Dict]:
    return [o for o in orders if o["customer_id"] == customer_id]

def get_orders_by_status(status: str) -> List[Dict]:
    return [o for o in orders if o["status"] == status]

def get_all_categories() -> List[Dict]:
    return categories

def get_customer_order_history(customer_id: str) -> List[Dict]:
    customer_orders = get_orders_by_customer(customer_id)
    result = []
    for order in customer_orders:
        order_items = []
        for item in order["items"]:
            product = get_product_by_id(item["product_id"])
            if product:
                order_items.append({
                    "product_name": product["name"],
                    "quantity": item["quantity"],
                    "price": item["price"]
                })
        result.append({
            "order_id": order["id"],
            "order_date": order["order_date"],
            "total_amount": order["total_amount"],
            "status": order["status"],
            "items": order_items
        })
    return sorted(result, key=lambda x: x["order_date"], reverse=True)