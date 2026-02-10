"""
配置文件
存储所有系统配置和环境变量
"""
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class Config:
    """系统配置类"""
    
    # Flask配置
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-here')
    DEBUG = os.getenv('DEBUG', 'False') == 'True'
    
    # 钉钉配置
    DINGTALK_APP_KEY = os.getenv('DINGTALK_APP_KEY', '')
    DINGTALK_APP_SECRET = os.getenv('DINGTALK_APP_SECRET', '')
    DINGTALK_WEBHOOK_URL = os.getenv('DINGTALK_WEBHOOK_URL', '')
    DINGTALK_ROBOT_CODE = os.getenv('DINGTALK_ROBOT_CODE', '')
    
    # OpenAI配置
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
    OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-4-turbo')
    OPENAI_BASE_URL = os.getenv('OPENAI_BASE_URL', 'https://api.openai.com/v1')
    
    # NewsAPI配置
    NEWS_API_KEY = os.getenv('NEWS_API_KEY', '')
    NEWS_API_URL = 'https://newsapi.org/v2/everything'
    
    # 文件存储配置
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', '/tmp/dingtalk-ai-assistant')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    
    # 定时任务配置
    DAILY_NEWS_TIME = os.getenv('DAILY_NEWS_TIME', '09:00')  # 每天推送时间
    TIMEZONE = os.getenv('TIMEZONE', 'Asia/Shanghai')
    
    # AI助手配置
    SYSTEM_PROMPT = """你是一个专业的AI助手，专注于人工智能、机器学习和深度学习领域。
你的任务是：
1. 回答用户关于AI的各种问题
2. 当用户需要详细报告时，生成结构化的专业内容
3. 保持友好、专业的对话风格
4. 如果问题超出AI领域，礼貌地引导用户回到AI相关话题
"""
    
    # 报告生成配置
    REPORT_TRIGGER_KEYWORDS = ['报告', '详细', '分析', '深入', '研究']
    
    @staticmethod
    def init_app(app):
        """初始化Flask应用配置"""
        # 创建必要的目录
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
