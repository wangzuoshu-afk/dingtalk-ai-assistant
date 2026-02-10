"""
钉钉相关工具函数
包括签名验证、消息发送等功能
"""
import time
import hmac
import hashlib
import base64
import json
import requests
from typing import Dict, Any, Optional


class DingTalkUtils:
    """钉钉工具类"""
    
    @staticmethod
    def verify_signature(timestamp: str, sign: str, app_secret: str) -> bool:
        """
        验证钉钉请求签名
        
        Args:
            timestamp: 时间戳
            sign: 签名
            app_secret: 应用密钥
            
        Returns:
            bool: 验证是否通过
        """
        # 检查时间戳是否在1小时内
        current_time = int(time.time() * 1000)
        request_time = int(timestamp)
        if abs(current_time - request_time) > 3600000:  # 1小时 = 3600000毫秒
            return False
        
        # 计算签名
        string_to_sign = f"{timestamp}\n{app_secret}"
        hmac_code = hmac.new(
            app_secret.encode('utf-8'),
            string_to_sign.encode('utf-8'),
            digestmod=hashlib.sha256
        ).digest()
        calculated_sign = base64.b64encode(hmac_code).decode('utf-8')
        
        return calculated_sign == sign
    
    @staticmethod
    def send_text_message(webhook_url: str, content: str, 
                         at_mobiles: Optional[list] = None,
                         is_at_all: bool = False) -> Dict[str, Any]:
        """
        发送文本消息到钉钉群
        
        Args:
            webhook_url: Webhook地址
            content: 消息内容
            at_mobiles: @的手机号列表
            is_at_all: 是否@所有人
            
        Returns:
            dict: 发送结果
        """
        data = {
            "msgtype": "text",
            "text": {
                "content": content
            },
            "at": {
                "atMobiles": at_mobiles or [],
                "isAtAll": is_at_all
            }
        }
        
        headers = {'Content-Type': 'application/json'}
        response = requests.post(webhook_url, json=data, headers=headers)
        return response.json()
    
    @staticmethod
    def send_markdown_message(webhook_url: str, title: str, text: str,
                             at_mobiles: Optional[list] = None,
                             is_at_all: bool = False) -> Dict[str, Any]:
        """
        发送Markdown消息到钉钉群
        
        Args:
            webhook_url: Webhook地址
            title: 消息标题
            text: Markdown格式的消息内容
            at_mobiles: @的手机号列表
            is_at_all: 是否@所有人
            
        Returns:
            dict: 发送结果
        """
        data = {
            "msgtype": "markdown",
            "markdown": {
                "title": title,
                "text": text
            },
            "at": {
                "atMobiles": at_mobiles or [],
                "isAtAll": is_at_all
            }
        }
        
        headers = {'Content-Type': 'application/json'}
        response = requests.post(webhook_url, json=data, headers=headers)
        return response.json()
    
    @staticmethod
    def send_link_message(webhook_url: str, title: str, text: str,
                         message_url: str, pic_url: Optional[str] = None) -> Dict[str, Any]:
        """
        发送链接消息到钉钉群
        
        Args:
            webhook_url: Webhook地址
            title: 消息标题
            text: 消息内容
            message_url: 点击消息跳转的URL
            pic_url: 图片URL
            
        Returns:
            dict: 发送结果
        """
        data = {
            "msgtype": "link",
            "link": {
                "title": title,
                "text": text,
                "messageUrl": message_url,
                "picUrl": pic_url or ""
            }
        }
        
        headers = {'Content-Type': 'application/json'}
        response = requests.post(webhook_url, json=data, headers=headers)
        return response.json()
    
    @staticmethod
    def create_response_message(msg_type: str, content: str) -> Dict[str, Any]:
        """
        创建回复消息的JSON格式
        
        Args:
            msg_type: 消息类型 (text/markdown)
            content: 消息内容
            
        Returns:
            dict: 回复消息的JSON对象
        """
        if msg_type == "text":
            return {
                "msgtype": "text",
                "text": {
                    "content": content
                }
            }
        elif msg_type == "markdown":
            return {
                "msgtype": "markdown",
                "markdown": {
                    "title": "AI助手回复",
                    "text": content
                }
            }
        else:
            return {
                "msgtype": "text",
                "text": {
                    "content": content
                }
            }
    
    @staticmethod
    def parse_message(request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        解析钉钉消息
        
        Args:
            request_data: 钉钉发送的请求数据
            
        Returns:
            dict: 解析后的消息信息
        """
        msg_type = request_data.get('msgtype', '')
        conversation_type = request_data.get('conversationType', '')
        sender_id = request_data.get('senderId', '')
        sender_nick = request_data.get('senderNick', '')
        conversation_id = request_data.get('conversationId', '')
        
        result = {
            'msg_type': msg_type,
            'conversation_type': conversation_type,
            'sender_id': sender_id,
            'sender_nick': sender_nick,
            'conversation_id': conversation_id,
            'content': '',
            'download_code': None
        }
        
        # 根据消息类型提取内容
        if msg_type == 'text':
            result['content'] = request_data.get('text', {}).get('content', '')
        elif msg_type == 'audio':
            result['download_code'] = request_data.get('content', {}).get('downloadCode', '')
            result['duration'] = request_data.get('content', {}).get('duration', 0)
        elif msg_type == 'picture':
            result['download_code'] = request_data.get('content', {}).get('downloadCode', '')
            result['picture_url'] = request_data.get('content', {}).get('pictureDownloadCode', '')
        
        return result
    
    @staticmethod
    def download_media_file(download_code: str, access_token: str) -> bytes:
        """
        下载钉钉媒体文件
        
        Args:
            download_code: 下载码
            access_token: 访问令牌
            
        Returns:
            bytes: 文件内容
        """
        url = f"https://oapi.dingtalk.com/robot/messageFiles/download"
        params = {
            'access_token': access_token,
            'file_key': download_code
        }
        response = requests.get(url, params=params)
        if response.status_code == 200:
            return response.content
        else:
            raise Exception(f"下载文件失败: {response.text}")
