"""
检索 + 生成 QA 链模块
- 使用 Chroma 作为 Retriever
- 通过 RetrievalQA chain 组合 LLM 生成最终回答
- 支持自定义 prompt，让回答更贴合中文场景
"""
from typing import Optional, Dict, Any

from langchain.chains import RetrievalQA
from langchain.chains.base import Chain
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import ChatOpenAI

from config import settings
from vector_store import get_vector_store


# ---------- 中文 Prompt 模板 ----------
PROMPT_TEMPLATE = """你是一个专业的知识库问答助手。请根据下方【参考资料】回答用户问题。

要求：
1. 回答必须基于【参考资料】，不要编造资料中不存在的信息
2. 如果资料不足以回答，请明确说明"根据现有资料无法回答该问题"
3. 回答使用中文，条理清晰，必要时分点说明
4. 在回答末尾标注引用的资料来源

【参考资料】：
{context}

【用户问题】：{question}

【回答】：
"""

PROMPT = PromptTemplate.from_template(PROMPT_TEMPLATE)


# ---------- LLM 单例 ----------
_llm: Optional[ChatOpenAI] = None


def get_llm() -> ChatOpenAI:
    """
    获取 LLM 实例（单例）
    兼容 OpenAI / DeepSeek / 通义千问 / 本地 Ollama 等 OpenAI 兼容接口
    """
    global _llm
    if _llm is None:
        _llm = ChatOpenAI(
            base_url=settings.llm_base_url,
            api_key=settings.llm_api_key or "not-needed",
            model=settings.llm_model,
            temperature=settings.llm_temperature,
        )
    return _llm


def get_qa_chain() -> Chain:
    """
    构建 RetrievalQA 链

    流程: 用户问题 -> Retriever 检索 -> 组装 Prompt -> LLM 生成 -> 输出回答
    """
    vector_store = get_vector_store()
    retriever = vector_store.as_retriever(
        search_type="similarity",
        search_kwargs={"k": settings.search_top_k},
    )

    def format_docs(docs):
        """把检索到的文档块格式化为上下文文本"""
        return "\n\n".join(
            f"[资料{i + 1}] (来源: {d.metadata.get('filename', '未知')}):\n{d.page_content}"
            for i, d in enumerate(docs)
        )

    # 使用 LCEL 构建链，更灵活
    rag_chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | PROMPT
        | get_llm()
        | StrOutputParser()
    )
    return rag_chain


def ask(question: str) -> Dict[str, Any]:
    """
    问答接口：输入问题，返回回答 + 检索到的参考资料

    参数:
        question: 用户问题

    返回:
        {"answer": 回答文本, "sources": [资料来源列表]}
    """
    # 1. 检索
    from vector_store import similarity_search
    source_docs = similarity_search(question)

    # 2. 生成
    chain = get_qa_chain()
    answer = chain.invoke(question)

    # 3. 整理来源信息
    sources = [
        {
            "filename": doc.metadata.get("filename", "未知"),
            "source": doc.metadata.get("source", "未知"),
            "snippet": doc.page_content[:150],
        }
        for doc in source_docs
    ]

    print(f"\n[问答] 问题: {question}")
    print(f"[问答] 回答: {answer[:200]}...")

    return {"answer": answer, "sources": sources}


if __name__ == "__main__":
    # 测试问答
    result = ask("请介绍一下相关内容")
    print("\n===== 完整回答 =====")
    print(result["answer"])
    print("\n===== 引用来源 =====")
    for s in result["sources"]:
        print(f"- {s['filename']}: {s['snippet']}")
