"""
定时任务调度器
负责每天定时推送AI资讯
"""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import sys
import os
import logging

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.config import Config
from utils.dingtalk_utils import DingTalkUtils
from utils.news_utils import NewsUtils

logger = logging.getLogger(__name__)


class NewsScheduler:
    """新闻推送调度器"""
    
    def __init__(self):
        """初始化调度器"""
        self.scheduler = BackgroundScheduler(timezone=Config.TIMEZONE)
        self.dingtalk_utils = DingTalkUtils()
        self.news_utils = NewsUtils(api_key=Config.NEWS_API_KEY)
        self.webhook_url = Config.DINGTALK_WEBHOOK_URL
    
    def push_daily_news(self):
        """推送每日AI资讯"""
        try:
            logger.info("开始推送每日AI资讯")
            
            # 获取资讯内容
            news_content = self.news_utils.get_daily_news(
                use_mock=not Config.NEWS_API_KEY,  # 如果没有API密钥则使用模拟数据
                max_results=5
            )
            
            # 发送到钉钉群
            if self.webhook_url:
                result = self.dingtalk_utils.send_markdown_message(
                    webhook_url=self.webhook_url,
                    title="今日AI资讯速递",
                    text=news_content,
                    is_at_all=False
                )
                
                if result.get('errcode') == 0:
                    logger.info("AI资讯推送成功")
                else:
                    logger.error(f"AI资讯推送失败: {result}")
            else:
                logger.warning("未配置Webhook URL，跳过推送")
        
        except Exception as e:
            logger.error(f"推送每日资讯时出错: {str(e)}", exc_info=True)
    
    def start(self):
        """启动调度器"""
        try:
            # 解析推送时间（格式：HH:MM）
            hour, minute = Config.DAILY_NEWS_TIME.split(':')
            
            # 添加定时任务
            self.scheduler.add_job(
                func=self.push_daily_news,
                trigger=CronTrigger(hour=int(hour), minute=int(minute)),
                id='daily_news_push',
                name='每日AI资讯推送',
                replace_existing=True
            )
            
            logger.info(f"定时任务已配置：每天 {Config.DAILY_NEWS_TIME} 推送AI资讯")
            
            # 启动调度器
            self.scheduler.start()
            logger.info("调度器已启动")
        
        except Exception as e:
            logger.error(f"启动调度器失败: {str(e)}", exc_info=True)
    
    def stop(self):
        """停止调度器"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("调度器已停止")
    
    def trigger_now(self):
        """立即触发一次推送（用于测试）"""
        logger.info("手动触发资讯推送")
        self.push_daily_news()


# 创建全局调度器实例
news_scheduler = NewsScheduler()


if __name__ == '__main__':
    # 测试推送功能
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("测试新闻推送功能...")
    news_scheduler.trigger_now()
    print("推送完成！")
