"""
基于检索结果的答案生成模块
使用 Qwen2.5-7B-Instruct 生成规范化的运维解决方案
"""

import yaml
from typing import List, Dict
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

class AnswerGenerator:
    """答案生成器：基于检索到的知识生成运维解决方案"""
    
    def __init__(self, config_path: str = "config/config.yaml"):
        """初始化生成器"""
        # 加载配置
        with open(config_path, "r", encoding="utf-8") as f:
            self.config = yaml.safe_load(f)
        
        # 加载大模型
        model_path = self.config['llm']['model_name']
        print(f"加载大模型: {model_path}")
        
        self.tokenizer = AutoTokenizer.from_pretrained(
            model_path,
            trust_remote_code=True
        )
        
        self.model = AutoModelForCausalLM.from_pretrained(
            model_path,
            torch_dtype=torch.float16,
            device_map="auto",
            trust_remote_code=True
        )
        
        print(f"✓ 模型加载完成")
    
    def _build_prompt(self, query: str, retrieved_docs: List[Dict]) -> str:
        """构建提示词模板"""
        # 组装检索到的知识
        knowledge_context = ""
        for i, doc in enumerate(retrieved_docs, 1):
            knowledge_context += f"\n【参考文档 {i}】\n"
            knowledge_context += f"产品线: {doc['product_line']}\n"
            knowledge_context += f"组件: {doc['component']}\n"
            knowledge_context += f"文档类型: {doc['doc_type']}\n"
            knowledge_context += f"内容:\n{doc['text']}\n"
            knowledge_context += f"来源: {doc['source_file']}\n"
            knowledge_context += "-" * 60
        
        # 构建完整提示词
        prompt = f"""你是一位经验丰富的云原生运维专家，擅长解决 Kubernetes、数据库、网关、存储等基础设施的故障问题。

用户问题：
{query}

参考知识库：
{knowledge_context}

请根据上述参考文档，为用户提供详细的故障排查和解决方案。要求：

1. **问题分析**：简要说明故障的可能原因
2. **排查步骤**：提供具体的命令和操作步骤
3. **解决方案**：给出明确的修复方法
4. **预防措施**：建议如何避免类似问题再次发生

注意：
- 只使用参考文档中的信息，不要编造内容
- 如果参考文档不足以回答问题，明确说明需要更多信息
- 使用 Markdown 格式组织答案，便于阅读
- 命令和配置用代码块标注

请开始回答："""
        
        return prompt
    
    def generate(self, query: str, retrieved_docs: List[Dict], max_length: int = 2048) -> str:
        """
        生成答案
        
        Args:
            query: 用户查询
            retrieved_docs: 检索到的文档列表
            max_length: 生成的最大长度
        
        Returns:
            生成的答案
        """
        # 构建提示词
        prompt = self._build_prompt(query, retrieved_docs)
        
        # 编码输入
        messages = [
            {"role": "system", "content": "你是一位专业的云原生运维专家。"},
            {"role": "user", "content": prompt}
        ]
        
        text = self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )
        
        model_inputs = self.tokenizer([text], return_tensors="pt").to(self.model.device)
        
        # 生成答案
        print("\n正在生成答案...")
        generated_ids = self.model.generate(
            **model_inputs,
            max_new_tokens=max_length,
            temperature=0.7,
            top_p=0.9,
            do_sample=True
        )
        
        # 解码输出
        generated_ids = [
            output_ids[len(input_ids):] 
            for input_ids, output_ids in zip(model_inputs.input_ids, generated_ids)
        ]
        
        response = self.tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]
        
        return response
    
    def generate_stream(self, query: str, retrieved_docs: List[Dict]):
        """
        流式生成答案（逐字返回）
        
        Args:
            query: 用户查询
            retrieved_docs: 检索到的文档列表
        
        Yields:
            生成的文本片段
        """
        from transformers import TextIteratorStreamer
        from threading import Thread
        
        # 构建提示词
        prompt = self._build_prompt(query, retrieved_docs)
        
        messages = [
            {"role": "system", "content": "你是一位专业的云原生运维专家。"},
            {"role": "user", "content": prompt}
        ]
        
        text = self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )
        
        model_inputs = self.tokenizer([text], return_tensors="pt").to(self.model.device)
        
        # 创建流式输出器
        streamer = TextIteratorStreamer(
            self.tokenizer,
            skip_prompt=True,
            skip_special_tokens=True
        )
        
        # 在后台线程中生成
        generation_kwargs = dict(
            **model_inputs,
            streamer=streamer,
            max_new_tokens=2048,
            temperature=0.7,
            top_p=0.9,
            do_sample=True
        )
        
        thread = Thread(target=self.model.generate, kwargs=generation_kwargs)
        thread.start()
        
        # 逐字返回
        for text in streamer:
            yield text


# 测试代码
if __name__ == "__main__":
    from retriever import MRAGRetriever
    
    # 初始化检索器和生成器
    retriever = MRAGRetriever()
    generator = AnswerGenerator()
    
    # 测试查询
    query = "Kubernetes Pod 一直处于 Pending 状态怎么办？"
    
    # 检索相关文档
    print(f"查询: {query}\n")
    retrieved_docs = retriever.retrieve(query, top_k=3)
    
    # 生成答案
    answer = generator.generate(query, retrieved_docs)
    
    print("\n" + "="*60)
    print("生成的答案:")
    print("="*60)
    print(answer)

