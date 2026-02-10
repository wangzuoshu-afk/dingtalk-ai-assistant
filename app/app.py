"""
Flask主应用
处理钉钉机器人的消息接收和回复
"""
from flask import Flask, request, jsonify
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.config import Config
from utils.dingtalk_utils import DingTalkUtils
from utils.openai_utils import OpenAIUtils
from utils.pdf_utils import PDFGenerator
from utils.audio_utils import AudioUtils, VoiceProcessor
from app.scheduler import news_scheduler
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 创建Flask应用
app = Flask(__name__)
app.config.from_object(Config)
Config.init_app(app)

# 初始化工具类
dingtalk_utils = DingTalkUtils()
openai_utils = OpenAIUtils(
    api_key=Config.OPENAI_API_KEY,
    base_url=Config.OPENAI_BASE_URL,
    model=Config.OPENAI_MODEL
)
pdf_generator = PDFGenerator(output_dir=Config.UPLOAD_FOLDER)
audio_utils = AudioUtils(output_dir=Config.UPLOAD_FOLDER)
voice_processor = VoiceProcessor(
    openai_utils=openai_utils,
    audio_utils=audio_utils,
    app_key=Config.DINGTALK_APP_KEY,
    app_secret=Config.DINGTALK_APP_SECRET
)


@app.route('/', methods=['GET'])
def index():
    """健康检查接口"""
    return jsonify({
        'status': 'ok',
        'message': '钉钉AI助手运行中',
        'version': '1.0.0'
    })


@app.route('/webhook', methods=['POST'])
def webhook():
    """
    接收钉钉消息的Webhook接口
    """
    try:
        # 获取请求头
        timestamp = request.headers.get('timestamp', '')
        sign = request.headers.get('sign', '')
        
        # 验证签名
        if not dingtalk_utils.verify_signature(timestamp, sign, Config.DINGTALK_APP_SECRET):
            logger.warning("签名验证失败")
            return jsonify({'error': '签名验证失败'}), 401
        
        # 获取请求数据
        data = request.json
        logger.info(f"收到消息: {data}")
        
        # 解析消息
        message_info = dingtalk_utils.parse_message(data)
        msg_type = message_info['msg_type']
        sender_id = message_info['sender_id']
        sender_nick = message_info['sender_nick']
        
        # 处理不同类型的消息
        if msg_type == 'text':
            # 处理文本消息
            user_message = message_info['content']
            response_text = handle_text_message(sender_id, user_message, sender_nick)
            
            # 返回回复消息
            return jsonify(dingtalk_utils.create_response_message('text', response_text))
        
        elif msg_type == 'audio':
            # 处理语音消息
            response_text = handle_audio_message(message_info)
            return jsonify(dingtalk_utils.create_response_message('text', response_text))
        
        else:
            # 不支持的消息类型
            return jsonify(dingtalk_utils.create_response_message(
                'text', 
                f"抱歉，暂不支持{msg_type}类型的消息。请发送文字或语音消息。"
            ))
    
    except Exception as e:
        logger.error(f"处理消息时出错: {str(e)}", exc_info=True)
        return jsonify(dingtalk_utils.create_response_message(
            'text',
            "抱歉，处理您的消息时出现错误，请稍后再试。"
        ))


def handle_text_message(user_id: str, message: str, user_name: str) -> str:
    """
    处理文本消息
    
    Args:
        user_id: 用户ID
        message: 消息内容
        user_name: 用户昵称
        
    Returns:
        str: 回复内容
    """
    try:
        # 检查是否需要生成报告
        if openai_utils.should_generate_report(message, Config.REPORT_TRIGGER_KEYWORDS):
            return handle_report_request(user_id, message, user_name)
        
        # 普通对话
        response = openai_utils.chat(
            user_id=user_id,
            message=message,
            system_prompt=Config.SYSTEM_PROMPT
        )
        
        return response
    
    except Exception as e:
        logger.error(f"处理文本消息时出错: {str(e)}")
        return "抱歉，处理您的消息时出现错误。"


def handle_report_request(user_id: str, message: str, user_name: str) -> str:
    """
    处理报告生成请求
    
    Args:
        user_id: 用户ID
        message: 消息内容
        user_name: 用户昵称
        
    Returns:
        str: 回复内容
    """
    try:
        # 先回复用户正在生成
        response_text = f"收到您的请求，正在为您生成详细报告，请稍候...\n\n主题：{message}"
        
        # 生成报告内容
        logger.info(f"开始生成报告: {message}")
        report_content = openai_utils.generate_report_content(
            topic=message,
            system_prompt=Config.SYSTEM_PROMPT
        )
        
        # 生成PDF
        logger.info("开始生成PDF")
        pdf_path = pdf_generator.generate_report_pdf(
            content=report_content,
            title=f"AI报告 - {message[:30]}"
        )
        
        logger.info(f"PDF生成成功: {pdf_path}")
        
        # 注意：这里需要将PDF上传到可访问的服务器或云存储
        # 由于是示例代码，这里只返回本地路径提示
        # 实际部署时需要上传到OSS/S3等云存储服务
        
        response_text = f"""报告已生成完成！

📊 报告主题：{message}
👤 请求人：{user_name}
📄 文件已保存到服务器

由于当前环境限制，PDF文件已保存在服务器本地。
在生产环境中，文件将上传到云存储并提供下载链接。

报告摘要：
{report_content[:200]}...

完整内容请查看PDF文件。"""
        
        return response_text
    
    except Exception as e:
        logger.error(f"生成报告时出错: {str(e)}")
        return f"抱歉，生成报告时出现错误：{str(e)}"


def handle_audio_message(message_info: dict) -> str:
    """
    处理语音消息
    
    Args:
        message_info: 消息信息
        
    Returns:
        str: 回复内容
    """
    try:
        download_code = message_info.get('download_code')
        sender_id = message_info.get('sender_id')
        
        if not download_code:
            return "抱歉，无法获取语音文件。"
        
        # 检查是否配置了钉钉应用密钥
        if not Config.DINGTALK_APP_KEY or not Config.DINGTALK_APP_SECRET:
            return """收到您的语音消息！

由于语音消息处理需要配置钉钉应用密钥（DINGTALK_APP_KEY 和 DINGTALK_APP_SECRET），
当前环境未配置，暂时无法处理语音消息。

请您：
1. 使用文字消息与我交流
2. 或者配置应用密钥后使用语音功能

感谢您的理解！"""
        
        # 处理语音消息
        logger.info(f"开始处理语音消息: {download_code}")
        text = voice_processor.process_voice_message(download_code)
        
        # 如果识别成功，继续处理文字内容
        if text and not text.startswith("抱歉") and not text.startswith("语音识别失败"):
            logger.info(f"语音识别结果: {text}")
            # 使用识别的文字内容进行对话
            response = openai_utils.chat(
                user_id=sender_id,
                message=text,
                system_prompt=Config.SYSTEM_PROMPT
            )
            return f"🎤 您说：{text}\n\n{response}"
        else:
            return text
    
    except Exception as e:
        logger.error(f"处理语音消息时出错: {str(e)}")
        return "抱歉，处理语音消息时出现错误。"


@app.route('/health', methods=['GET'])
def health():
    """健康检查接口"""
    return jsonify({
        'status': 'healthy',
        'timestamp': os.popen('date').read().strip()
    })


# 启动定时任务调度器
news_scheduler.start()

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=Config.DEBUG)
