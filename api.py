"""
FastAPI 接口模块
对外提供：
  - POST /chat   : 基于知识库的问答
  - POST /upload : 上传文档并增量入库
  - POST /build  : 重建向量库
  - GET  /health : 健康检查
"""
import shutil
import tempfile
from pathlib import Path
from typing import List

from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel

from config import settings, DATA_DIR
from document_loader import load_document
from text_splitter import split_documents
from vector_store import build_vector_store, get_vector_store
from qa_chain import ask


app = FastAPI(
    title="RAG 知识库问答系统",
    description="文档加载 → 切分 → 向量化(bge-small-zh) → Chroma存储 → RetrievalQA生成",
    version="1.0.0",
)


# ---------- 请求/响应模型 ----------
class ChatRequest(BaseModel):
    question: str
    top_k: int = None  # 可选，覆盖默认检索数量


class ChatResponse(BaseModel):
    answer: str
    sources: List[dict] = []


class UploadResponse(BaseModel):
    filename: str
    chunks: int
    message: str


class BuildResponse(BaseModel):
    success: bool
    message: str


# ---------- 接口 ----------
@app.get("/health")
def health():
    """健康检查"""
    return {"status": "ok", "embedding_model": settings.embedding_model}


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    """
    知识库问答接口
    接收问题 -> 检索相关文档 -> LLM 生成回答
    """
    if not req.question.strip():
        raise HTTPException(status_code=400, detail="问题不能为空")

    try:
        result = ask(req.question)
        return ChatResponse(answer=result["answer"], sources=result["sources"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"问答失败: {e}")


@app.post("/upload", response_model=UploadResponse)
async def upload(file: UploadFile = File(...)):
    """
    上传文档接口
    保存文件到 data 目录 -> 加载 -> 切分 -> 增量入库
    支持 txt / pdf / md / docx
    """
    suffix = Path(file.filename).suffix.lower()
    allowed = {".txt", ".pdf", ".md", ".docx"}
    if suffix not in allowed:
        raise HTTPException(status_code=400, detail=f"不支持的格式，仅支持 {allowed}")

    # 保存到 data 目录
    save_path = DATA_DIR / file.filename
    content = await file.read()
    save_path.write_bytes(content)

    try:
        # 加载 -> 切分 -> 入库
        documents = load_document(save_path)
        chunks = split_documents(documents)
        build_vector_store(chunks, clear_existing=False)  # 增量入库

        return UploadResponse(
            filename=file.filename,
            chunks=len(chunks),
            message=f"上传成功，切分为 {len(chunks)} 个块并已入库",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"处理文档失败: {e}")


@app.post("/build", response_model=BuildResponse)
def rebuild():
    """
    重建向量库：重新加载 data 目录所有文档
    """
    try:
        from vector_store import build_from_data_directory
        vs = build_from_data_directory(clear_existing=True)
        return BuildResponse(success=True, message="向量库重建完成")
    except Exception as e:
        return BuildResponse(success=False, message=f"重建失败: {e}")


if __name__ == "__main__":
    import uvicorn
    print("=" * 50)
    print("RAG 知识库问答系统启动中...")
    print(f"  文档目录: {DATA_DIR}")
    print(f"  向量库:   {Path('vector_db').resolve()}")
    print(f"  模型:     {settings.embedding_model}")
    print(f"  LLM:      {settings.llm_model}")
    print("=" * 50)
    uvicorn.run(
        "api:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True,
    )
