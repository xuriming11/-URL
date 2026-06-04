from typing import List, Dict, Optional, Any
import re
from datetime import datetime

class MemoryItem:
    def __init__(self, keyword: str, content: str, session_id: str, timestamp: Optional[datetime] = None):
        self.keyword = keyword
        self.content = content
        self.session_id = session_id
        self.timestamp = timestamp or datetime.now()
        self.reference_count = 1
    
    def to_dict(self):
        return {
            "keyword": self.keyword,
            "content": self.content,
            "session_id": self.session_id,
            "timestamp": self.timestamp.isoformat(),
            "reference_count": self.reference_count
        }

class MemoryManager:
    def __init__(self):
        self.memories: Dict[str, List[MemoryItem]] = {}
    
    def extract_keywords(self, text: str) -> List[str]:
        patterns = [
            r'([\u4e00-\u9fa5]{2,})',
            r'([a-zA-Z]+(?:\s+[a-zA-Z]+)*)',
        ]
        
        keywords = set()
        for pattern in patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                cleaned = match.strip()
                if len(cleaned) >= 2 and not cleaned.isdigit():
                    keywords.add(cleaned)
        
        return list(keywords)
    
    def add_memory(self, session_id: str, content: str):
        keywords = self.extract_keywords(content)
        
        for keyword in keywords:
            if keyword not in self.memories:
                self.memories[keyword] = []
            
            existing = next((m for m in self.memories[keyword] if m.session_id == session_id and m.content == content), None)
            if existing:
                existing.reference_count += 1
                existing.timestamp = datetime.now()
            else:
                self.memories[keyword].append(MemoryItem(keyword, content, session_id))
    
    def search_by_keyword(self, keyword: str, session_id: Optional[str] = None) -> List[Dict]:
        results = []
        if keyword in self.memories:
            items = self.memories[keyword]
            if session_id:
                items = [item for item in items if item.session_id == session_id]
            results = [item.to_dict() for item in sorted(items, key=lambda x: x.timestamp, reverse=True)]
        return results
    
    def search_by_session(self, session_id: str) -> List[Dict]:
        results = []
        for keyword, items in self.memories.items():
            session_items = [item.to_dict() for item in items if item.session_id == session_id]
            results.extend(session_items)
        return sorted(results, key=lambda x: x['timestamp'], reverse=True)
    
    def get_all_keywords(self) -> List[str]:
        return list(self.memories.keys())
    
    def get_keyword_stats(self) -> Dict[str, int]:
        stats = {}
        for keyword, items in self.memories.items():
            stats[keyword] = sum(item.reference_count for item in items)
        return dict(sorted(stats.items(), key=lambda x: x[1], reverse=True))
    
    def delete_memory(self, keyword: str, session_id: Optional[str] = None):
        if keyword in self.memories:
            if session_id:
                self.memories[keyword] = [item for item in items if item.session_id != session_id]
                if not self.memories[keyword]:
                    del self.memories[keyword]
            else:
                del self.memories[keyword]
    
    def clear_session_memories(self, session_id: str):
        for keyword in list(self.memories.keys()):
            self.memories[keyword] = [item for item in self.memories[keyword] if item.session_id != session_id]
            if not self.memories[keyword]:
                del self.memories[keyword]

memory_manager = MemoryManager()

def remember_user_question(session_id: str, question: str):
    memory_manager.add_memory(session_id, question)

def recall_related_info(session_id: str, query: str) -> str:
    keywords = memory_manager.extract_keywords(query)
    related_memories = []
    
    for keyword in keywords:
        memories = memory_manager.search_by_keyword(keyword, session_id)
        related_memories.extend(memories)
    
    if not related_memories:
        return ""
    
    unique_memories = {}
    for mem in related_memories:
        key = mem['content']
        if key not in unique_memories or mem['reference_count'] > unique_memories[key]['reference_count']:
            unique_memories[key] = mem
    
    sorted_memories = sorted(unique_memories.values(), key=lambda x: x['reference_count'], reverse=True)
    
    context = "\n".join([f"- {mem['content']}" for mem in sorted_memories[:5]])
    return f"用户之前问过的相关问题：\n{context}"