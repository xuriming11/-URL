from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, List, Dict
from qianwen_agent import chat_with_qianwen, chat_with_qianwen_sync
from agent_state import session_manager, AgentState
from memory_tools import memory_manager
from mock_data import (
    get_all_customers, get_customer_by_id, get_customers_by_vip_level, search_customers,
    get_all_products, get_product_by_id, get_products_by_category, search_products,
    get_all_orders, get_order_by_id, get_orders_by_customer, get_orders_by_status,
    get_all_categories, get_customer_order_history
)
import uvicorn

long_term_memory = None

def get_long_term_memory():
    global long_term_memory
    if long_term_memory is None:
        try:
            from long_term_memory import long_term_memory as ltm
            long_term_memory = ltm
        except Exception as e:
            print(f"Warning: Failed to load long term memory: {e}")
            long_term_memory = None
    return long_term_memory

app = FastAPI(title="智能客服机器人 API", version="1.0", docs_url=None, redoc_url=None)

@app.get("/")
async def root():
    from fastapi.responses import FileResponse
    return FileResponse("static/index.html")

app.mount("/static", StaticFiles(directory="static"), name="static_files")

class ChatRequest(BaseModel):
    prompt: str
    session_id: Optional[str] = None
    customer_id: Optional[str] = None

class ChatResponse(BaseModel):
    session_id: str
    response: str
    messages: List[Dict]

class SessionResponse(BaseModel):
    session_id: str
    messages: List[Dict]
    created_at: str
    last_updated: str
    context: Dict

