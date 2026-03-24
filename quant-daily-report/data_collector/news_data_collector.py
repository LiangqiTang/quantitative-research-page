"""
新闻数据采集器
负责采集财经新闻、公告、社交媒体舆情等信息
"""

import requests
from bs4 import BeautifulSoup
import feedparser
from datetime import datetime
from typing import List, Dict, Optional
import re

class NewsDataCollector:
    def __init__(self):
        self.news_sources = {
            'cailianshe': 'https://www.cailianshe.com/live',
            'eastmoney_news': 'https://news.eastmoney.com/',
            'xueqiu': 'https://xueqiu.com/hot'
        }

    def get_latest_news(self, sector: Optional[str] = None, count: int = 20) -> List[Dict]:
        """
        获取最新财经新闻
        :param sector: 行业板块过滤（可选）
        :param count: 返回新闻数量
        :return: 新闻列表，每个元素包含title、content、url、time、source
        """
        news_list = []

        try:
            # 从财联社获取实时新闻
            cailianshe_news = self._get_cailianshe_news(count)
            news_list.extend(cailianshe_news)

            # 从东方财富获取财经新闻
            eastmoney_news = self._get_eastmoney_news(count)
            news_list.extend(eastmoney_news)

            # 按时间排序
            news_list.sort(key=lambda x: x['time'], reverse=True)

            # 行业过滤
            if sector:
                filtered_news = []
                keywords = sector.lower().split() + sector.split()
                for news in news_list:
                    news_text = f"{news['title']} {news['content']}".lower()
                    if any(keyword.lower() in news_text for keyword in keywords):
                        filtered_news.append(news)
                return filtered_news[:count]

            return news_list[:count]

        except Exception as e:
            print(f"获取最新新闻失败: {e}")
            return []

    def get_stock_news(self, symbol: str, count: int = 10) -> List[Dict]:
        """
        获取个股相关新闻
        :param symbol: 股票代码
        :param count: 返回新闻数量
        :return: 新闻列表
        """
        try:
            # 使用东方财富个股新闻接口
            url = f"https://emweb.securities.eastmoney.com/PC_HSF10/News/NewsAjax?code={symbol}"

            response = requests.get(url)
            result = response.json()

            news_list = []
            if result.get('NewsList'):
                for item in result['NewsList'][:count]:
                    news = {
                        'title': item.get('TITLE', ''),
                        'content': item.get('CONTENT', '')[:200] + '...',  # 摘要
                        'url': f"https://emweb.securities.eastmoney.com/PC_HSF10/News/NewsDetail?code={symbol}&id={item.get('ID', '')}",
                        'time': datetime.strptime(item.get('CREATETIME', ''), '%Y-%m-%d %H:%M:%S'),
                        'source': item.get('SOURCE', '东方财富'),
                        'symbol': symbol
                    }
                    news_list.append(news)

            return news_list

        except Exception as e:
            print(f"获取股票{symbol}新闻失败: {e}")
            return []

    def get_announcements(self, symbol: str, count: int = 10) -> List[Dict]:
        """
        获取个股公告
        :param symbol: 股票代码
        :param count: 返回公告数量
        :return: 公告列表
        """
        try:
            # 使用东方财富公告接口
            url = f"https://data.eastmoney.com/notices/stock/{symbol}.html"
            response = requests.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')

            announcements = []
            notice_list = soup.select('.notice-list li')

            for item in notice_list[:count]:
                title_elem = item.select_one('.notice-title a')
                time_elem = item.select_one('.notice-time')

                if title_elem and time_elem:
                    announcement = {
                        'title': title_elem.get('title', ''),
                        'url': f"https://data.eastmoney.com{title_elem.get('href', '')}",
                        'time': datetime.strptime(time_elem.text.strip(), '%Y-%m-%d'),
                        'source': '东方财富公告',
                        'symbol': symbol
                    }
                    announcements.append(announcement)

            return announcements

        except Exception as e:
            print(f"获取股票{symbol}公告失败: {e}")
            return []

    def _get_cailianshe_news(self, count: int = 10) -> List[Dict]:
        """从财联社获取新闻"""
        try:
            url = "https://www.cailianshe.com/live"
            # 临时绕过SSL证书验证（仅用于测试环境）
            import ssl
            ssl._create_default_https_context = ssl._create_unverified_context
            response = requests.get(url, verify=False)
            soup = BeautifulSoup(response.text, 'html.parser')

            news_list = []
            news_items = soup.select('.live-list-item')[:count]

            for item in news_items:
                content_elem = item.select_one('.content')
                time_elem = item.select_one('.time')

                if content_elem and time_elem:
                    title = content_elem.text.strip()
                    news_time = time_elem.text.strip()

                    # 处理时间
                    if ':' in news_time:
                        today = datetime.now().strftime('%Y-%m-%d')
                        news_datetime = datetime.strptime(f"{today} {news_time}", '%Y-%m-%d %H:%M')
                    else:
                        news_datetime = datetime.strptime(news_time, '%Y-%m-%d')

                    news = {
                        'title': title,
                        'content': title,
                        'url': f"https://www.cailianshe.com/live",
                        'time': news_datetime,
                        'source': '财联社'
                    }
                    news_list.append(news)

            return news_list

        except Exception as e:
            print(f"从财联社获取新闻失败: {e}")
            return []

    def _get_eastmoney_news(self, count: int = 10) -> List[Dict]:
        """从东方财富获取新闻"""
        try:
            url = "https://news.eastmoney.com/"
            response = requests.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')

            news_list = []
            news_items = soup.select('.news-item')[:count]

            for item in news_items:
                title_elem = item.select_one('.news-title a')
                desc_elem = item.select_one('.news-desc')
                time_elem = item.select_one('.news-time')

                if title_elem:
                    title = title_elem.get('title', title_elem.text.strip())
                    url = title_elem.get('href', '')
                    content = desc_elem.text.strip() if desc_elem else ''
                    news_time = time_elem.text.strip() if time_elem else ''

                    # 处理时间
                    if news_time:
                        if '分钟前' in news_time or '小时前' in news_time:
                            news_datetime = datetime.now()
                        elif '今天' in news_time:
                            time_str = re.search(r'(\d+:\d+)', news_time)
                            if time_str:
                                news_datetime = datetime.strptime(
                                    f"{datetime.now().strftime('%Y-%m-%d')} {time_str.group(1)}",
                                    '%Y-%m-%d %H:%M'
                                )
                            else:
                                news_datetime = datetime.now()
                        else:
                            try:
                                news_datetime = datetime.strptime(news_time, '%Y-%m-%d %H:%M')
                            except:
                                news_datetime = datetime.now()
                    else:
                        news_datetime = datetime.now()

                    news = {
                        'title': title,
                        'content': content,
                        'url': url if url.startswith('http') else f"https://news.eastmoney.com{url}",
                        'time': news_datetime,
                        'source': '东方财富'
                    }
                    news_list.append(news)

            return news_list

        except Exception as e:
            print(f"从东方财富获取新闻失败: {e}")
            return []

if __name__ == "__main__":
    # 测试代码
    collector = NewsDataCollector()

    print("测试获取最新新闻...")
    latest_news = collector.get_latest_news(count=10)
    for i, news in enumerate(latest_news):
        print(f"{i+1}. [{news['time'].strftime('%H:%M')}] {news['title']} ({news['source']})")

    print("\n测试获取个股新闻...")
    stock_news = collector.get_stock_news('000001', count=5)
    for i, news in enumerate(stock_news):
        print(f"{i+1}. [{news['time'].strftime('%Y-%m-%d %H:%M')}] {news['title']}")

    print("\n测试获取个股公告...")
    announcements = collector.get_announcements('000001', count=5)
    for i, announcement in enumerate(announcements):
        print(f"{i+1}. [{announcement['time'].strftime('%Y-%m-%d')}] {announcement['title']}")