"""
新闻资讯工具
从各种来源获取AI相关资讯
"""
import requests
from typing import List, Dict, Any
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class NewsUtils:
    """新闻工具类"""
    
    def __init__(self, api_key: str = ""):
        """
        初始化新闻工具
        
        Args:
            api_key: NewsAPI密钥（可选）
        """
        self.api_key = api_key
        self.newsapi_url = "https://newsapi.org/v2/everything"
    
    def get_ai_news_from_newsapi(self, max_results: int = 5) -> List[Dict[str, Any]]:
        """
        从NewsAPI获取AI相关新闻
        
        Args:
            max_results: 最大结果数
            
        Returns:
            list: 新闻列表
        """
        if not self.api_key:
            logger.warning("未配置NewsAPI密钥")
            return []
        
        try:
            # 计算昨天的日期
            yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
            
            params = {
                'apiKey': self.api_key,
                'q': 'artificial intelligence OR machine learning OR deep learning OR AI',
                'language': 'en',
                'sortBy': 'publishedAt',
                'from': yesterday,
                'pageSize': max_results
            }
            
            response = requests.get(self.newsapi_url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            articles = data.get('articles', [])
            
            # 格式化新闻
            news_list = []
            for article in articles:
                news_list.append({
                    'title': article.get('title', ''),
                    'description': article.get('description', ''),
                    'url': article.get('url', ''),
                    'source': article.get('source', {}).get('name', ''),
                    'published_at': article.get('publishedAt', ''),
                    'image_url': article.get('urlToImage', '')
                })
            
            return news_list
        
        except Exception as e:
            logger.error(f"从NewsAPI获取新闻失败: {str(e)}")
            return []
    
    def get_ai_news_mock(self) -> List[Dict[str, Any]]:
        """
        获取模拟AI新闻（用于演示）
        
        Returns:
            list: 新闻列表
        """
        today = datetime.now().strftime('%Y-%m-%d')
        
        return [
            {
                'title': 'OpenAI发布GPT-5：多模态能力大幅提升',
                'description': 'OpenAI今日正式发布GPT-5模型，在图像理解、视频生成和代码编写等方面展现出革命性的进步。新模型支持更长的上下文窗口，推理能力显著增强。',
                'url': 'https://openai.com',
                'source': 'TechCrunch',
                'published_at': today,
                'image_url': ''
            },
            {
                'title': '谷歌Gemini 2.0在多项基准测试中超越竞争对手',
                'description': '谷歌最新发布的Gemini 2.0模型在MMLU、HumanEval等多项基准测试中取得领先成绩，特别是在数学推理和科学问题解答方面表现突出。',
                'url': 'https://deepmind.google',
                'source': 'The Verge',
                'published_at': today,
                'image_url': ''
            },
            {
                'title': 'Meta开源Llama 4：参数规模达到5000亿',
                'description': 'Meta宣布开源Llama 4系列模型，最大版本参数量达到5000亿，支持128种语言。这是迄今为止最大的开源语言模型。',
                'url': 'https://ai.meta.com',
                'source': 'VentureBeat',
                'published_at': today,
                'image_url': ''
            },
            {
                'title': '自动驾驶技术突破：特斯拉FSD V13实现城市完全自动驾驶',
                'description': '特斯拉最新的FSD V13版本在城市道路测试中实现零接管，标志着L4级自动驾驶技术的重大突破。',
                'url': 'https://tesla.com',
                'source': 'Reuters',
                'published_at': today,
                'image_url': ''
            },
            {
                'title': 'AI芯片市场竞争加剧：英伟达、AMD和英特尔三足鼎立',
                'description': '随着AI需求爆发，英伟达H200、AMD MI300和英特尔Gaudi 3在数据中心市场展开激烈竞争，推动AI算力成本持续下降。',
                'url': 'https://nvidia.com',
                'source': 'Bloomberg',
                'published_at': today,
                'image_url': ''
            }
        ]
    
    def format_news_as_markdown(self, news_list: List[Dict[str, Any]]) -> str:
        """
        将新闻列表格式化为Markdown
        
        Args:
            news_list: 新闻列表
            
        Returns:
            str: Markdown格式的新闻内容
        """
        if not news_list:
            return "暂无最新AI资讯"
        
        markdown = "# 🤖 今日AI资讯速递\n\n"
        markdown += f"📅 {datetime.now().strftime('%Y年%m月%d日')} 星期{['一','二','三','四','五','六','日'][datetime.now().weekday()]}\n\n"
        markdown += "---\n\n"
        
        for i, news in enumerate(news_list, 1):
            markdown += f"## {i}. {news['title']}\n\n"
            
            if news.get('description'):
                markdown += f"{news['description']}\n\n"
            
            markdown += f"**来源**: {news.get('source', '未知')}\n\n"
            
            if news.get('url'):
                markdown += f"**链接**: [查看详情]({news['url']})\n\n"
            
            markdown += "---\n\n"
        
        markdown += "\n💡 *由AI助手自动推送，祝您工作愉快！*"
        
        return markdown
    
    def get_daily_news(self, use_mock: bool = False, max_results: int = 5) -> str:
        """
        获取每日AI资讯（Markdown格式）
        
        Args:
            use_mock: 是否使用模拟数据
            max_results: 最大结果数
            
        Returns:
            str: Markdown格式的资讯内容
        """
        if use_mock or not self.api_key:
            news_list = self.get_ai_news_mock()
        else:
            news_list = self.get_ai_news_from_newsapi(max_results)
            # 如果API获取失败，使用模拟数据
            if not news_list:
                logger.info("API获取失败，使用模拟数据")
                news_list = self.get_ai_news_mock()
        
        return self.format_news_as_markdown(news_list)
