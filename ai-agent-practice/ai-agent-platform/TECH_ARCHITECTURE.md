# AgentHub 技术架构文档

## 1. 技术栈

### 1.1 前端技术
- **HTML5**: 语义化标签
- **CSS3**: 
  - Flexbox + Grid 布局
  - CSS Variables 主题变量
  - CSS Animations 动画效果
  - Backdrop-filter 毛玻璃效果
- **JavaScript (ES6+)**: 
  - Fetch API 网络请求
  - WebSocket 实时通信
  - LocalStorage 本地存储

### 1.2 后端技术
- **Python 3.11+**
- **Flask**: 轻量级Web框架
- **SQLAlchemy**: ORM数据库操作
- **Flask-CORS**: 跨域支持

### 1.3 数据库
- **SQLite**: 本地轻量级数据库
- **表结构设计** (详见下方)

---

## 2. 数据库设计

### 2.1 agents 表（Agent管理）
```sql
CREATE TABLE agents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    model_id VARCHAR(50) DEFAULT 'qwen-plus',
    api_key VARCHAR(200),
    base_url VARCHAR(200),
    config TEXT,  -- JSON配置
    status VARCHAR(20) DEFAULT 'active',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### 2.2 conversations 表（对话记录）
```sql
CREATE TABLE conversations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_id INTEGER NOT NULL,
    title VARCHAR(200),
    messages TEXT,  -- JSON数组
    token_count INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE CASCADE
);
```

### 2.3 files 表（文件管理）
```sql
CREATE TABLE files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename VARCHAR(255) NOT NULL,
    original_name VARCHAR(255),
    filepath VARCHAR(500) NOT NULL,
    filesize INTEGER,
    filetype VARCHAR(50),
    category VARCHAR(50),
    uploaded_by VARCHAR(100),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### 2.4 usage_logs 表（使用统计）
```sql
CREATE TABLE usage_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_id INTEGER NOT NULL,
    conversation_id INTEGER,
    token_used INTEGER,
    response_time FLOAT,
    status VARCHAR(20),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE CASCADE
);
```

---

## 3. API接口设计

### 3.1 Agent管理接口

#### 创建Agent
```
POST /api/agents
Request: { name, description, model_id, api_key, base_url, config }
Response: { id, name, ... }
```

#### 获取Agent列表
```
GET /api/agents
Response: { agents: [{ id, name, model_id, status, ... }] }
```

#### 获取单个Agent
```
GET /api/agents/<id>
Response: { id, name, model_id, config, ... }
```

#### 更新Agent
```
PUT /api/agents/<id>
Request: { name, config, ... }
Response: { success: true }
```

#### 删除Agent
```
DELETE /api/agents/<id>
Response: { success: true }
```

### 3.2 对话接口

#### 创建对话
```
POST /api/chat/<agent_id>
Request: { message, conversation_id? }
Response: { response, conversation_id, tokens }
```

#### 获取对话历史
```
GET /api/conversations/<agent_id>
Response: { conversations: [...] }
```

### 3.3 文件管理接口

#### 上传文件
```
POST /api/files/upload
Request: multipart/form-data (file, category)
Response: { id, filename, filepath, filesize }
```

#### 获取文件列表
```
GET /api/files
Query: ?category=&page=&limit=
Response: { files: [...], total, page }
```

#### 下载文件
```
GET /api/files/download/<id>
Response: 文件流
```

#### 删除文件
```
DELETE /api/files/<id>
Response: { success: true }
```

### 3.4 统计接口

#### 获取使用统计
```
GET /api/stats
Response: { total_calls, total_tokens, total_agents, recent_usage }
```

---

## 4. 前端架构

### 4.1 页面结构
```
index.html
├── 顶部导航栏 (Header)
├── 侧边栏 (Sidebar)
│   ├── Agent列表
│   ├── 文件管理
│   ├── 使用统计
│   └── 设置
└── 主内容区 (Main Content)
    ├── Agent对话面板
    ├── 文件管理面板
    └── 统计面板
```

### 4.2 JavaScript模块化设计
```javascript
// app.js 模块结构
const App = {
    // 状态管理
    state: {
        currentAgent: null,
        conversations: [],
        files: []
    },
    
    // API模块
    api: {
        agents: {...},
        chat: {...},
        files: {...}
    },
    
    // UI组件
    components: {
        sidebar: {...},
        chatPanel: {...},
        fileManager: {...}
    },
    
    // 初始化
    init() {...}
};
```

---

## 5. 安全性设计

### 5.1 文件上传安全
- 文件类型白名单验证
- 文件大小限制（50MB）
- 文件名随机化存储
- 上传目录与Web根目录分离

### 5.2 API安全
- CORS配置
- 输入验证和清洗
- SQL注入防护（使用ORM）
- 敏感信息加密存储

### 5.3 前端安全
- XSS防护（内容转义）
- CSRF Token验证
- 安全的内容安全策略

---

## 6. 部署方案

### 6.1 开发环境
```bash
pip install flask flask-cors sqlalchemy
python app.py
# 访问 http://localhost:5000
```

### 6.2 生产环境
```bash
# 使用Gunicorn
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

---

## 7. 性能优化

### 7.1 数据库优化
- 索引优化
- 分页查询
- 定期清理旧数据

### 7.2 前端优化
- CSS/JS压缩
- 懒加载
- 缓存策略

### 7.3 实时性能
- WebSocket心跳检测
- 请求超时处理
- 重连机制
