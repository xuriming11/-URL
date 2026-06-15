"""
知识库插件
使用父子块（Parent-Child Chunk）策略提高检索准确性
支持向量存储、检索和重排功能
"""

import logging
import hashlib
import json
import re
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, field
from backend.plugin_interface import PluginInterface, PluginInfo
from backend.config import config

# LangChain相关导入
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter


logger = logging.getLogger(__name__)


@dataclass
class ParentChunk:
    """父块数据结构"""
    id: str
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    child_chunks: List["ChildChunk"] = field(default_factory=list)  # 使用字符串引用
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "content": self.content,
            "metadata": self.metadata,
            "child_count": len(self.child_chunks),
            "created_at": self.created_at.isoformat()
        }


@dataclass
class ChildChunk:
    """子块数据结构"""
    id: str
    parent_id: str
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    embedding: Optional[List[float]] = None
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "parent_id": self.parent_id,
            "content": self.content,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat()
        }


class ParentChildChunker:
    """
    父子块分割器
    
    策略说明：
    - 父块：较大的文本块，保留完整上下文信息
    - 子块：较小的文本块，用于精确检索匹配
    
    检索流程：
    1. 对子块进行向量检索，找到最相关的子块
    2. 根据子块的parent_id找到对应的父块
    3. 返回父块的完整内容，提供更丰富的上下文
    """
    
    def __init__(
        self,
        parent_chunk_size: int = 1000,
        parent_chunk_overlap: int = 200,
        child_chunk_size: int = 200,
        child_chunk_overlap: int = 50,
        separators: List[str] = None
    ):
        """
        初始化父子块分割器
        
        Args:
            parent_chunk_size: 父块大小（字符数）
            parent_chunk_overlap: 父块重叠大小
            child_chunk_size: 子块大小（字符数）
            child_chunk_overlap: 子块重叠大小
            separators: 分隔符列表
        """
        self.parent_chunk_size = parent_chunk_size
        self.parent_chunk_overlap = parent_chunk_overlap
        self.child_chunk_size = child_chunk_size
        self.child_chunk_overlap = child_chunk_overlap
        
        # 默认分隔符：优先按段落、句子分割
        self.separators = separators or [
            "\n\n",  # 段落
            "\n",    # 行
            "。",    # 中文句号
            "！",    # 中文感叹号
            "？",    # 中文问号
            "；",    # 中文分号
            ".",     # 英文句号
            "!",     # 英文感叹号
            "?",     # 英文问号
            ";",     # 英文分号
            " ",     # 空格
            ""       # 字符
        ]
        
        # 创建分割器
        self.parent_splitter = RecursiveCharacterTextSplitter(
            chunk_size=parent_chunk_size,
            chunk_overlap=parent_chunk_overlap,
            separators=self.separators,
            length_function=len
        )
        
        self.child_splitter = RecursiveCharacterTextSplitter(
            chunk_size=child_chunk_size,
            chunk_overlap=child_chunk_overlap,
            separators=self.separators,
            length_function=len
        )
    
    def chunk_text(self, text: str, metadata: Dict[str, Any] = None) -> List[ParentChunk]:
        """
        将文本分割为父子块
        
        Args:
            text: 待分割的文本
            metadata: 元数据
        
        Returns:
            List[ParentChunk]: 父块列表（包含子块）
        """
        parent_chunks = []
        base_metadata = metadata or {}
        
        # 第一步：分割为父块
        parent_texts = self.parent_splitter.split_text(text)
        
        for i, parent_text in enumerate(parent_texts):
            # 生成父块ID
            parent_id = self._generate_chunk_id(parent_text, f"parent_{i}")
            
            # 创建父块
            parent_chunk = ParentChunk(
                id=parent_id,
                content=parent_text,
                metadata={
                    **base_metadata,
                    "chunk_type": "parent",
                    "chunk_index": i,
                    "total_parent_chunks": len(parent_texts)
                }
            )
            
            # 第二步：将父块分割为子块
            child_texts = self.child_splitter.split_text(parent_text)
            
            for j, child_text in enumerate(child_texts):
                # 生成子块ID
                child_id = self._generate_chunk_id(child_text, f"child_{i}_{j}")
                
                # 创建子块
                child_chunk = ChildChunk(
                    id=child_id,
                    parent_id=parent_id,
                    content=child_text,
                    metadata={
                        **base_metadata,
                        "chunk_type": "child",
                        "parent_index": i,
                        "child_index": j,
                        "total_child_chunks": len(child_texts)
                    }
                )
                
                parent_chunk.child_chunks.append(child_chunk)
            
            parent_chunks.append(parent_chunk)
        
        logger.info(f"文本分割完成: {len(parent_chunks)}个父块, 共{sum(len(p.child_chunks) for p in parent_chunks)}个子块")
        
        return parent_chunks
    
    def _generate_chunk_id(self, content: str, prefix: str) -> str:
        """
        生成块ID
        
        Args:
            content: 块内容
            prefix: ID前缀
        
        Returns:
            str: 唯一的块ID
        """
        content_hash = hashlib.md5(content.encode()).hexdigest()[:8]
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        return f"{prefix}_{content_hash}_{timestamp}"


