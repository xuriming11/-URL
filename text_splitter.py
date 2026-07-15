"""
文本切分模块
使用 RecursiveCharacterTextSplitter 进行递归切分，保留语义完整性
"""
from typing import List

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from config import settings


def get_splitter(chunk_size: int = None, chunk_overlap: int = None) -> RecursiveCharacterTextSplitter:
    """
    创建文本切分器

    参数:
        chunk_size: 每块最大字符数，默认从配置读取
        chunk_overlap: 块之间的重叠字符数，保证上下文连贯

    返回:
        RecursiveCharacterTextSplitter 实例
    """
    return RecursiveCharacterTextSplitter(
        chunk_size=chunk_size or settings.chunk_size,
        chunk_overlap=chunk_overlap or settings.chunk_overlap,
        # 分隔符优先级：段落 > 换行 > 句号 > 空格（中文友好）
        separators=["\n\n", "\n", "。", "！", "？", ".", "!", "?", " ", ""],
        length_function=len,
    )


def split_documents(documents: List[Document]) -> List[Document]:
    """
    对文档列表进行切分

    参数:
        documents: 原始文档列表

    返回:
        List[Document]: 切分后的文档块列表
    """
    if not documents:
        return []

    splitter = get_splitter()
    chunks = splitter.split_documents(documents)
    print(f"[切分完成] 原始文档 {len(documents)} 个 -> 切分后 {len(chunks)} 个块")
    return chunks


if __name__ == "__main__":
    # 测试切分
    test_docs = [
        Document(
            page_content="这是一个测试文档。用于验证文本切分功能是否正常工作。\n\n"
                         "第二段内容会单独成块，确保语义完整性。" * 20,
            metadata={"source": "test"},
        )
    ]
    result = split_documents(test_docs)
    for i, chunk in enumerate(result):
        print(f"--- 块 {i + 1}（{len(chunk.page_content)} 字）---")
        print(chunk.page_content[:100])
