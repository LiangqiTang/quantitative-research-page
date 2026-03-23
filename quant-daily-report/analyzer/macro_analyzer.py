"""
宏观分析引擎
负责市场情绪分析、板块轮动分析、宏观政策影响分析等
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

class MacroAnalyzer:
    def __init__(self, data: Dict):
        self.data = data

    def analyze_market_sentiment(self) -> Dict:
        """
        市场情绪分析
        返回包含情绪指标、情绪阶段、操作建议的字典
        """
        try:
            # 计算情绪指标
            sentiment_metrics = self._calculate_sentiment_metrics()

            # 判定情绪阶段
            sentiment_stage = self._judge_sentiment_stage(sentiment_metrics)

            # 生成操作建议
            trading_advice = self._generate_trading_advice(sentiment_stage, sentiment_metrics)

            return {
                'metrics': sentiment_metrics,
                'sentiment_stage': sentiment_stage,
                'trading_advice': trading_advice,
                'update_time': datetime.now()
            }

        except Exception as e:
            print(f"市场情绪分析失败: {e}")
            return {}

    def analyze_sector_rotation(self, window_days: int = 60) -> List[Dict]:
        """
        板块轮动分析
        :param window_days: 分析窗口天数
        :return: 包含板块强度、资金流向、轮动趋势的列表
        """
        try:
            # 获取板块数据
            sector_data = self._get_sector_data(window_days)

            # 计算板块强度指标
            sector_strength = []
            for sector in sector_data:
                strength = self._calculate_sector_strength(sector)
                sector_strength.append(strength)

            # 按板块强度排序
            sector_strength.sort(key=lambda x: x['overall_strength'], reverse=True)

            return sector_strength

        except Exception as e:
            print(f"板块轮动分析失败: {e}")
            return []

    def analyze_macro_impact(self) -> Dict:
        """
        宏观政策影响分析
        返回包含宏观事件、影响评估、投资建议的字典
        """
        try:
            # 获取宏观新闻数据
            news_data = self._get_macro_news()

            # 分析宏观新闻的市场影响
            impact_analysis = {
                'positive_events': [],
                'negative_events': [],
                'neutral_events': [],
                'overall_impact': 'neutral',
                'investment_advice': ''
            }

            for news in news_data:
                impact_score = self._calculate_impact_score(news)
                news['impact_score'] = impact_score

                if impact_score > 0.5:
                    impact_analysis['positive_events'].append(news)
                elif impact_score < -0.5:
                    impact_analysis['negative_events'].append(news)
                else:
                    impact_analysis['neutral_events'].append(news)

            # 计算整体影响
            total_score = sum(news['impact_score'] for news in news_data)
            if total_score > 3:
                impact_analysis['overall_impact'] = 'positive'
                impact_analysis['investment_advice'] = '利好市场，可适当增加仓位关注政策受益板块'
            elif total_score < -3:
                impact_analysis['overall_impact'] = 'negative'
                impact_analysis['investment_advice'] = '利空市场，建议控制仓位规避风险'
            else:
                impact_analysis['overall_impact'] = 'neutral'
                impact_analysis['investment_advice'] = '宏观面中性，关注个股基本面'

            return impact_analysis

        except Exception as e:
            print(f"宏观政策影响分析失败: {e}")
            return {}

    def _calculate_sentiment_metrics(self) -> Dict:
        """计算情绪指标"""
        data = self.data

        # 上涨家数占比
        total_stocks = data.get('up_count', 0) + data.get('down_count', 0) + data.get('flat_count', 0)
        up_ratio = data.get('up_count', 0) / total_stocks if total_stocks > 0 else 0

        # 涨跌停比
        limit_up_ratio = data.get('limit_up_count', 0) / max(1, data.get('limit_down_count', 1))

        # 资金流向指标
        north_money = data.get('north_money', 0)
        market_amount = data.get('sh_amount', 0) + data.get('sz_amount', 0)
        north_money_ratio = north_money / market_amount * 100 if market_amount > 0 else 0

        # 量能指标
        current_amount = market_amount
        avg_amount = data.get('avg_market_amount', current_amount)
        volume_ratio = current_amount / avg_amount if avg_amount > 0 else 1

        return {
            'up_ratio': up_ratio,
            'limit_up_ratio': limit_up_ratio,
            'north_money': north_money,
            'north_money_ratio': north_money_ratio,
            'volume_ratio': volume_ratio,
            'market_amount': market_amount,
            'up_count': data.get('up_count', 0),
            'down_count': data.get('down_count', 0),
            'limit_up_count': data.get('limit_up_count', 0),
            'limit_down_count': data.get('limit_down_count', 0)
        }

    def _judge_sentiment_stage(self, metrics: Dict) -> str:
        """
        判断情绪周期阶段
        - 冰点: 极端低迷，物极必反
        - 启动: 情绪开始复苏
        - 分歧: 多空分歧加大
        - 退潮: 情绪开始退潮
        - 震荡: 无明显趋势
        """
        up_ratio = metrics.get('up_ratio', 0)
        limit_up_ratio = metrics.get('limit_up_ratio', 0)
        volume_ratio = metrics.get('volume_ratio', 1)

        # 冰点判断
        if up_ratio < 0.2 and limit_up_ratio < 0.5 and volume_ratio < 0.8:
            return '冰点'

        # 启动判断
        elif up_ratio > 0.7 and limit_up_ratio > 2 and volume_ratio > 1.2:
            return '启动'

        # 分歧判断
        elif abs(up_ratio - 0.5) > 0.3 and abs(volume_ratio - 1) > 0.5:
            return '分歧'

        # 退潮判断
        elif up_ratio < 0.3 and limit_up_ratio < 1 and volume_ratio > 1:
            return '退潮'

        # 震荡判断
        else:
            return '震荡'

    def _generate_trading_advice(self, stage: str, metrics: Dict) -> str:
        """生成操作建议"""
        advice_map = {
            '冰点': {
                'short': '情绪冰点，准备抄底',
                'detail': '市场情绪极度低迷，下跌动能衰竭，建议关注低估值优质标的，分批建仓，控制仓位在30-50%',
                'strategy': '左侧布局，关注超跌绩优股'
            },
            '启动': {
                'short': '情绪启动，积极做多',
                'detail': '市场情绪全面复苏，赚钱效应显现，可增加仓位至70-90%，聚焦主线热点板块龙头股',
                'strategy': '右侧追涨，主线板块龙头'
            },
            '分歧': {
                'short': '情绪分歧，谨慎操作',
                'detail': '市场多空分歧加大，震荡加剧，建议降低仓位至30-50%，快进快出，回避高位股',
                'strategy': '高抛低吸，控制仓位'
            },
            '退潮': {
                'short': '情绪退潮，注意风险',
                'detail': '市场情绪退潮，亏钱效应显现，建议严格控制仓位在20%以下，甚至空仓观望',
                'strategy': '防守为主，空仓观望'
            },
            '震荡': {
                'short': '情绪震荡，灵活操作',
                'detail': '市场情绪震荡，缺乏明确主线，建议仓位控制在50%左右，关注业绩确定性高的个股',
                'strategy': '波段操作，业绩为王'
            }
        }

        return advice_map.get(stage, advice_map['震荡'])

    def _calculate_sector_strength(self, sector_data: Dict) -> Dict:
        """计算板块强度"""
        try:
            # 计算涨幅强度
            price_strength = sector_data.get('pct_chg', 0) * 1.5

            # 计算资金强度
            money_strength = sector_data.get('main_inflow', 0) / sector_data.get('total_amount', 1) * 1000

            # 计算量能强度
            volume_strength = sector_data.get('volume_ratio', 1) * 0.5

            # 计算热度强度
            heat_strength = sector_data.get('stock_count', 0) / 100

            # 综合强度
            overall_strength = (price_strength + money_strength + volume_strength + heat_strength) / 4

            # 趋势判断
            trend = '上升' if price_strength > 0 else '下降'
            if abs(price_strength) < 1:
                trend = '震荡'

            return {
                'sector_name': sector_data.get('name', ''),
                'price_strength': price_strength,
                'money_strength': money_strength,
                'volume_strength': volume_strength,
                'heat_strength': heat_strength,
                'overall_strength': overall_strength,
                'trend': trend,
                'pct_chg': sector_data.get('pct_chg', 0),
                'main_inflow': sector_data.get('main_inflow', 0),
                'update_time': sector_data.get('update_time', datetime.now())
            }

        except Exception as e:
            print(f"板块强度计算失败: {e}")
            return {}

    def _get_sector_data(self, window_days: int) -> List[Dict]:
        """获取板块数据（模拟）"""
        # 这里应该从数据源获取板块数据，暂时返回模拟数据
        sectors = [
            {'name': '半导体', 'pct_chg': 5.2, 'main_inflow': 125000, 'total_amount': 850000, 'volume_ratio': 1.8, 'stock_count': 45},
            {'name': 'AI概念', 'pct_chg': 3.8, 'main_inflow': 98000, 'total_amount': 720000, 'volume_ratio': 1.5, 'stock_count': 68},
            {'name': '新能源汽车', 'pct_chg': -1.2, 'main_inflow': -45000, 'total_amount': 520000, 'volume_ratio': 0.8, 'stock_count': 36},
            {'name': '医药生物', 'pct_chg': 2.5, 'main_inflow': 76000, 'total_amount': 630000, 'volume_ratio': 1.3, 'stock_count': 89},
            {'name': '金融', 'pct_chg': 0.5, 'main_inflow': 12000, 'total_amount': 450000, 'volume_ratio': 0.6, 'stock_count': 24},
        ]
        return sectors

    def _get_macro_news(self) -> List[Dict]:
        """获取宏观新闻数据（模拟）"""
        news = [
            {'title': '央行降准0.5个百分点，释放长期资金约1万亿', 'content': '央行宣布全面降准0.5个百分点，...', 'source': '央行网站', 'time': datetime.now()},
            {'title': '国务院部署进一步稳经济一揽子措施', 'content': '国务院常务会议部署稳经济一揽子措施，...', 'source': '中国政府网', 'time': datetime.now() - timedelta(hours=2)},
            {'title': 'PMI数据公布，经济复苏态势明显', 'content': '5月制造业PMI为51.2%，...', 'source': '国家统计局', 'time': datetime.now() - timedelta(days=1)},
        ]
        return news

    def _calculate_impact_score(self, news: Dict) -> float:
        """计算新闻影响分数"""
        # 简单的关键词匹配评分
        positive_keywords = ['降准', '降息', '放水', '利好', '扶持', '增长', '上升', '超预期']
        negative_keywords = ['加息', '收紧', '利空', '下滑', '下降', '低于预期', '风险']

        score = 0
        text = news['title'] + ' ' + news['content']

        for keyword in positive_keywords:
            if keyword in text:
                score += 1

        for keyword in negative_keywords:
            if keyword in text:
                score -= 1

        return score

if __name__ == "__main__":
    # 测试代码
    data = {
        'up_count': 3215,
        'down_count': 1245,
        'flat_count': 230,
        'limit_up_count': 125,
        'limit_down_count': 15,
        'north_money': 85.2,
        'sh_amount': 4500,
        'sz_amount': 5800,
        'avg_market_amount': 8500
    }

    analyzer = MacroAnalyzer(data)
    sentiment = analyzer.analyze_market_sentiment()
    print("市场情绪分析结果:")
    print(f"情绪阶段: {sentiment['sentiment_stage']}")
    print(f"操作建议: {sentiment['trading_advice']['short']}")
    print(f"详细建议: {sentiment['trading_advice']['detail']}")

    sector_rotation = analyzer.analyze_sector_rotation()
    print("\n板块轮动分析结果:")
    for sector in sector_rotation[:3]:
        print(f"{sector['sector_name']}: 综合强度 {sector['overall_strength']:.2f} ({sector['trend']})")