class VectorStore:
    """
    向量存储基类
    支持多种向量数据库后端
    """
    
    def __init__(self):
        self.embeddings: Dict[str, List[float]] = {}  # chunk_id -> embedding
        self.documents: Dict[str, ChildChunk] = {}     # chunk_id -> child_chunk
        self.parent_chunks: Dict[str, ParentChunk] = {}  # parent_id -> parent_chunk
    
    def add_documents(self, parent_chunks: List[ParentChunk], embeddings: Dict[str, List[float]] = None):
        """
        添加文档到向量存储
        
        Args:
            parent_chunks: 父块列表
            embeddings: 子块嵌入向量字典（chunk_id -> embedding）
        """
        for parent_chunk in parent_chunks:
            # 存储父块
            self.parent_chunks[parent_chunk.id] = parent_chunk
            
            # 存储子块
            for child_chunk in parent_chunk.child_chunks:
                self.documents[child_chunk.id] = child_chunk
                
                # 如果提供了嵌入向量，存储它
                if embeddings and child_chunk.id in embeddings:
                    self.embeddings[child_chunk.id] = embeddings[child_chunk.id]
                    child_chunk.embedding = embeddings[child_chunk.id]
    
    def search(self, query_embedding: List[float], top_k: int = 5) -> List[Tuple[ChildChunk, float]]:
        """
        搜索最相似的子块
        
        Args:
            query_embedding: 查询嵌入向量
            top_k: 返回数量
        
        Returns:
            List[Tuple[ChildChunk, float]]: (子块, 相似度分数)列表
        """
        results = []
        
        for chunk_id, embedding in self.embeddings.items():
            similarity = self._cosine_similarity(query_embedding, embedding)
            results.append((self.documents[chunk_id], similarity))
        
        # 按相似度排序
        results.sort(key=lambda x: x[1], reverse=True)
        
        return results[:top_k]
    
    def get_parent_by_child_id(self, child_id: str) -> Optional[ParentChunk]:
        """
        根据子块ID获取父块
        
        Args:
            child_id: 子块ID
        
        Returns:
            Optional[ParentChunk]: 父块
        """
        child_chunk = self.documents.get(child_id)
        if child_chunk:
            return self.parent_chunks.get(child_chunk.parent_id)
        return None
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """
        计算余弦相似度
        
        Args:
            vec1: 向量1
            vec2: 向量2
        
        Returns:
            float: 相似度分数
        """
        if len(vec1) != len(vec2):
            return 0.0
        
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = sum(a ** 2 for a in vec1) ** 0.5
        norm2 = sum(b ** 2 for b in vec2) ** 0.5
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)


