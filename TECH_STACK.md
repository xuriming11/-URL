# AI客服系统 - 技术栈文档

## 一、项目概述

本项目是一个基于 **MCP（Model Context Protocol）协议** 的插件式AI客服系统，提供智能对话、知识库管理、用户画像、数据分析等核心功能。

**项目定位**：可插拔、易扩展的企业级AI客服解决方案

---

## 二、技术架构

```
┌─────────────────────────────────────────────────────────────┐
│                    AI客服系统架构                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   Frontend Layer                                            │
│   ┌─────────────────────────────────────────────────────┐   │
│   │  HTML5 + CSS3 + JavaScript (ES6+)                    │   │
│   │  响应式设计 · 移动端适配 · 实时聊天                    │   │
│   └─────────────────────────────────────────────────────┘   │
│                           │                                 │
│                           ▼                                 │
│   API Layer                                                 │
│   ┌─────────────────────────────────────────────────────┐   │
│   │  FastAPI + Uvicorn                                   │   │
│   │  RESTful API · WebSocket · Async Support             │   │
│   └─────────────────────────────────────────────────────┘   │
│                           │                                 │
│                           ▼                                 │
│   Plugin Layer                                              │
│   ┌─────────────────────────────────────────────────────┐   │
│   │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐ │   │
│   │  │ AI Service  │  │ Knowledge   │  │   Ticket    │ │   │
│   │  │   Plugin    │  │   Base      │  │   Manager   │ │   │
│   │  │             │  │   Plugin    │  │   Plugin    │ │   │
│   │  └─────────────┘  └─────────────┘  └─────────────┘ │   │
│   └─────────────────────────────────────────────────────┘   │
│                           │                                 │
│                           ▼                                 │
│   AI Layer                                                  │
│   ┌─────────────────────────────────────────────────────┐   │
│   │  LangChain + OpenAI API                              │   │
│   │  Intent Recognition · Context Management             │   │
│   │  Knowledge Retrieval · Transfer Logic               │   │
│   └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 三、技术栈详细清单

### 3.1 后端技术栈

| 分类 | 技术 | 版本 | 说明 |
|------|------|------|------|
| **Web框架** | FastAPI | 0.104.1 | 高性能异步API框架，自动生成OpenAPI文档 |
| **服务器** | Uvicorn | 0.24.0 | ASGI服务器，支持热重载 |
| **AI框架** | LangChain | 0.1.0 | AI应用开发框架，支持多LLM集成 |
| **LLM接口** | langchain-openai | 0.0.5 | OpenAI API集成 |
| **数据验证** | Pydantic | 2.5.0 | 数据模型定义与验证 |
| **配置管理** | python-dotenv | 1.0.0 | 环境变量加载 |
| **CLI框架** | Click | 8.0.0 | 命令行接口开发 |
| **终端美化** | Rich | 13.0.0+ | 富文本终端输出 |

### 3.2 前端技术栈

| 分类 | 技术 | 说明 |
|------|------|------|
| **结构** | HTML5 | 语义化标签，SEO友好 |
| **样式** | CSS3 | 响应式布局、动画效果 |
| **逻辑** | JavaScript ES6+ | 模块化、异步处理 |

### 3.3 开发工具

| 工具 | 用途 |
|------|------|
| **pip** | Python包管理 |
| **setuptools** | 包打包与分发 |
| **python-dotenv** | 环境配置 |

---

## 四、项目结构

```
ai-customer-service/
├── src/
│   └── ai_customer_service/          # Python包根目录
│       ├── __init__.py               # 包入口
│       ├── cli/                      # 命令行接口
│       │   ├── __init__.py
│       │   └── main.py               # CLI主入口
│       ├── core/                     # 核心模块
│       │   ├── __init__.py
│       │   ├── app.py                # FastAPI应用工厂
│       │   ├── config_manager.py     # 配置管理器
│       │   ├── plugin_interface.py   # 插件接口定义
│       │   └── plugin_manager.py     # 插件管理器
│       └── plugins/                  # 插件目录
│           ├── __init__.py
│           ├── ai_service_plugin.py     # AI客服插件
│           ├── knowledge_base_plugin.py # 知识库插件
│           └── ticket_plugin.py         # 工单插件
├── frontend/                         # 前端静态文件
│   ├── index.html
│   ├── script.js
│   └── styles.css
├── .env                              # 环境配置文件
├── .env.example                      # 配置模板
├── pyproject.toml                    # PyPI包配置
├── requirements.txt                  # 依赖清单
└── README.md                         # 项目说明
```

---

## 五、核心模块说明

### 5.1 插件系统

#### 插件接口定义
```python
class PluginInterface(ABC):
    def initialize(config) -> bool    # 初始化插件
    def execute(input_data) -> Dict   # 执行插件功能
    def shutdown() -> bool           # 关闭插件
    def get_info() -> PluginInfo     # 获取插件信息
