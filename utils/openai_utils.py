"""
OpenAI相关工具函数
包括对话生成、语音识别等功能
"""
from openai import OpenAI
from typing import List, Dict, Any, Optional
import os


class OpenAIUtils:
    """OpenAI工具类"""
    
    def __init__(self, api_key: str, base_url: Optional[str] = None, model: str = 'gpt-4-turbo'):
        """
        初始化OpenAI客户端
        
        Args:
            api_key: OpenAI API密钥
            base_url: API基础URL（可选）
            model: 使用的模型名称
        """
        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url
        )
        self.model = model
        self.conversation_history: Dict[str, List[Dict[str, str]]] = {}
    
    def chat(self, user_id: str, message: str, system_prompt: str = "") -> str:
        """
        与AI进行对话
        
        Args:
            user_id: 用户ID（用于维护对话历史）
            message: 用户消息
            system_prompt: 系统提示词
            
        Returns:
            str: AI的回复
        """
        # 初始化或获取对话历史
        if user_id not in self.conversation_history:
            self.conversation_history[user_id] = []
            if system_prompt:
                self.conversation_history[user_id].append({
                    "role": "system",
                    "content": system_prompt
                })
        
        # 添加用户消息
        self.conversation_history[user_id].append({
            "role": "user",
            "content": message
        })
        
        # 限制历史记录长度（保留最近10轮对话）
        if len(self.conversation_history[user_id]) > 21:  # system + 10轮对话(20条)
            # 保留system消息和最近的20条消息
            system_msg = [msg for msg in self.conversation_history[user_id] if msg['role'] == 'system']
            recent_msgs = self.conversation_history[user_id][-20:]
            self.conversation_history[user_id] = system_msg + recent_msgs
        
        try:
            # 调用OpenAI API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=self.conversation_history[user_id],
                temperature=0.7,
                max_tokens=2000
            )
            
            # 获取回复
            assistant_message = response.choices[0].message.content
            
            # 添加助手回复到历史
            self.conversation_history[user_id].append({
                "role": "assistant",
                "content": assistant_message
            })
            
            return assistant_message
        
        except Exception as e:
            return f"抱歉，处理您的请求时出现错误：{str(e)}"
    
    def generate_report_content(self, topic: str, system_prompt: str = "") -> str:
        """
        生成详细报告内容
        
        Args:
            topic: 报告主题
            system_prompt: 系统提示词
            
        Returns:
            str: 报告内容
        """
        prompt = f"""请针对以下主题生成一份详细的专业报告：

主题：{topic}

要求：
1. 报告应包含以下部分：标题、摘要、引言、主体内容（分多个章节）、结论
2. 内容要专业、准确、有深度
3. 使用Markdown格式组织内容
4. 每个章节要有清晰的标题和结构
5. 适当引用相关技术、案例或数据
6. 总字数控制在2000-3000字

请开始生成报告："""
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=4000
            )
            
            return response.choices[0].message.content
        
        except Exception as e:
            return f"生成报告时出现错误：{str(e)}"
    
    def transcribe_audio(self, audio_file_path: str) -> str:
        """
        将音频文件转换为文字
        
        Args:
            audio_file_path: 音频文件路径
            
        Returns:
            str: 转录的文字内容
        """
        try:
            with open(audio_file_path, 'rb') as audio_file:
                transcript = self.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    language="zh"  # 指定中文
                )
            return transcript.text
        
        except Exception as e:
            return f"语音识别失败：{str(e)}"
    
    def clear_conversation(self, user_id: str):
        """
        清除用户的对话历史
        
        Args:
            user_id: 用户ID
        """
        if user_id in self.conversation_history:
            del self.conversation_history[user_id]
    
    def should_generate_report(self, message: str, keywords: List[str]) -> bool:
        """
        判断是否需要生成报告
        
        Args:
            message: 用户消息
            keywords: 触发关键词列表
            
        Returns:
            bool: 是否需要生成报告
        """
        return any(keyword in message for keyword in keywords)