class MockEmbedding:
    """
    模拟嵌入模型
    当没有配置真实API时使用
    """
    
    def __init__(self, dimension: int = 384):
        self.dimension = dimension
    
    def embed_text(self, text: str) -> List[float]:
        """
        生成文本嵌入向量（模拟）
        
        Args:
            text: 文本
        
        Returns:
            List[float]: 嵌入向量
        """
        # 使用简单的哈希方法生成模拟向量
        text_hash = hashlib.sha256(text.encode()).hexdigest()
        
        # 将哈希转换为向量
        embedding = []
        for i in range(self.dimension):
            # 使用哈希的不同部分生成向量元素
            start = (i * 2) % len(text_hash)
            value = int(text_hash[start:start+2], 16) / 255.0 - 0.5
            embedding.append(value)
        
        return embedding


class Reranker:
    """
    重排器
    对检索结果进行二次排序，提高准确性
    """
    
    def __init__(self):
        pass
    
    def rerank(
        self,
        query: str,
        results: List[Tuple[ChildChunk, float]],
        top_k: int = 3
    ) -> List[Tuple[ParentChunk, float, str]]:
        """
        重排检索结果
        
        Args:
            query: 查询文本
            results: 初步检索结果
            top_k: 最终返回数量
        
        Returns:
            List[Tuple[ParentChunk, float, str]]: (父块, 重排分数, 匹配的子块内容)列表
        """
        reranked_results = []
        
        # 去重：同一个父块可能有多个子块匹配
        seen_parents = {}
        
        for child_chunk, similarity in results:
            parent_id = child_chunk.parent_id
            
            if parent_id not in seen_parents:
                seen_parents[parent_id] = {
                    "max_similarity": similarity,
                    "child_content": child_chunk.content,
                    "child_chunks": [child_chunk]
                }
            else:
                # 如果已有该父块，更新最大相似度
                if similarity > seen_parents[parent_id]["max_similarity"]:
                    seen_parents[parent_id]["max_similarity"] = similarity
                    seen_parents[parent_id]["child_content"] = child_chunk.content
                seen_parents[parent_id]["child_chunks"].append(child_chunk)
        
        # 计算重排分数
        for parent_id, info in seen_parents.items():
            # 重排分数考虑：
            # 1. 最大子块相似度
            # 2. 匹配子块数量（越多说明父块更相关）
            # 3. 关键词匹配度
            
            max_sim = info["max_similarity"]
            child_count = len(info["child_chunks"])
            
            # 关键词匹配分数
            keyword_score = self._keyword_match_score(query, info["child_content"])
            
            # 综合分数
            rerank_score = max_sim * 0.6 + (child_count / 10) * 0.2 + keyword_score * 0.2
            
            reranked_results.append((
                self._get_parent_chunk(parent_id),
                rerank_score,
                info["child_content"]
            ))
        
        # 按重排分数排序
        reranked_results.sort(key=lambda x: x[1], reverse=True)
        
        return reranked_results[:top_k]
    
    def _keyword_match_score(self, query: str, content: str) -> float:
        """
        计算关键词匹配分数
        
        Args:
            query: 查询文本
            content: 内容文本
        
        Returns:
            float: 匹配分数
        """
        # 提取关键词
        query_keywords = self._extract_keywords(query)
        content_keywords = self._extract_keywords(content)
        
        # 计算交集比例
        if not query_keywords:
            return 0.0
        
        common_keywords = set(query_keywords) & set(content_keywords)
        return len(common_keywords) / len(query_keywords)
    
    def _extract_keywords(self, text: str) -> List[str]:
        """
        提取关键词
        
        Args:
            text: 文本
        
        Returns:
            List[str]: 关键词列表
        """
        # 简单的关键词提取：去除停用词，提取有意义的词
        stopwords = {"的", "是", "在", "有", "和", "了", "我", "你", "他", "她", "它", "这", "那", "什么", "怎么", "如何", "为什么"}
        
        # 分词（简单按空格和标点分割）
        words = re.findall(r'[\w]+', text)
        
        # 过滤停用词和短词
        keywords = [w for w in words if w not in stopwords and len(w) > 1]
        
        return keywords
    
    def _get_parent_chunk(self, parent_id: str) -> ParentChunk:
        """获取父块（需要在实际使用时连接向量存储）"""
        # 这里返回一个占位符，实际使用时需要传入向量存储
        return ParentChunk(id=parent_id, content="")


