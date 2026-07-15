"""
文档加载模块
支持 PDF、TXT、Markdown、DOCX 等常见格式
"""
from pathlib import Path
from typing import List, Union

from langchain_core.documents import Document
from langchain_community.document_loaders import (
    TextLoader,
    PyPDFLoader,
    UnstructuredMarkdownLoader,
    Docx2txtLoader,
)


# 文件后缀 -> 加载器 映射
LOADER_MAP = {
    ".txt": TextLoader,
    ".pdf": PyPDFLoader,
    ".md": UnstructuredMarkdownLoader,
    ".docx": Docx2txtLoader,
}


def load_document(file_path: Union[str, Path]) -> List[Document]:
    """
    加载单个文档文件，返回 Document 列表

    参数:
        file_path: 文件路径

    返回:
        List[Document]: 加载后的文档块列表
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"文件不存在: {path}")

    suffix = path.suffix.lower()
    loader_cls = LOADER_MAP.get(suffix)
    if loader_cls is None:
        raise ValueError(f"不支持的文件格式: {suffix}（支持: {list(LOADER_MAP.keys())}）")

    loader = loader_cls(str(path))
    documents = loader.load()

    # 统一补充元数据
    for doc in documents:
        doc.metadata.setdefault("source", str(path))
        doc.metadata.setdefault("filename", path.name)

    return documents


def load_directory(directory: Union[str, Path]) -> List[Document]:
    """
    批量加载目录下所有受支持格式的文档

    参数:
        directory: 目录路径

    返回:
        List[Document]: 合并后的文档列表
    """
    dir_path = Path(directory)
    if not dir_path.exists():
        raise FileNotFoundError(f"目录不存在: {dir_path}")

    all_documents: List[Document] = []
    for file_path in dir_path.iterdir():
        if file_path.is_file() and file_path.suffix.lower() in LOADER_MAP:
            try:
                all_documents.extend(load_document(file_path))
                print(f"[加载成功] {file_path.name}")
            except Exception as e:
                print(f"[加载失败] {file_path.name}: {e}")

    return all_documents


if __name__ == "__main__":
    # 测试：加载 data 目录
    from config import DATA_DIR

    docs = load_directory(DATA_DIR)
    print(f"\n共加载 {len(docs)} 个文档块")
    if docs:
        print(f"示例内容前 200 字: {docs[0].page_content[:200]}")
