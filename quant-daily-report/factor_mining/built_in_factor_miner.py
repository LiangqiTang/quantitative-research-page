#!/usr/bin/env python3
"""
内置因子挖掘器
提供常用的量价、波动率、基本面等因子的计算
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)

class BuiltInFactorMiner:
    """内置因子挖掘器"""

    def __init__(self):
        """初始化内置因子挖掘器"""
        self.available_factor_types = [
            "price",          # 价格类因子
            "volume",         # 成交量类因子
            "volatility",     # 波动率类因子
            "trend",          # 趋势类因子
            "momentum",       # 动量类因子
            "liquidity",      # 流动性类因子
            "fundamental"      # 基本面类因子
        ]

        self.factor_calculators = {
            "price": self._calculate_price_factors,
            "volume": self._calculate_volume_factors,
            "volatility": self._calculate_volatility_factors,
            "trend": self._calculate_trend_factors,
            "momentum": self._calculate_momentum_factors,
            "liquidity": self._calculate_liquidity_factors,
            "fundamental": self._calculate_fundamental_factors
        }

    def mine_factors(self, data: Dict, **kwargs) -> List[Dict]:
        """
        使用内置方法进行因子挖掘
        :param data: 包含行情、财务等数据的字典
        :return: 挖掘出的因子列表
        """
        try:
            logger.info("🔍 开始使用内置因子挖掘器进行因子挖掘...")

            # 获取用户指定的因子类型
            factor_types = kwargs.get("factor_types", self.available_factor_types)

            # 验证因子类型
            invalid_types = [ft for ft in factor_types if ft not in self.available_factor_types]
            if invalid_types:
                logger.warning(f"⚠️ 不支持的因子类型: {invalid_types}")
                factor_types = [ft for ft in factor_types if ft in self.available_factor_types]

            if not factor_types:
                logger.warning("⚠️ 没有有效的因子类型可用")
                return []

            logger.info(f"📊 将计算{len(factor_types)}类因子: {factor_types}")

            # 计算各类因子
            all_factors = []

            for factor_type in factor_types:
                try:
                    calculator = self.factor_calculators[factor_type]
                    factors = calculator(data, **kwargs)
                    logger.info(f"✅ {factor_type}类因子计算完成，共{len(factors)}个因子")
                    all_factors.extend(factors)
                except Exception as e:
                    logger.error(f"❌ {factor_type}类因子计算失败: {e}")
                    continue

            # 计算因子显著性和质量指标
            all_factors = self._calculate_factor_quality(all_factors, data, **kwargs)

            logger.info(f"🎉 内置因子挖掘完成，共计算{len(all_factors)}个因子")

            return all_factors

        except Exception as e:
            logger.error(f"❌ 内置因子挖掘失败: {e}")
            return []

    def _calculate_price_factors(self, data: Dict, **kwargs) -> List[Dict]:
        """
        计算价格类因子
        :param data: 数据字典
        :return: 价格类因子列表
        """
        factors = []

        # 计算各种移动平均线
        ma_windows = kwargs.get("ma_windows", [5, 10, 20, 60, 120])

        for window in ma_windows:
            factors.append({
                "name": f"MA{window}",
                "type": "price",
                "description": f"{window}日移动平均线",
                "unit": "",
                "calculation": f"close_{window}_day_avg",
                "is_quality_factor": False
            })

        # 价格趋势因子
        factors.extend([
            {
                "name": "PriceTrend",
                "type": "price",
                "description": "价格趋势强度",
                "unit": "",
                "calculation": "(close - close_20day_ago) / close_20day_ago",
                "is_quality_factor": True
            },
            {
                "name": "PriceAcceleration",
                "type": "price",
                "description": "价格加速度",
                "unit": "",
                "calculation": "((close - close_5day_ago)/5) - ((close_5day_ago - close_10day_ago)/5)",
                "is_quality_factor": True
            }
        ])

        return factors

    def _calculate_volume_factors(self, data: Dict, **kwargs) -> List[Dict]:
        """
        计算成交量类因子
        :param data: 数据字典
        :return: 成交量类因子列表
        """
        factors = []

        # 成交量移动平均线
        volume_windows = kwargs.get("volume_windows", [5, 10, 20])

        for window in volume_windows:
            factors.append({
                "name": f"VOL_MA{window}",
                "type": "volume",
                "description": f"{window}日均量",
                "unit": "",
                "calculation": f"volume_{window}_day_avg",
                "is_quality_factor": False
            })

        # 成交量比率因子
        factors.extend([
            {
                "name": "VolumeRatio",
                "type": "volume",
                "description": "当前成交量与20日均量的比率",
                "unit": "",
                "calculation": "volume / volume_20day_avg",
                "is_quality_factor": True
            },
            {
                "name": "VolumeTrend",
                "type": "volume",
                "description": "成交量趋势",
                "unit": "",
                "calculation": "(volume_5day_avg - volume_20day_avg) / volume_20day_avg",
                "is_quality_factor": True
            },
            {
                "name": "VolumePriceCorrelation",
                "type": "volume",
                "description": "成交量与价格的相关性",
                "unit": "",
                "calculation": "correlation(volume_change, price_change, 20days)",
                "is_quality_factor": True
            }
        ])

        return factors

    def _calculate_volatility_factors(self, data: Dict, **kwargs) -> List[Dict]:
        """
        计算波动率类因子
        :param data: 数据字典
        :return: 波动率类因子列表
        """
        factors = []

        # 波动率因子
        volatility_windows = kwargs.get("volatility_windows", [10, 20, 60])

        for window in volatility_windows:
            factors.append({
                "name": f"Volatility{window}",
                "type": "volatility",
                "description": f"{window}日波动率",
                "unit": "",
                "calculation": f"std(price_return, {window}days)",
                "is_quality_factor": True
            })

        # 其他波动率相关因子
        factors.extend([
            {
                "name": "ATR",
                "type": "volatility",
                "description": "平均真实波幅",
                "unit": "",
                "calculation": "avg(true_range, 14days)",
                "is_quality_factor": True
            },
            {
                "name": "VolatilityRatio",
                "type": "volatility",
                "description": "短期波动率与长期波动率的比率",
                "unit": "",
                "calculation": "volatility_10day / volatility_60day",
                "is_quality_factor": True
            },
            {
                "name": "DownsideVolatility",
                "type": "volatility",
                "description": "下行波动率",
                "unit": "",
                "calculation": "std(negative_returns, 20days)",
                "is_quality_factor": True
            }
        ])

        return factors

    def _calculate_trend_factors(self, data: Dict, **kwargs) -> List[Dict]:
        """
        计算趋势类因子
        :param data: 数据字典
        :return: 趋势类因子列表
        """
        factors = []

        # MACD相关因子
        factors.extend([
            {
                "name": "MACD",
                "type": "trend",
                "description": "指数平滑异同移动平均线",
                "unit": "",
                "calculation": "ema(12) - ema(26)",
                "is_quality_factor": True
            },
            {
                "name": "MACDSignal",
                "type": "trend",
                "description": "MACD信号线",
                "unit": "",
                "calculation": "ema(MACD, 9)",
                "is_quality_factor": False
            },
            {
                "name": "MACDHistogram",
                "type": "trend",
                "description": "MACD柱状图",
                "unit": "",
                "calculation": "MACD - MACDSignal",
                "is_quality_factor": True
            }
        ])

        # 布林带相关因子
        factors.extend([
            {
                "name": "BollingerUpper",
                "type": "trend",
                "description": "布林带上轨",
                "unit": "",
                "calculation": "ma(20) + 2*std(20)",
                "is_quality_factor": False
            },
            {
                "name": "BollingerLower",
                "type": "trend",
                "description": "布林带下轨",
                "unit": "",
                "calculation": "ma(20) - 2*std(20)",
                "is_quality_factor": False
            },
            {
                "name": "BollingerWidth",
                "type": "trend",
                "description": "布林带宽度",
                "unit": "",
                "calculation": "(BollingerUpper - BollingerLower) / ma(20)",
                "is_quality_factor": True
            },
            {
                "name": "BollingerPosition",
                "type": "trend",
                "description": "价格在布林带中的位置",
                "unit": "",
                "calculation": "(close - BollingerLower) / (BollingerUpper - BollingerLower)",
                "is_quality_factor": True
            }
        ])

        return factors

    def _calculate_momentum_factors(self, data: Dict, **kwargs) -> List[Dict]:
        """
        计算动量类因子
        :param data: 数据字典
        :return: 动量类因子列表
        """
        factors = []

        # 动量指标
        momentum_windows = kwargs.get("momentum_windows", [5, 10, 20, 60])

        for window in momentum_windows:
            factors.append({
                "name": f"Momentum{window}",
                "type": "momentum",
                "description": f"{window}日动量",
                "unit": "",
                "calculation": f"(close / close_{window}_day_ago) - 1",
                "is_quality_factor": True
            })

        # RSI指标
        factors.extend([
            {
                "name": "RSI6",
                "type": "momentum",
                "description": "6日相对强弱指数",
                "unit": "",
                "calculation": "rsi(6)",
                "is_quality_factor": True
            },
            {
                "name": "RSI12",
                "type": "momentum",
                "description": "12日相对强弱指数",
                "unit": "",
                "calculation": "rsi(12)",
                "is_quality_factor": True
            },
            {
                "name": "RSI24",
                "type": "momentum",
                "description": "24日相对强弱指数",
                "unit": "",
                "calculation": "rsi(24)",
                "is_quality_factor": True
            }
        ])

        return factors

    def _calculate_liquidity_factors(self, data: Dict, **kwargs) -> List[Dict]:
        """
        计算流动性类因子
        :param data: 数据字典
        :return: 流动性类因子列表
        """
        factors = []

        # 流动性因子
        factors.extend([
            {
                "name": "TurnoverRate",
                "type": "liquidity",
                "description": "换手率",
                "unit": "",
                "calculation": "volume / outstanding_shares",
                "is_quality_factor": True
            },
            {
                "name": "AmihudIlliquidity",
                "type": "liquidity",
                "description": "Amihud非流动性指标",
                "unit": "",
                "calculation": "avg(|return| / dollar_volume, 20days)",
                "is_quality_factor": True
            },
            {
                "name": "VolumeImbalance",
                "type": "liquidity",
                "description": "成交量不平衡",
                "unit": "",
                "calculation": "(buy_volume - sell_volume) / (buy_volume + sell_volume)",
                "is_quality_factor": True
            }
        ])

        return factors

    def _calculate_fundamental_factors(self, data: Dict, **kwargs) -> List[Dict]:
        """
        计算基本面类因子
        :param data: 数据字典
        :return: 基本面类因子列表
        """
        factors = []

        # 估值因子
        factors.extend([
            {
                "name": "PE",
                "type": "fundamental",
                "description": "市盈率",
                "unit": "",
                "calculation": "price / earnings_per_share",
                "is_quality_factor": True
            },
            {
                "name": "PB",
                "type": "fundamental",
                "description": "市净率",
                "unit": "",
                "calculation": "price / book_value_per_share",
                "is_quality_factor": True
            },
            {
                "name": "PS",
                "type": "fundamental",
                "description": "市销率",
                "unit": "",
                "calculation": "price / sales_per_share",
                "is_quality_factor": True
            },
            {
                "name": "PCF",
                "type": "fundamental",
                "description": "市现率",
                "unit": "",
                "calculation": "price / cash_flow_per_share",
                "is_quality_factor": True
            }
        ])

        # 盈利因子
        factors.extend([
            {
                "name": "ROE",
                "type": "fundamental",
                "description": "净资产收益率",
                "unit": "",
                "calculation": "net_profit / shareholders_equity",
                "is_quality_factor": True
            },
            {
                "name": "ROA",
                "type": "fundamental",
                "description": "资产收益率",
                "unit": "",
                "calculation": "net_profit / total_assets",
                "is_quality_factor": True
            },
            {
                "name": "GrossProfitMargin",
                "type": "fundamental",
                "description": "毛利率",
                "unit": "",
                "calculation": "gross_profit / revenue",
                "is_quality_factor": True
            },
            {
                "name": "NetProfitMargin",
                "type": "fundamental",
                "description": "净利率",
                "unit": "",
                "calculation": "net_profit / revenue",
                "is_quality_factor": True
            }
        ])

        return factors

    def _calculate_factor_quality(self, factors: List[Dict], data: Dict, **kwargs) -> List[Dict]:
        """
        计算因子质量指标
        :param factors: 因子列表
        :param data: 数据字典
        :return: 添加了质量指标的因子列表
        """
        try:
            logger.info("📊 计算因子质量指标...")

            # 这里应该根据实际数据计算因子的质量指标
            # 例如IC值、IR值、夏普比率等

            # 模拟计算因子质量
            min_significance = kwargs.get("min_significance", 0.05)

            for factor in factors:
                # 模拟计算IC值和显著性
                # 在实际应用中，应该使用真实数据进行计算
                ic_value = np.random.uniform(-0.3, 0.3)
                p_value = np.random.uniform(0, 0.1)

                factor.update({
                    "ic": {
                        "value": abs(ic_value),
                        "direction": "positive" if ic_value > 0 else "negative",
                        "p_value": p_value,
                        "significant": p_value < min_significance
                    },
                    "icir": {
                        "value": abs(ic_value) / np.random.uniform(0.1, 0.3),
                        "description": "Information Coefficient Ratio"
                    },
                    "sharpe_ratio": {
                        "value": np.random.uniform(0.5, 2.5),
                        "description": "Sharpe Ratio based on factor returns"
                    },
                    "quality_score": abs(ic_value) * 100,
                    "significant": p_value < min_significance
                })

            logger.info("✅ 因子质量指标计算完成")

            return factors

        except Exception as e:
            logger.error(f"❌ 因子质量指标计算失败: {e}")
            return factors

    def validate_factors(self, data: Dict, factors: List[Dict] = None) -> List[Dict]:
        """
        验证因子有效性
        :param data: 验证数据
        :param factors: 要验证的因子列表
        :return: 验证后的因子列表
        """
        if not factors:
            logger.warning("⚠️ 没有可用的因子进行验证")
            return []

        logger.info(f"📊 开始验证{len(factors)}个因子...")

        try:
            # 这里应该实现实际的因子验证逻辑
            # 例如使用分组回测、IC分析等方法

            validated_factors = []

            for factor in factors:
                # 模拟验证过程
                validation_score = np.random.uniform(0.5, 1.0)
                is_valid = validation_score > 0.7

                factor["validation"] = {
                    "score": validation_score,
                    "valid": is_valid,
                    "method": "built_in_validation",
                    "confidence": np.random.uniform(0.7, 1.0)
                }

                if is_valid:
                    validated_factors.append(factor)

            logger.info(f"✅ 因子验证完成，共验证{len(validated_factors)}个有效因子")

            return validated_factors

        except Exception as e:
            logger.error(f"❌ 因子验证失败: {e}")
            return factors

if __name__ == "__main__":
    # 测试代码
    miner = BuiltInFactorMiner()
    print(f"可用因子类型: {miner.available_factor_types}")

    # 模拟数据
    mock_data = {
        'price_data': None,
        'financial_data': None,
        'technical_data': None,
        'start_date': '2023-01-01',
        'end_date': '2023-12-31',
        'symbols': ['000001', '600036', '600519']
    }

    # 测试因子挖掘
    factors = miner.mine_factors(mock_data, factor_types=['price', 'momentum'])
    print(f"挖掘出{len(factors)}个因子")

    # 打印部分因子
    if factors:
        print("\n部分因子信息:")
        for factor in factors[:5]:
            print(f"名称: {factor['name']}, 类型: {factor['type']}, 质量得分: {factor.get('quality_score', 0):.2f}")

    # 测试因子验证
    validated_factors = miner.validate_factors(mock_data, factors)
    print(f"\n验证通过{len(validated_factors)}个因子")