class KnowledgeBasePlugin(PluginInterface):
    """
    知识库插件
    整合父子块分割、向量存储、检索和重排功能
    """
    
    def __init__(self):
        self.chunker: ParentChildChunker = None
        self.vector_store: VectorStore = None
        self.embedding_model: MockEmbedding = None
        self.reranker: Reranker = None
        self.knowledge_bases: Dict[str, Dict] = {}  # 知识库名称 -> 配置
        self.use_mock = True
    
    def initialize(self, config: Dict[str, Any]) -> bool:
        """
        初始化知识库插件
        
        Args:
            config: 插件配置
        
        Returns:
            bool: 初始化是否成功
        """
        try:
            # 初始化父子块分割器
            self.chunker = ParentChildChunker(
                parent_chunk_size=config.get("parent_chunk_size", 1000),
                parent_chunk_overlap=config.get("parent_chunk_overlap", 200),
                child_chunk_size=config.get("child_chunk_size", 200),
                child_chunk_overlap=config.get("child_chunk_overlap", 50)
            )
            
            # 初始化向量存储
            self.vector_store = VectorStore()
            
            # 初始化嵌入模型
            api_key = config.get("embedding_api_key")
            if api_key and api_key.strip():
                # 使用真实嵌入模型（需要配置）
                self.use_mock = False
                logger.info("使用真实嵌入模型")
            else:
                # 使用模拟嵌入模型
                self.embedding_model = MockEmbedding(dimension=config.get("embedding_dimension", 384))
                self.use_mock = True
                logger.info("使用模拟嵌入模型")
            
            # 初始化重排器
            self.reranker = Reranker()
            
            logger.info("知识库插件初始化成功")
            return True
            
        except Exception as e:
            logger.error(f"知识库插件初始化失败: {e}")
            return False
    
    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行知识库操作
        
        Args:
            input_data: 输入数据
        
        Returns:
            Dict: 执行结果
        """
        action = input_data.get("action", "")
        
        if action == "add_document":
            return self.add_document(input_data)
        elif action == "search":
            return self.search(input_data)
        elif action == "get_document":
            return self.get_document(input_data)
        elif action == "list_documents":
            return self.list_documents()
        elif action == "delete_document":
            return self.delete_document(input_data)
        elif action == "get_stats":
            return self.get_stats()
        else:
            return {"success": False, "error": "Unknown action"}
    
    def shutdown(self) -> bool:
        """
        关闭知识库插件
        
        Returns:
            bool: 关闭是否成功
        """
        try:
            self.vector_store = None
            self.chunker = None
            logger.info("知识库插件关闭成功")
            return True
        except Exception as e:
            logger.error(f"知识库插件关闭失败: {e}")
            return False
    
    def get_info(self) -> PluginInfo:
        """
        获取插件信息
        
        Returns:
            PluginInfo: 插件信息
        """
        return PluginInfo(
            name="knowledge_base_plugin",
            version="1.0.0",
            description="知识库插件 - 支持父子块Chunking和智能检索",
            author="AI客服团队",
            dependencies=["langchain", "langchain-text-splitters"]
        )
    
    def add_document(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        添加文档到知识库
        
        Args:
            input_data: 包含document_id, content, metadata
        
        Returns:
            Dict: 添加结果
        """
        try:
            document_id = input_data.get("document_id", "")
            content = input_data.get("content", "")
            metadata = input_data.get("metadata", {})
            
            if not content:
                return {"success": False, "error": "内容不能为空"}
            
            # 添加文档元数据
            metadata["document_id"] = document_id
            metadata["added_at"] = datetime.now().isoformat()
            
            # 使用父子块分割器分割文本
            parent_chunks = self.chunker.chunk_text(content, metadata)
            
            # 生成嵌入向量
            embeddings = {}
            for parent_chunk in parent_chunks:
                for child_chunk in parent_chunk.child_chunks:
                    if self.use_mock:
                        embedding = self.embedding_model.embed_text(child_chunk.content)
                        embeddings[child_chunk.id] = embedding
                    # 如果使用真实嵌入模型，这里需要调用API
            
            # 添加到向量存储
            self.vector_store.add_documents(parent_chunks, embeddings)
            
            # 记录知识库信息
            self.knowledge_bases[document_id] = {
                "document_id": document_id,
                "metadata": metadata,
                "parent_count": len(parent_chunks),
                "child_count": sum(len(p.child_chunks) for p in parent_chunks),
                "added_at": datetime.now().isoformat()
            }
            
            logger.info(f"文档添加成功: {document_id}, {len(parent_chunks)}个父块")
            
            return {
                "success": True,
                "document_id": document_id,
                "parent_chunks": len(parent_chunks),
                "child_chunks": sum(len(p.child_chunks) for p in parent_chunks),
                "message": "文档添加成功"
            }
            
        except Exception as e:
            logger.error(f"添加文档失败: {e}")
            return {"success": False, "error": str(e)}
    
    def search(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        搜索知识库
        
        Args:
            input_data: 包含query, top_k
        
        Returns:
            Dict: 搜索结果（包含父块完整内容）
        """
        try:
            query = input_data.get("query", "")
            top_k = input_data.get("top_k", 5)
            
            if not query:
                return {"success": False, "error": "查询内容不能为空"}
            
            # 生成查询嵌入向量
            if self.use_mock:
                query_embedding = self.embedding_model.embed_text(query)
            
            # 在向量存储中搜索
            child_results = self.vector_store.search(query_embedding, top_k=top_k * 2)
            
            # 重排结果
            # 需要传入向量存储以获取父块
            reranked_results = []
            seen_parents = {}
            
            for child_chunk, similarity in child_results:
                parent_id = child_chunk.parent_id
                
                if parent_id not in seen_parents:
                    parent_chunk = self.vector_store.get_parent_by_child_id(child_chunk.id)
                    if parent_chunk:
                        seen_parents[parent_id] = {
                            "parent": parent_chunk,
                            "max_similarity": similarity,
                            "matched_child": child_chunk.content,
                            "child_count": 1
                        }
                else:
                    seen_parents[parent_id]["child_count"] += 1
                    if similarity > seen_parents[parent_id]["max_similarity"]:
                        seen_parents[parent_id]["max_similarity"] = similarity
                        seen_parents[parent_id]["matched_child"] = child_chunk.content
            
            # 计算重排分数
            for parent_id, info in seen_parents.items():
                keyword_score = self.reranker._keyword_match_score(query, info["matched_child"])
                rerank_score = info["max_similarity"] * 0.6 + (info["child_count"] / 10) * 0.2 + keyword_score * 0.2
                
                reranked_results.append({
                    "parent_content": info["parent"].content,
                    "parent_id": parent_id,
                    "rerank_score": rerank_score,
                    "matched_child": info["matched_child"],
                    "child_similarity": info["max_similarity"],
                    "metadata": info["parent"].metadata
                })
            
            # 按重排分数排序
            reranked_results.sort(key=lambda x: x["rerank_score"], reverse=True)
            
            # 返回top_k结果
            final_results = reranked_results[:top_k]
            
            logger.info(f"搜索完成: 查询'{query}', 返回{len(final_results)}个结果")
            
            return {
                "success": True,
                "query": query,
                "results": final_results,
                "total_matches": len(reranked_results),
                "mode": "mock" if self.use_mock else "real"
            }
            
        except Exception as e:
            logger.error(f"搜索失败: {e}")
            return {"success": False, "error": str(e)}
    
    def get_document(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        获取文档详情
        
        Args:
            input_data: 包含document_id
        
        Returns:
            Dict: 文档详情
        """
        document_id = input_data.get("document_id", "")
        
        if document_id not in self.knowledge_bases:
            return {"success": False, "error": "文档不存在"}
        
        doc_info = self.knowledge_bases[document_id]
        
        # 获取所有相关的父块
        parent_chunks = []
        for parent_id, parent in self.vector_store.parent_chunks.items():
            if parent.metadata.get("document_id") == document_id:
                parent_chunks.append(parent.to_dict())
        
        return {
            "success": True,
            "document_info": doc_info,
            "parent_chunks": parent_chunks
        }
    
    def list_documents(self) -> Dict[str, Any]:
        """
        列出所有文档
        
        Returns:
            Dict: 文档列表
        """
        documents = []
        for doc_id, doc_info in self.knowledge_bases.items():
            documents.append({
                "document_id": doc_id,
                "metadata": doc_info.get("metadata", {}),
                "parent_count": doc_info.get("parent_count", 0),
                "child_count": doc_info.get("child_count", 0),
                "added_at": doc_info.get("added_at", "")
            })
        
        return {
            "success": True,
            "documents": documents,
            "total": len(documents)
        }
    
    def delete_document(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        删除文档
        
        Args:
            input_data: 包含document_id
        
        Returns:
            Dict: 删除结果
        """
        document_id = input_data.get("document_id", "")
        
        if document_id not in self.knowledge_bases:
            return {"success": False, "error": "文档不存在"}
        
        # 从向量存储中删除
        parent_ids_to_delete = []
        child_ids_to_delete = []
        
        for parent_id, parent in self.vector_store.parent_chunks.items():
            if parent.metadata.get("document_id") == document_id:
                parent_ids_to_delete.append(parent_id)
                for child in parent.child_chunks:
                    child_ids_to_delete.append(child.id)
        
        # 删除子块
        for child_id in child_ids_to_delete:
            if child_id in self.vector_store.documents:
                del self.vector_store.documents[child_id]
            if child_id in self.vector_store.embeddings:
                del self.vector_store.embeddings[child_id]
        
        # 删除父块
        for parent_id in parent_ids_to_delete:
            if parent_id in self.vector_store.parent_chunks:
                del self.vector_store.parent_chunks[parent_id]
        
        # 从知识库记录中删除
        del self.knowledge_bases[document_id]
        
        logger.info(f"文档删除成功: {document_id}")
        
        return {
            "success": True,
            "document_id": document_id,
            "deleted_parents": len(parent_ids_to_delete),
            "deleted_children": len(child_ids_to_delete),
            "message": "文档删除成功"
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取知识库统计信息
        
        Returns:
            Dict: 统计信息
        """
        return {
            "success": True,
            "stats": {
                "total_documents": len(self.knowledge_bases),
                "total_parent_chunks": len(self.vector_store.parent_chunks),
                "total_child_chunks": len(self.vector_store.documents),
                "total_embeddings": len(self.vector_store.embeddings),
                "embedding_mode": "mock" if self.use_mock else "real",
                "chunker_config": {
                    "parent_chunk_size": self.chunker.parent_chunk_size,
                    "parent_chunk_overlap": self.chunker.parent_chunk_overlap,
                    "child_chunk_size": self.chunker.child_chunk_size,
                    "child_chunk_overlap": self.chunker.child_chunk_overlap
                }
            }
        }