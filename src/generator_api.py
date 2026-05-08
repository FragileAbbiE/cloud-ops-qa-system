"""基于 API 的答案生成器"""
from openai import OpenAI
import os

class APIAnswerGenerator:
    def __init__(self, api_key=None, api_base=None, model="Qwen/Qwen2.5-7B-Instruct"):
        self.client = OpenAI(
            api_key=api_key or os.getenv("OPENAI_API_KEY"),
            base_url=api_base or "https://api.siliconflow.cn/v1"
        )
        self.model = model
    
    def generate(self, query: str, retrieved_docs: list) -> str:
        context = "\n\n".join([
            f"文档 {i+1}:\n{doc['content']}"
            for i, doc in enumerate(retrieved_docs)
        ])
        
        prompt = f"""你是云运维专家。基于以下文档回答问题。

参考文档：
{context}

问题：{query}

请提供详细答案。如果文档中没有相关信息，请说明。"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "你是专业的云运维助手。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=2048
        )
        
        return response.choices[0].message.content
