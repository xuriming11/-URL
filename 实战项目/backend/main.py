from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List, AsyncGenerator
import os
import asyncio

try:
    from langchain_openai import ChatOpenAI
    from langchain.prompts import PromptTemplate
    from langchain.chains import LLMChain
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False

app = FastAPI(title="智能文案生成器", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class GenerateRequest(BaseModel):
    product_name: str
    product_description: str
    target_audience: str
    tone: str = "professional"
    platform: str = "general"
    length: str = "medium"

class GenerateResponse(BaseModel):
    success: bool
    content: str
    type: str

class BatchGenerateRequest(BaseModel):
    requests: List[GenerateRequest]

class BatchGenerateResponse(BaseModel):
    success: bool
    results: List[GenerateResponse]

class MockLLM:
    def generate(self, prompts):
        responses = []
        for prompt in prompts:
            text = prompt.text
            if "产品名称" in text and "描述" in text:
                responses.append("根据您的需求，为您生成以下文案：\n\n【产品名称】智能AI助手\n【核心卖点】基于先进的大语言模型，为您提供智能化的文案创作服务\n\n这是一个专业、简洁的产品描述，适合在多个平台使用。")
            else:
                responses.append("这是一个示例文案响应。在实际使用中，这里会调用真实的LLM模型生成文案。")
        return type('obj', (object,), {'generations': [[type('gen', (object,), {'text': r}) for r in responses]]})
    
    def invoke(self, prompt):
        return type('obj', (object,), {'content': """
【标题】探索智能文案生成器 - 让创作更高效

【产品描述】
智能文案生成器是一款基于先进AI技术的内容创作工具，能够帮助您快速生成高质量的营销文案、产品描述、社交媒体内容等。

【核心优势】
✅ 智能分析产品特性
✅ 精准定位目标受众
✅ 支持多种语气风格
✅ 一键生成多平台文案

【适用场景】
- 电商产品描述
- 社交媒体帖子
- 广告宣传文案
- 品牌故事创作

【结语】
释放您的创作潜能，让AI成为您的创意伙伴！
        """.strip()})
    
    def stream(self, prompt):
        content = self.invoke(prompt).content
        for char in content:
            yield type('obj', (object,), {'content': char})

class CopyGenerator:
    def __init__(self):
        self.use_real_llm = LANGCHAIN_AVAILABLE and os.getenv("OPENAI_API_KEY")
        
        self.prompt_template = PromptTemplate(
            input_variables=["product_name", "product_description", "target_audience", "tone", "platform", "length"],
            template="""
作为一名专业的文案策划师，请根据以下信息为产品生成高质量的文案：

产品名称：{product_name}
产品描述：{product_description}
目标受众：{target_audience}
语气风格：{tone}（可选：professional专业、casual随意、humorous幽默、formal正式）
发布平台：{platform}（可选：general通用、wechat微信、weibo微博、douyin抖音、电商平台）
文案长度：{length}（可选：short简短、medium中等、long详细）

请生成适合该产品的营销文案，包括标题、描述、核心卖点等内容。
                """.strip()
        )
        
        if self.use_real_llm:
            self.llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.9)
            self.chain = LLMChain(llm=self.llm, prompt=self.prompt_template)
        else:
            self.llm = MockLLM()
    
    def generate(self, request: GenerateRequest):
        try:
            if self.use_real_llm:
                result = self.chain.run(
                    product_name=request.product_name,
                    product_description=request.product_description,
                    target_audience=request.target_audience,
                    tone=request.tone,
                    platform=request.platform,
                    length=request.length
                )
            else:
                result = self.llm.invoke(request.product_name)
                result = result.content
            
            return {"success": True, "content": result, "type": "real" if self.use_real_llm else "mock"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    async def generate_stream(self, request: GenerateRequest) -> AsyncGenerator[str, None]:
        try:
            prompt = self.prompt_template.format(
                product_name=request.product_name,
                product_description=request.product_description,
                target_audience=request.target_audience,
                tone=request.tone,
                platform=request.platform,
                length=request.length
            )
            for chunk in self.llm.stream(prompt):
                yield chunk.content
                if not self.use_real_llm:
                    await asyncio.sleep(0.02)
        except Exception as e:
            yield f"Error: {str(e)}"

generator = CopyGenerator()

@app.get("/")
def read_root():
    return {"message": "智能文案生成器 API"}

@app.get("/health")
def health_check():
    return {"status": "healthy", "langchain_available": LANGCHAIN_AVAILABLE, "using_real_llm": generator.use_real_llm}

@app.post("/generate", response_model=GenerateResponse)
def generate_copy(request: GenerateRequest):
    return generator.generate(request)

@app.post("/generate/stream")
async def generate_stream(request: GenerateRequest):
    return StreamingResponse(
        generator.generate_stream(request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive"
        }
    )

@app.post("/generate/batch", response_model=BatchGenerateResponse)
def generate_batch(request: BatchGenerateRequest):
    results = []
    for req in request.requests:
        try:
            result = generator.generate(req)
            results.append(result)
        except Exception as e:
            results.append({"success": False, "content": str(e), "type": "error"})
    return {"success": True, "results": results}

@app.get("/templates")
def get_templates():
    return {
        "tones": ["professional", "casual", "humorous", "formal", "warm", "energetic"],
        "platforms": ["general", "wechat", "weibo", "douyin", "taobao", "jd", "小红书"],
        "lengths": ["short", "medium", "long"]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)