"""
语音处理工具
包括语音文件下载、格式转换和语音识别
"""
import os
import requests
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class AudioUtils:
    """音频处理工具类"""
    
    def __init__(self, output_dir: str = '/tmp'):
        """
        初始化音频工具
        
        Args:
            output_dir: 输出目录
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
    
    def download_audio_from_dingtalk(self, download_code: str, access_token: str, 
                                     filename: Optional[str] = None) -> Optional[str]:
        """
        从钉钉下载音频文件
        
        Args:
            download_code: 下载码
            access_token: 访问令牌
            filename: 保存的文件名（可选）
            
        Returns:
            str: 保存的文件路径，失败返回None
        """
        try:
            # 钉钉机器人下载文件的API
            url = "https://oapi.dingtalk.com/robot/messageFiles/download"
            params = {
                'access_token': access_token,
                'file_key': download_code
            }
            
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            # 生成文件名
            if not filename:
                filename = f"audio_{download_code[:10]}.amr"
            
            filepath = os.path.join(self.output_dir, filename)
            
            # 保存文件
            with open(filepath, 'wb') as f:
                f.write(response.content)
            
            logger.info(f"音频文件下载成功: {filepath}")
            return filepath
        
        except Exception as e:
            logger.error(f"下载音频文件失败: {str(e)}")
            return None
    
    def convert_amr_to_mp3(self, amr_path: str) -> Optional[str]:
        """
        将AMR格式转换为MP3格式
        使用ffmpeg进行转换
        
        Args:
            amr_path: AMR文件路径
            
        Returns:
            str: MP3文件路径，失败返回None
        """
        try:
            # 检查ffmpeg是否安装
            if os.system('which ffmpeg > /dev/null 2>&1') != 0:
                logger.warning("ffmpeg未安装，跳过格式转换")
                return amr_path  # 返回原文件
            
            mp3_path = amr_path.rsplit('.', 1)[0] + '.mp3'
            
            # 使用ffmpeg转换
            cmd = f"ffmpeg -i {amr_path} -ar 16000 -ac 1 {mp3_path} -y > /dev/null 2>&1"
            result = os.system(cmd)
            
            if result == 0 and os.path.exists(mp3_path):
                logger.info(f"音频格式转换成功: {mp3_path}")
                return mp3_path
            else:
                logger.warning("音频格式转换失败，使用原格式")
                return amr_path
        
        except Exception as e:
            logger.error(f"转换音频格式时出错: {str(e)}")
            return amr_path
    
    def get_access_token(self, app_key: str, app_secret: str) -> Optional[str]:
        """
        获取钉钉access_token
        
        Args:
            app_key: 应用Key
            app_secret: 应用Secret
            
        Returns:
            str: access_token，失败返回None
        """
        try:
            url = "https://oapi.dingtalk.com/gettoken"
            params = {
                'appkey': app_key,
                'appsecret': app_secret
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            if data.get('errcode') == 0:
                access_token = data.get('access_token')
                logger.info("获取access_token成功")
                return access_token
            else:
                logger.error(f"获取access_token失败: {data}")
                return None
        
        except Exception as e:
            logger.error(f"获取access_token时出错: {str(e)}")
            return None
    
    def cleanup_audio_file(self, filepath: str):
        """
        清理音频文件
        
        Args:
            filepath: 文件路径
        """
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
                logger.info(f"已清理音频文件: {filepath}")
        except Exception as e:
            logger.warning(f"清理音频文件失败: {str(e)}")


class VoiceProcessor:
    """语音处理器（集成音频下载和识别）"""
    
    def __init__(self, openai_utils, audio_utils: AudioUtils, 
                 app_key: str, app_secret: str):
        """
        初始化语音处理器
        
        Args:
            openai_utils: OpenAI工具实例
            audio_utils: 音频工具实例
            app_key: 钉钉应用Key
            app_secret: 钉钉应用Secret
        """
        self.openai_utils = openai_utils
        self.audio_utils = audio_utils
        self.app_key = app_key
        self.app_secret = app_secret
        self._access_token = None
    
    def get_access_token(self) -> Optional[str]:
        """获取或刷新access_token"""
        if not self._access_token:
            self._access_token = self.audio_utils.get_access_token(
                self.app_key, 
                self.app_secret
            )
        return self._access_token
    
    def process_voice_message(self, download_code: str) -> str:
        """
        处理语音消息（下载、识别、转文字）
        
        Args:
            download_code: 下载码
            
        Returns:
            str: 识别的文字内容
        """
        audio_path = None
        converted_path = None
        
        try:
            # 获取access_token
            access_token = self.get_access_token()
            if not access_token:
                return "抱歉，无法获取访问令牌，语音识别失败。"
            
            # 下载音频文件
            audio_path = self.audio_utils.download_audio_from_dingtalk(
                download_code=download_code,
                access_token=access_token
            )
            
            if not audio_path:
                return "抱歉，下载语音文件失败。"
            
            # 转换格式（如果需要）
            converted_path = self.audio_utils.convert_amr_to_mp3(audio_path)
            
            # 使用OpenAI Whisper识别
            text = self.openai_utils.transcribe_audio(converted_path)
            
            return text
        
        except Exception as e:
            logger.error(f"处理语音消息时出错: {str(e)}")
            return f"语音识别失败：{str(e)}"
        
        finally:
            # 清理临时文件
            if audio_path:
                self.audio_utils.cleanup_audio_file(audio_path)
            if converted_path and converted_path != audio_path:
                self.audio_utils.cleanup_audio_file(converted_path)
