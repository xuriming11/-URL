import os
import json
import hashlib
from datetime import datetime
from typing import List, Dict, Optional, Any

MEMORY_DIR = "memories"

try:
    from sentence_transformers import SentenceTransformer
    from sklearn.metrics.pairwise import cosine_similarity
    import numpy as np
    EMBEDDING_AVAILABLE = True
except ImportError:
    EMBEDDING_AVAILABLE = False
    print("Warning: sentence-transformers not available, semantic search will be disabled")

class MemoryItem:
    def __init__(
        self,
        session_id: str,
        content: str,
        summary: Optional[str] = None,
        embedding: Optional[List[float]] = None,
        keywords: Optional[List[str]] = None,
        timestamp: Optional[str] = None
    ):
        self.session_id = session_id
        self.content = content
        self.summary = summary
        self.embedding = embedding
        self.keywords = keywords or []
        self.timestamp = timestamp or datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "content": self.content,
            "summary": self.summary,
            "embedding": self.embedding,
            "keywords": self.keywords,
            "timestamp": self.timestamp
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MemoryItem':
        return cls(
            session_id=data.get("session_id", ""),
            content=data.get("content", ""),
            summary=data.get("summary"),
            embedding=data.get("embedding"),
            keywords=data.get("keywords", []),
            timestamp=data.get("timestamp")
        )

class LongTermMemory:
    def __init__(self):
        self.memory_dir = MEMORY_DIR
        self._ensure_dir()
        self.embedding_model = None
        if EMBEDDING_AVAILABLE:
            try:
                self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
                print("Embedding model loaded successfully")
            except Exception as e:
                print(f"Warning: Failed to load embedding model: {e}")
    
    def _ensure_dir(self):
        if not os.path.exists(self.memory_dir):
            os.makedirs(self.memory_dir)
    
    def _get_file_path(self, session_id: str) -> str:
        safe_session_id = hashlib.md5(session_id.encode()).hexdigest()
        return os.path.join(self.memory_dir, f"{safe_session_id}.json")
    
    def save_memory(self, session_id: str, content: str, summary: Optional[str] = None, keywords: Optional[List[str]] = None) -> bool:
        try:
            embedding = None
            if self.embedding_model:
                try:
                    embedding = self._generate_embedding(content).tolist()
                except Exception as e:
                    print(f"Warning: Failed to generate embedding: {e}")
            
            memory = MemoryItem(
                session_id=session_id,
                content=content,
                summary=summary,
                embedding=embedding,
                keywords=keywords or []
            )
            
            file_path = self._get_file_path(session_id)
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(memory.to_dict(), f, ensure_ascii=False, indent=2)
            
            return True
        except Exception as e:
            print(f"Error saving memory: {e}")
            return False
    
    def load_memory(self, session_id: str) -> Optional[MemoryItem]:
        try:
            file_path = self._get_file_path(session_id)
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return MemoryItem.from_dict(data)
            return None
        except Exception as e:
            print(f"Error loading memory: {e}")
            return None
    
    def delete_memory(self, session_id: str) -> bool:
        try:
            file_path = self._get_file_path(session_id)
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
            return False
        except Exception as e:
            print(f"Error deleting memory: {e}")
            return False
    
    def _generate_embedding(self, text: str) -> np.ndarray:
        if self.embedding_model:
            return self.embedding_model.encode(text)
        return np.zeros(384)
    
    def search_by_keyword(self, keyword: str, limit: int = 10) -> List[Dict[str, Any]]:
        results = []
        try:
            for filename in os.listdir(self.memory_dir):
                if filename.endswith('.json'):
                    file_path = os.path.join(self.memory_dir, filename)
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        content = data.get("content", "")
                        keywords = data.get("keywords", [])
                        
                        if keyword.lower() in content.lower() or keyword.lower() in [k.lower() for k in keywords]:
                            results.append(data)
            
            results.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
            return results[:limit]
        except Exception as e:
            print(f"Error searching by keyword: {e}")
            return []
    
    def search_by_semantic(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        if not self.embedding_model:
            print("Warning: Semantic search not available (embedding model not loaded)")
            return []
        
        results = []
        try:
            query_embedding = self._generate_embedding(query)
            
            for filename in os.listdir(self.memory_dir):
                if filename.endswith('.json'):
                    file_path = os.path.join(self.memory_dir, filename)
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        embedding = data.get("embedding")
                        
                        if embedding:
                            embedding_np = np.array(embedding).reshape(1, -1)
                            query_np = query_embedding.reshape(1, -1)
                            similarity = cosine_similarity(query_np, embedding_np)[0][0]
                            
                            results.append({
                                **data,
                                "similarity": float(similarity)
                            })
            
            results.sort(key=lambda x: x.get("similarity", 0), reverse=True)
            return results[:limit]
        except Exception as e:
            print(f"Error searching by semantic: {e}")
            return []
    
    def list_memories(self) -> List[Dict[str, Any]]:
        memories = []
        try:
            for filename in os.listdir(self.memory_dir):
                if filename.endswith('.json'):
                    file_path = os.path.join(self.memory_dir, filename)
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        memories.append(data)
            
            memories.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
            return memories
        except Exception as e:
            print(f"Error listing memories: {e}")
            return []
    
    def get_memory_count(self) -> int:
        try:
            return len([f for f in os.listdir(self.memory_dir) if f.endswith('.json')])
        except Exception as e:
            print(f"Error counting memories: {e}")
            return 0

long_term_memory = LongTermMemory()