# AI Agent Practice

## 环境配置

### 1. 安装依赖
```bash
pip install openai python-dotenv dashscope  # dashscope是阿里云通义千问的SDK
```

### 2. 配置API密钥

复制 `.env.example` 并重命名为 `.env`，然后根据你选择的服务配置相应的API密钥。

## 支持的AI服务

### 方案A：OpenAI API（需要网络代理）
```ini
AI_PROVIDER=openai
OPENAI_API_KEY=your-openai-key
OPENAI_API_BASE=https://api.openai.com/v1
```

### 方案B：阿里云通义千问（国内可直接访问）
```ini
AI_PROVIDER=dashscope
DASHSCOPE_API_KEY=your-dashscope-key
```

### 方案C：百度文心一言（国内可直接访问）
```ini
AI_PROVIDER=baidu
BAIDU_API_KEY=your-api-key
BAIDU_SECRET_KEY=your-secret-key
```

## 获取API密钥

### OpenAI
- 访问：https://platform.openai.com/api-keys
- 需要科学上网

### 阿里云通义千问
- 访问：https://dashscope.console.aliyun.com/
- 国内可直接访问，新用户有免费额度

### 百度文心一言
- 访问：https://console.bce.baidu.com/qianfan/
- 国内可直接访问，新用户有免费额度

## 测试连接
```bash
python test_api.py
```