class CreateSessionResponse(BaseModel):
    session_id: str
    message: str

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        if request.session_id:
            state = session_manager.get_session(request.session_id)
            if not state:
                raise HTTPException(status_code=404, detail="会话不存在")
        else:
            state = session_manager.create_session()
        
        state.add_message("user", request.prompt)
        response_text = await chat_with_qianwen(state, request.prompt, request.customer_id)
        state.add_message("assistant", response_text)
        
        session_manager.update_session(state.session_id, state)
        
        return {
            "session_id": state.session_id,
            "response": response_text,
            "messages": state.get_history()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat_sync", response_model=ChatResponse)
def chat_sync(request: ChatRequest):
    try:
        if request.session_id:
            state = session_manager.get_session(request.session_id)
            if not state:
                raise HTTPException(status_code=404, detail="会话不存在")
        else:
            state = session_manager.create_session()
        
        state.add_message("user", request.prompt)
        response_text = chat_with_qianwen_sync(state, request.prompt, request.customer_id)
        state.add_message("assistant", response_text)
        
        session_manager.update_session(state.session_id, state)
        
        return {
            "session_id": state.session_id,
            "response": response_text,
            "messages": state.get_history()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/session", response_model=CreateSessionResponse)
def create_session():
    state = session_manager.create_session()
    return {
        "session_id": state.session_id,
        "message": "会话创建成功"
    }

@app.get("/session/{session_id}", response_model=SessionResponse)
def get_session(session_id: str):
    state = session_manager.get_session(session_id)
    if not state:
        raise HTTPException(status_code=404, detail="会话不存在")
    return state.to_dict()

@app.get("/sessions")
def list_sessions():
    return {
        "count": session_manager.get_session_count(),
        "sessions": session_manager.list_sessions()
    }

@app.delete("/session/{session_id}")
def delete_session(session_id: str):
    state = session_manager.get_session(session_id)
    if not state:
        raise HTTPException(status_code=404, detail="会话不存在")
    session_manager.delete_session(session_id)
    return {"message": "会话删除成功"}

@app.post("/session/{session_id}/clear")
def clear_session(session_id: str):
    state = session_manager.get_session(session_id)
    if not state:
        raise HTTPException(status_code=404, detail="会话不存在")
    state.clear()
    session_manager.update_session(session_id, state)
    return {"message": "会话内容已清空"}

@app.post("/session/{session_id}/context")
def set_session_context(session_id: str, key: str, value: str):
    state = session_manager.get_session(session_id)
    if not state:
        raise HTTPException(status_code=404, detail="会话不存在")
    state.set_context(key, value)
    session_manager.update_session(session_id, state)
    return {"message": "上下文设置成功", "context": state.get_context()}

@app.get("/session/{session_id}/context")
def get_session_context(session_id: str):
    state = session_manager.get_session(session_id)
    if not state:
        raise HTTPException(status_code=404, detail="会话不存在")
    return {"context": state.get_context()}

@app.get("/memory/keywords")
def get_all_keywords():
    return {"keywords": memory_manager.get_all_keywords()}

@app.get("/memory/keywords/stats")
def get_keyword_stats():
    return {"stats": memory_manager.get_keyword_stats()}

@app.get("/memory/search")
def search_memory(keyword: str, session_id: Optional[str] = None):
    results = memory_manager.search_by_keyword(keyword, session_id)
    return {"results": results}

@app.get("/memory/session/{session_id}")
def get_session_memories(session_id: str):
    results = memory_manager.search_by_session(session_id)
    return {"results": results}

@app.delete("/memory/keyword/{keyword}")
def delete_memory_by_keyword(keyword: str, session_id: Optional[str] = None):
    memory_manager.delete_memory(keyword, session_id)
    return {"message": "记忆已删除"}

@app.delete("/memory/session/{session_id}")
def clear_session_memories(session_id: str):
    memory_manager.clear_session_memories(session_id)
    return {"message": "会话记忆已清空"}

@app.get("/api/customers")
def api_get_all_customers(vip_level: Optional[str] = None, keyword: Optional[str] = None):
    if vip_level:
        return {"customers": get_customers_by_vip_level(vip_level)}
    elif keyword:
        return {"customers": search_customers(keyword)}
    return {"customers": get_all_customers()}

@app.get("/api/customers/{customer_id}")
def api_get_customer(customer_id: str):
    customer = get_customer_by_id(customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="客户不存在")
    return customer

@app.get("/api/customers/{customer_id}/orders")
def api_get_customer_orders(customer_id: str):
    customer = get_customer_by_id(customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="客户不存在")
    orders = get_customer_order_history(customer_id)
    return {"customer_name": customer["name"], "orders": orders}

@app.get("/api/products")
def api_get_all_products(category: Optional[str] = None, keyword: Optional[str] = None):
    if category:
        return {"products": get_products_by_category(category)}
    elif keyword:
        return {"products": search_products(keyword)}
    return {"products": get_all_products()}

@app.get("/api/products/{product_id}")
def api_get_product(product_id: str):
    product = get_product_by_id(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="产品不存在")
    return product

@app.get("/api/orders")
def api_get_all_orders(customer_id: Optional[str] = None, status: Optional[str] = None):
    if customer_id:
        return {"orders": get_orders_by_customer(customer_id)}
    elif status:
        return {"orders": get_orders_by_status(status)}
    return {"orders": get_all_orders()}

@app.get("/api/orders/{order_id}")
def api_get_order(order_id: str):
    order = get_order_by_id(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    return order

@app.get("/api/categories")
def api_get_all_categories():
    return {"categories": get_all_categories()}

@app.post("/longterm/save")
def save_longterm_memory(session_id: str, content: str, summary: Optional[str] = None):
    ltm = get_long_term_memory()
    if not ltm:
        raise HTTPException(status_code=503, detail="长期记忆服务不可用")
    keywords = memory_manager.extract_keywords(content)
    success = ltm.save_memory(session_id, content, summary, keywords)
    if success:
        return {"message": "长期记忆保存成功", "session_id": session_id}
    else:
        raise HTTPException(status_code=500, detail="保存失败")

@app.get("/longterm/load")
def load_longterm_memory(session_id: str):
    ltm = get_long_term_memory()
    if not ltm:
        raise HTTPException(status_code=503, detail="长期记忆服务不可用")
    memory = ltm.load_memory(session_id)
    if memory:
        return memory.to_dict()
    else:
        raise HTTPException(status_code=404, detail="记忆不存在")

@app.delete("/longterm/delete")
def delete_longterm_memory(session_id: str):
    ltm = get_long_term_memory()
    if not ltm:
        raise HTTPException(status_code=503, detail="长期记忆服务不可用")
    success = ltm.delete_memory(session_id)
    if success:
        return {"message": "长期记忆删除成功"}
    else:
        raise HTTPException(status_code=404, detail="记忆不存在")

@app.get("/longterm/search/keyword")
def search_longterm_by_keyword(keyword: str, limit: int = 10):
    ltm = get_long_term_memory()
    if not ltm:
        return {"results": [], "warning": "长期记忆服务不可用"}
    results = ltm.search_by_keyword(keyword, limit)
    return {"results": results}

@app.get("/longterm/search/semantic")
def search_longterm_by_semantic(query: str, limit: int = 10):
    ltm = get_long_term_memory()
    if not ltm:
        return {"results": [], "warning": "长期记忆服务不可用"}
    results = ltm.search_by_semantic(query, limit)
    return {"results": results}

@app.get("/longterm/list")
def list_longterm_memories():
    ltm = get_long_term_memory()
    if not ltm:
        return {"count": 0, "memories": [], "warning": "长期记忆服务不可用"}
    memories = ltm.list_memories()
    return {"count": len(memories), "memories": memories}

@app.get("/longterm/count")
def count_longterm_memories():
    ltm = get_long_term_memory()
    if not ltm:
        return {"count": 0, "warning": "长期记忆服务不可用"}
    count = ltm.get_memory_count()
    return {"count": count}

@app.post("/session/{session_id}/save_longterm")
def save_session_to_longterm(session_id: str, summary: Optional[str] = None):
    ltm = get_long_term_memory()
    if not ltm:
        raise HTTPException(status_code=503, detail="长期记忆服务不可用")
    
    state = session_manager.get_session(session_id)
    if not state:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    messages = state.get_history()
    content = "\n".join([f"{msg['role']}: {msg['content']}" for msg in messages])
    keywords = []
    for msg in messages:
        keywords.extend(memory_manager.extract_keywords(msg['content']))
    
    success = ltm.save_memory(session_id, content, summary, keywords)
    if success:
        return {"message": "会话已保存到长期记忆"}
    else:
        raise HTTPException(status_code=500, detail="保存失败")

@app.get("/health")
def health_check():
    ltm = get_long_term_memory()
    ltm_count = ltm.get_memory_count() if ltm else 0
    return {"status": "healthy", "session_count": session_manager.get_session_count(), "longterm_count": ltm_count}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)