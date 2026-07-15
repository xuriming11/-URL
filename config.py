"""
RAG 系统配置模块
集中管理所有可调参数，方便统一修改
"""
import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


# ---------- 路径配置 ----------
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"            # 原始文档存放目录
PERSIST_DIR = BASE_DIR / "vector_db"    # Chroma 持久化目录

# 自动创建目录
DATA_DIR.mkdir(exist_ok=True)
PERSIST_DIR.mkdir(exist_ok=True)


class Settings(BaseSettings):
    """系统配置（可通过环境变量覆盖）"""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # ---------- 文本切分 ----------
    chunk_size: int = 500
    chunk_overlap: int = 50

    # ---------- Embedding 模型 ----------
    # bge-small-zh 中文效果好、体积小，适合本地部署
    embedding_model: str = "BAAI/bge-small-zh-v1.5"

    # ---------- Chroma 向量库 ----------
    collection_name: str = "rag_collection"

    # ---------- 检索 ----------
    search_top_k: int = 4          # 每次检索返回的文档块数量

    # ---------- LLM（OpenAI 兼容接口）----------
    # 本地可用 Ollama / vLLM，云端可用 OpenAI / 通义千问 / DeepSeek 等
    llm_base_url: str = "https://api.openai.com/v1"
    llm_api_key: str = ""
    llm_model: str = "gpt-3.5-turbo"
    llm_temperature: float = 0.3

    # ---------- API 服务 ----------
    api_host: str = "0.0.0.0"
    api_port: int = 8000


settings = Settings()
