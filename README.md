# AI客服系统

## 项目概述

这是一个完整的网页AI客服系统，支持智能客服自动响应和人工客服转接功能。

## 功能特性

- ✅ AI客服自动响应
- ✅ 客户不满意时主动转人工
- ✅ 工单系统管理
- ✅ 客服接入功能
- ✅ 聊天记录保存
- ✅ 实时消息推送

## 系统流程

```
客户 → AI客服 → 客户不满意 → 客户主动要求转人工 
    → 系统发送工单给客服 → 客服接入 → 继续服务
```

## 技术栈

### 前端
- HTML5
- CSS3
- JavaScript (原生)
- WebSocket (实时通信)

### 后端
- Python 3.11+
- FastAPI (Web框架)
- LangChain (AI客服)
- WebSocket (实时通信)
- SQLite (数据库)

## 项目结构

```
ai-customer-service/
├── frontend/           # 前端代码
│   ├── index.html      # 客户聊天界面
│   ├── styles.css      # 样式文件
│   └── script.js       # 前端逻辑
├── backend/            # 后端代码
│   ├── main.py         # FastAPI主文件
│   ├── ai_service.py   # AI客服逻辑
│   ├── ticket_service.py # 工单管理
│   ├── config.py       # 配置文件
│   └── database.py     # 数据库操作
├── requirements.txt    # 依赖列表
└── README.md           # 项目说明
```

## 安装和运行

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

创建 `.env` 文件：
```
OPENAI_API_KEY=your_api_key_here
OPENAI_BASE_URL=https://api.openai.com/v1
```

### 3. 运行后端服务

```bash
cd backend
python main.py
```

### 4. 访问前端界面

打开浏览器访问：http://localhost:8000

## 使用说明

### 客户端使用
1. 打开网页，自动连接AI客服
2. 输入问题，AI客服自动响应
3. 如果不满意，点击"转人工客服"按钮
4. 系统自动创建工单，等待客服接入

### 客服端使用
1. 客服登录系统
2. 查看待处理工单列表
3. 点击工单接入客户
4. 开始人工服务

## API接口

### 客户端接口
- `POST /api/chat` - 发送消息
- `POST /api/request-human` - 请求转人工
- `GET /api/status` - 获取服务状态

### 客服端接口
- `GET /api/tickets` - 获取工单列表
- `POST /api/tickets/{id}/accept` - 接入工单
- `POST /api/tickets/{id}/close` - 关闭工单

## 数据库结构

### 聊天记录表 (chat_messages)
- id: 主键
- session_id: 会话ID
- user_type: 用户类型（客户/客服）
- message: 消息内容
- timestamp: 时间戳

### 工单表 (tickets)
- id: 主键
- session_id: 会话ID
- customer_id: 客户ID
- status: 工单状态（待处理/已接入/已关闭）
- created_at: 创建时间
- accepted_at: 接入时间
- closed_at: 关闭时间

## 配置说明

### AI客服配置
- 模型选择：GPT-3.5/GPT-4
- 温度参数：0.7
- 最大响应长度：1000字

### 工单系统配置
- 工单超时时间：30分钟
- 客服响应时间：5分钟内
- 自动关闭时间：24小时

## 开发计划

### 第一阶段（已完成）
- ✅ 基础聊天功能
- ✅ AI客服集成
- ✅ 转人工功能

### 第二阶段（进行中）
- 🔄 WebSocket实时通信
- 🔄 客服端界面
- 🔄 工单管理完善

### 第三阶段（计划中）
- ⏳ 多客服支持
- ⏳ 客服分配算法
- ⏳ 数据统计和分析

## 联系方式

如有问题，请提交Issue或联系开发团队。