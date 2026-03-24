"""
股票分析引擎
负责基本面分析、技术面分析、筹码分布分析、主力行为分析等
"""

import pandas as pd
import numpy as np
from scipy import stats
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

class StockAnalyzer:
    def __init__(self, stock_data: Dict):
        self.kline_data = stock_data.get('kline', pd.DataFrame())
        self.financial_data = stock_data.get('financial', {})
        self.basic_info = stock_data.get('basic', {})

    def analyze_fundamentals(self) -> Dict:
        """
        基本面分析
        返回包含估值指标、财务健康、成长能力、盈利质量等分析结果
        """
        try:
            # 估值分析
            valuation = self._analyze_valuation()

            # 财务健康分析
            financial_health = self._analyze_financial_health()

            # 成长能力分析
            growth_ability = self._analyze_growth_ability()

            # 盈利质量分析
            profit_quality = self._analyze_profit_quality()

            # 综合评分
            composite_score = self._calculate_composite_score(
                valuation, financial_health, growth_ability, profit_quality
            )

            return {
                'valuation': valuation,
                'financial_health': financial_health,
                'growth_ability': growth_ability,
                'profit_quality': profit_quality,
                'composite_score': composite_score,
                'investment_rating': self._get_investment_rating(composite_score),
                'update_time': datetime.now()
            }

        except Exception as e:
            print(f"基本面分析失败: {e}")
            return {}

    def analyze_technical(self) -> Dict:
        """
        技术面分析
        返回包含趋势判断、指标信号、形态分析等结果
        """
        try:
            # 趋势分析
            trend_analysis = self._analyze_trend()

            # 指标信号分析
            indicator_signals = self._analyze_indicators()

            # 形态分析
            pattern_analysis = self._analyze_patterns()

            # 支撑阻力分析
            support_resistance = self._analyze_support_resistance()

            # 技术面综合评分
            technical_score = self._calculate_technical_score(
                trend_analysis, indicator_signals, pattern_analysis
            )

            return {
                'trend': trend_analysis,
                'indicators': indicator_signals,
                'patterns': pattern_analysis,
                'support_resistance': support_resistance,
                'technical_score': technical_score,
                'trading_signal': self._get_trading_signal(technical_score, indicator_signals),
                'update_time': datetime.now()
            }

        except Exception as e:
            print(f"技术面分析失败: {e}")
            return {}

    def analyze_chips(self) -> Dict:
        """
        筹码分布分析
        返回包含筹码集中度、成本分布、主力行为等分析结果
        """
        try:
            # 计算筹码集中度
            chip_concentration = self._calculate_chip_concentration()

            # 分析成本分布
            cost_distribution = self._analyze_cost_distribution()

            # 判断主力行为
            mainforce_behavior = self._analyze_mainforce_behavior()

            return {
                'chip_concentration': chip_concentration,
                'cost_distribution': cost_distribution,
                'mainforce_behavior': mainforce_behavior,
                'support_level': cost_distribution.get('avg_cost', 0),
                'resistance_level': cost_distribution.get('high_cost', 0),
                'update_time': datetime.now()
            }

        except Exception as e:
            print(f"筹码分布分析失败: {e}")
            return {}

    def _analyze_valuation(self) -> Dict:
        """估值指标分析"""
        try:
            pe = self.financial_data.get('pe', 0)
            pb = self.financial_data.get('pb', 0)
            ps = self.financial_data.get('ps', 0)
            pcf = self.financial_data.get('pcf', 0)

            # 行业平均估值（模拟数据）
            industry_pe = 25.0
            industry_pb = 3.5

            # 估值评分
            pe_score = max(0, 100 - abs(pe - industry_pe) / industry_pe * 100) if industry_pe > 0 else 50
            pb_score = max(0, 100 - abs(pb - industry_pb) / industry_pb * 100) if industry_pb > 0 else 50

            return {
                'pe': pe,
                'pb': pb,
                'ps': ps,
                'pcf': pcf,
                'industry_pe': industry_pe,
                'industry_pb': industry_pb,
                'pe_score': pe_score,
                'pb_score': pb_score,
                'valuation_conclusion': self._get_valuation_conclusion(pe, pb, industry_pe, industry_pb)
            }

        except Exception as e:
            print(f"估值分析失败: {e}")
            return {}

    def _analyze_financial_health(self) -> Dict:
        """财务健康分析"""
        try:
            debt_ratio = self.financial_data.get('debt_ratio', 0)
            current_ratio = self.financial_data.get('current_ratio', 0)
            quick_ratio = self.financial_data.get('quick_ratio', 0)
            cash_ratio = self.financial_data.get('cash_ratio', 0)

            # 财务健康评分
            debt_score = 100 - debt_ratio if debt_ratio < 100 else 0
            liquidity_score = (current_ratio + quick_ratio + cash_ratio) / 3 * 20

            return {
                'debt_ratio': debt_ratio,
                'current_ratio': current_ratio,
                'quick_ratio': quick_ratio,
                'cash_ratio': cash_ratio,
                'debt_score': debt_score,
                'liquidity_score': liquidity_score,
                'health_conclusion': self._get_health_conclusion(debt_ratio, current_ratio)
            }

        except Exception as e:
            print(f"财务健康分析失败: {e}")
            return {}

    def _analyze_growth_ability(self) -> Dict:
        """成长能力分析"""
        try:
            revenue_growth = self.financial_data.get('revenue_growth', 0)
            profit_growth = self.financial_data.get('profit_growth', 0)
            eps_growth = self.financial_data.get('eps_growth', 0)

            # 成长评分
            growth_score = (revenue_growth + profit_growth + eps_growth) / 3
            growth_score = max(0, min(100, growth_score))

            return {
                'revenue_growth': revenue_growth,
                'profit_growth': profit_growth,
                'eps_growth': eps_growth,
                'growth_score': growth_score,
                'growth_conclusion': self._get_growth_conclusion(growth_score)
            }

        except Exception as e:
            print(f"成长能力分析失败: {e}")
            return {}

    def _analyze_profit_quality(self) -> Dict:
        """盈利质量分析"""
        try:
            roe = self.financial_data.get('roe', 0)
            roa = self.financial_data.get('roa', 0)
            net_margin = self.financial_data.get('net_margin', 0)
            gross_margin = self.financial_data.get('gross_margin', 0)

            # 盈利质量评分
            profit_score = (roe + roa) / 2 * 2 + net_margin
            profit_score = max(0, min(100, profit_score))

            return {
                'roe': roe,
                'roa': roa,
                'net_margin': net_margin,
                'gross_margin': gross_margin,
                'profit_score': profit_score,
                'quality_conclusion': self._get_quality_conclusion(roe, net_margin)
            }

        except Exception as e:
            print(f"盈利质量分析失败: {e}")
            return {}

    def _calculate_composite_score(self, valuation, financial_health, growth_ability, profit_quality) -> float:
        """计算综合评分"""
        try:
            # 权重分配
            weights = {
                'valuation': 0.25,
                'financial_health': 0.25,
                'growth_ability': 0.25,
                'profit_quality': 0.25
            }

            # 计算各部分得分
            valuation_score = (valuation.get('pe_score', 50) + valuation.get('pb_score', 50)) / 2
            financial_score = (financial_health.get('debt_score', 50) + financial_health.get('liquidity_score', 50)) / 2
            growth_score = growth_ability.get('growth_score', 50)
            profit_score = profit_quality.get('profit_score', 50)

            # 综合得分
            composite_score = (
                valuation_score * weights['valuation'] +
                financial_score * weights['financial_health'] +
                growth_score * weights['growth_ability'] +
                profit_score * weights['profit_quality']
            )

            return composite_score

        except Exception as e:
            print(f"综合评分计算失败: {e}")
            return 50.0

    def _calculate_technical_score(self, trend, indicators, patterns) -> float:
        """计算技术面综合评分"""
        try:
            trend_score = trend.get('trend_score', 50)
            indicator_score = sum(sig['score'] for sig in indicators.get('signals', [])) / len(indicators.get('signals', [{'score': 50}]))
            pattern_score = patterns.get('pattern_score', 50)

            technical_score = (trend_score * 0.4 + indicator_score * 0.4 + pattern_score * 0.2)
            return min(100, max(0, technical_score))

        except Exception as e:
            print(f"技术面评分计算失败: {e}")
            return 50.0

    # 辅助方法
    def _get_valuation_conclusion(self, pe, pb, industry_pe, industry_pb):
        """获取估值结论"""
        if pe < industry_pe * 0.7 and pb < industry_pb * 0.7:
            return "低估"
        elif pe > industry_pe * 1.3 or pb > industry_pb * 1.3:
            return "高估"
        else:
            return "合理"

    def _get_health_conclusion(self, debt_ratio, current_ratio):
        """获取财务健康结论"""
        if debt_ratio < 30 and current_ratio > 2:
            return "优秀"
        elif debt_ratio > 70 or current_ratio < 1:
            return "较差"
        else:
            return "良好"

    def _get_growth_conclusion(self, growth_score):
        """获取成长能力结论"""
        if growth_score > 20:
            return "高成长"
        elif growth_score < 5:
            return "低成长"
        else:
            return "稳定成长"

    def _get_quality_conclusion(self, roe, net_margin):
        """获取盈利质量结论"""
        if roe > 15 and net_margin > 10:
            return "高质量"
        elif roe < 5 or net_margin < 3:
            return "低质量"
        else:
            return "中等质量"

    def _get_investment_rating(self, composite_score):
        """获取投资评级"""
        if composite_score >= 80:
            return "买入"
        elif composite_score >= 60:
            return "持有"
        elif composite_score >= 40:
            return "观望"
        else:
            return "卖出"

    def _get_trading_signal(self, technical_score, indicators):
        """获取交易信号"""
        if technical_score >= 70:
            return "买入信号"
        elif technical_score <= 30:
            return "卖出信号"
        else:
            return "观望信号"

    # 技术分析辅助方法（简化实现）
    def _analyze_trend(self):
        """趋势分析"""
        return {
            'trend_direction': '上升',
            'trend_strength': 85,
            'trend_score': 85,
            'trend_conclusion': "多头趋势明显"
        }

    def _analyze_indicators(self):
        """指标信号分析"""
        return {
            'signals': [
                {'indicator': 'MACD', 'signal': '金叉', 'score': 80},
                {'indicator': 'RSI', 'signal': '买入区间', 'score': 75},
                {'indicator': '布林带', 'signal': '中轨支撑', 'score': 70}
            ],
            'bullish_count': 3,
            'bearish_count': 0
        }

    def _analyze_patterns(self):
        """形态分析"""
        return {
            'recognized_patterns': ['W底', '突破形态'],
            'pattern_score': 85,
            'pattern_conclusion': "多头形态确认"
        }

    def _analyze_support_resistance(self):
        """支撑阻力分析"""
        return {
            'support_levels': [25.0, 23.5],
            'resistance_levels': [30.0, 32.5],
            'immediate_support': 25.0,
            'immediate_resistance': 30.0
        }

    def _calculate_chip_concentration(self):
        """计算筹码集中度"""
        return {
            'chip_concentration': 25,
            'concentration_level': '集中',
            'lockup_degree': '高度锁定'
        }

    def _analyze_cost_distribution(self):
        """分析成本分布"""
        return {
            'avg_cost': 27.5,
            'low_cost': 24.0,
            'high_cost': 31.0,
            'cost_range': '24.0-31.0',
            'peak_cost_area': '27-29'
        }

    def _analyze_mainforce_behavior(self):
        """分析主力行为"""
        return {
            'mainforce_direction': '买入',
            'accumulation_degree': '中度控盘',
            'behavior_conclusion': '主力持续建仓'
        }

if __name__ == "__main__":
    # 测试代码
    stock_data = {
        'kline': pd.DataFrame(),
        'financial': {
            'pe': 22.5,
            'pb': 3.2,
            'debt_ratio': 45.0,
            'current_ratio': 1.8,
            'revenue_growth': 18.5,
            'profit_growth': 25.3,
            'roe': 15.2,
            'net_margin': 8.5
        },
        'basic': {}
    }

    analyzer = StockAnalyzer(stock_data)
    fundamental_result = analyzer.analyze_fundamentals()
    print("基本面分析结果:")
    print(f"综合评分: {fundamental_result['composite_score']:.1f}")
    print(f"投资评级: {fundamental_result['investment_rating']}")

    technical_result = analyzer.analyze_technical()
    print("\n技术面分析结果:")
    print(f"技术评分: {technical_result['technical_score']:.1f}")
    print(f"交易信号: {technical_result['trading_signal']}")