```
[plugin_interface.py](file:///h:/douyin/实战项目/src/ai_customer_service/core/plugin_interface.py)

#### 插件管理器功能
| 方法 | 功能 |
|------|------|
| `discover_plugins()` | 自动发现并注册插件 |
| `register_plugin()` | 注册插件 |
| `initialize_plugin()` | 初始化插件 |
| `execute_plugin()` | 执行插件 |
| `shutdown_plugin()` | 关闭插件 |
[plugin_manager.py](file:///h:/douyin/实战项目/src/ai_customer_service/core/plugin_manager.py)

### 5.2 AI客服插件

**核心功能**：
- 智能对话响应
- 意图识别（9种预定义意图）
- 满意度分析
- 转人工触发逻辑（轮次触发 + 满意度触发）
- 模拟模式支持（无API密钥时使用）

[ai_service_plugin.py](file:///h:/douyin/实战项目/src/ai_customer_service/plugins/ai_service_plugin.py)

### 5.3 知识库插件

**核心功能**：
- FAQ增删改查
- 多分类管理
- 相似度搜索
- 知识文档管理

[knowledge_base_plugin.py](file:///h:/douyin/实战项目/src/ai_customer_service/plugins/knowledge_base_plugin.py)

### 5.4 工单插件

**核心功能**：
- 工单创建
- 客服接单
- 工单关闭
- 状态跟踪

[ticket_plugin.py](file:///h:/douyin/实战项目/src/ai_customer_service/plugins/ticket_plugin.py)

---

## 六、API接口列表

| 端点 | HTTP方法 | 功能描述 |
|------|----------|----------|
| `/` | GET | 返回前端页面 |
| `/api/chat` | POST | AI对话接口 |
| `/api/request-human` | POST | 请求转人工 |
| `/api/status` | GET | 获取系统状态 |
| `/docs` | GET | OpenAPI文档 |

### API接口示例

**POST /api/chat**
```json
{
    "session_id": "session_xxx",
    "message": "您好，我想咨询一下订单问题"
}
```

**响应**
```json
{
    "success": true,
    "response": "您好！请问有什么可以帮助您的？",
    "session_id": "session_xxx",
    "satisfaction_level": 0.5,
    "should_transfer": false,
    "conversation_turns": 1,
    "user_requested_transfer": false,
    "transfer_suggestion": "",
    "mode": "mock"
}
```

---

## 七、配置说明

### 必需配置

| 配置项 | 说明 | 示例 |
|--------|------|------|
| `OPENAI_API_KEY` | OpenAI API密钥 | `sk-xxxxxxxxxxxxx` |

### 可选配置

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `OPENAI_BASE_URL` | (空) | 自定义API端点（如国内代理） |
| `MODEL_NAME` | `gpt-3.5-turbo` | 模型名称 |
| `TEMPERATURE` | `0.7` | 温度参数（0-1） |
| `MAX_TOKENS` | `2000` | 最大Token数 |
| `PLUGIN_DIR` | `plugins` | 插件目录 |
| `LOG_LEVEL` | `INFO` | 日志级别 |

### 国内用户配置示例

```env
# 使用DeepSeek API
OPENAI_API_KEY=your-deepseek-key
OPENAI_BASE_URL=https://api.deepseek.com/v1
MODEL_NAME=deepseek-chat
```

---

## 八、部署与运行

### 开发模式

```bash
# 安装依赖
pip install -e .

# 初始化配置
ai-cs init

# 编辑配置文件
# 填入 OPENAI_API_KEY=your-key

# 启动服务
ai-cs start --reload
```

### 生产模式

```bash
# 安装依赖
pip install -e .

# 设置环境变量
export OPENAI_API_KEY=your-key

# 启动服务
ai-cs start --host 0.0.0.0 --port 8000
```

---

## 九、技术特点总结

| 特性 | 实现方式 |
|------|----------|
| **插件化架构** | 通过 `PluginInterface` 抽象接口实现 |
| **自动发现** | `PluginManager.discover_plugins()` 扫描注册 |
| **热重载** | Uvicorn `--reload` 支持 |
| **CLI工具** | Click + Rich 提供友好命令行 |
| **配置集中化** | `.env` + `ConfigManager` 统一管理 |
| **模拟模式** | 无API密钥时自动切换 |
| **转人工触发** | 轮次触发 + 满意度触发双重机制 |

---

## 十、依赖树

```
ai-customer-service
├── fastapi (0.104.1)
├── uvicorn (0.24.0)
├── langchain (0.1.0)
│   └── langchain-openai (0.0.5)
├── pydantic (2.5.0)
├── python-dotenv (1.0.0)
├── click (8.0.0)
└── rich (15.0.0+)
```

---

## 附录：文件清单

| 文件路径 | 说明 |
|----------|------|
| `src/ai_customer_service/__init__.py` | 包入口 |
| `src/ai_customer_service/cli/main.py` | CLI命令行入口 |
| `src/ai_customer_service/core/app.py` | FastAPI应用 |
| `src/ai_customer_service/core/config_manager.py` | 配置管理器 |
| `src/ai_customer_service/core/plugin_interface.py` | 插件接口 |
| `src/ai_customer_service/core/plugin_manager.py` | 插件管理器 |
| `src/ai_customer_service/plugins/ai_service_plugin.py` | AI客服插件 |
| `src/ai_customer_service/plugins/knowledge_base_plugin.py` | 知识库插件 |
| `src/ai_customer_service/plugins/ticket_plugin.py` | 工单插件 |
| `frontend/index.html` | 前端页面 |
| `frontend/script.js` | 前端逻辑 |
| `frontend/styles.css` | 前端样式 |
| `.env` | 环境配置 |
| `pyproject.toml` | 包配置 |
| `requirements.txt` | 依赖清单 |

---

*Generated: 2026-06-13*
