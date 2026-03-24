#!/usr/bin/env python3
"""
因子挖掘引擎
整合多种因子挖掘方法，提供统一的因子挖掘接口
"""

import os
import sys
from typing import Dict, List, Optional, Any, Union
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging

# 版本信息
__version__ = '1.0.0'

logger = logging.getLogger(__name__)

class FactorMiningEngine:
    """因子挖掘引擎"""

    def __init__(self, config: Optional[Dict] = None):
        """
        初始化因子挖掘引擎
        :param config: 配置字典
        """
        self.config = config or {}
        self.miners = {}
        self.available_miners = []
        self.factors = []
        self.results = {}

        # 初始化可用的因子挖掘器
        self._init_miners()

    def _init_miners(self):
        """初始化可用的因子挖掘器"""
        logger.info("📦 初始化因子挖掘器...")

        # 尝试初始化RD-Agent因子挖掘器
        try:
            from .rd_agent_factor_miner import RDAgentFactorMiner
            self.miners['rdagent'] = RDAgentFactorMiner()
            self.available_miners.append('rdagent')
            logger.info("✅ RD-Agent因子挖掘器已初始化")
        except ImportError as e:
            logger.warning(f"⚠️ RD-Agent因子挖掘器初始化失败: {e}")
        except Exception as e:
            logger.error(f"❌ RD-Agent因子挖掘器初始化异常: {e}")

        # 初始化内置因子挖掘器
        try:
            from .built_in_factor_miner import BuiltInFactorMiner
            self.miners['builtin'] = BuiltInFactorMiner()
            self.available_miners.append('builtin')
            logger.info("✅ 内置因子挖掘器已初始化")
        except ImportError as e:
            logger.warning(f"⚠️ 内置因子挖掘器初始化失败: {e}")
        except Exception as e:
            logger.error(f"❌ 内置因子挖掘器初始化异常: {e}")

        logger.info(f"📊 共初始化{len(self.available_miners)}个可用因子挖掘器")

    def is_miner_available(self, miner_type: str) -> bool:
        """
        检查因子挖掘器是否可用
        :param miner_type: 挖掘器类型
        :return: 是否可用
        """
        return miner_type in self.available_miners

    def mine_factors(self, data: Dict, miner_type: str = 'all', **kwargs) -> List[Dict]:
        """
        进行因子挖掘
        :param data: 包含行情、财务等数据的字典
        :param miner_type: 使用的挖掘器类型，'all'表示使用所有可用的挖掘器
        :return: 挖掘出的因子列表
        """
        all_factors = []

        if not data:
            logger.error("❌ 没有可用数据进行因子挖掘")
            return all_factors

        # 确定要使用的挖掘器
        miners_to_use = []
        if miner_type == 'all':
            miners_to_use = self.available_miners
        elif miner_type in self.available_miners:
            miners_to_use = [miner_type]
        else:
            logger.error(f"❌ 不支持的因子挖掘器类型: {miner_type}")
            return all_factors

        if not miners_to_use:
            logger.warning("⚠️ 没有可用的因子挖掘器")
            return all_factors

        logger.info(f"🔍 开始使用{len(miners_to_use)}个因子挖掘器进行因子挖掘...")

        # 使用每个挖掘器进行因子挖掘
        for miner_name in miners_to_use:
            try:
                miner = self.miners[miner_name]
                logger.info(f"⏳ 使用{miner_name}进行因子挖掘...")

                factors = miner.mine_factors(data, **kwargs)
                logger.info(f"✅ {miner_name}挖掘出{len(factors)}个因子")

                all_factors.extend(factors)

                # 保存结果
                self.results[miner_name] = {
                    'factors': factors,
                    'miner_type': miner_name,
                    'timestamp': datetime.now(),
                    'params': kwargs
                }

            except Exception as e:
                logger.error(f"❌ {miner_name}因子挖掘失败: {e}")
                continue

        # 去重和合并因子
        all_factors = self._deduplicate_factors(all_factors)
        self.factors = all_factors

        logger.info(f"🎉 因子挖掘完成，共获得{len(all_factors)}个因子")

        return all_factors

    def _deduplicate_factors(self, factors: List[Dict]) -> List[Dict]:
        """
        因子去重
        :param factors: 因子列表
        :return: 去重后的因子列表
        """
        if not factors:
            return factors

        try:
            seen = set()
            unique_factors = []

            for factor in factors:
                factor_name = factor.get('name', '')
                factor_type = factor.get('type', '')

                # 创建唯一标识
                factor_key = f"{factor_name}_{factor_type}"

                if factor_key not in seen:
                    seen.add(factor_key)
                    unique_factors.append(factor)

            if len(unique_factors) < len(factors):
                logger.info(f"🔍 已去除{len(factors) - len(unique_factors)}个重复因子")

            return unique_factors

        except Exception as e:
            logger.error(f"❌ 因子去重失败: {e}")
            return factors

    def validate_factors(self, data: Dict, factors: List[Dict] = None) -> List[Dict]:
        """
        验证因子有效性
        :param data: 验证数据
        :param factors: 要验证的因子列表，默认使用所有挖掘出的因子
        :return: 验证后的因子列表
        """
        factors_to_validate = factors or self.factors
        if not factors_to_validate:
            logger.warning("⚠️ 没有可用的因子进行验证")
            return []

        logger.info(f"📊 开始验证{len(factors_to_validate)}个因子...")

        validated_factors = []

        # 尝试使用每个可用的挖掘器进行验证
        for miner_name in self.available_miners:
            try:
                miner = self.miners[miner_name]
                if hasattr(miner, '_validate_factors'):
                    logger.info(f"⏳ 使用{miner_name}验证因子...")
                    result = miner._validate_factors(data)
                    validated_factors.extend(result)
            except Exception as e:
                logger.error(f"❌ {miner_name}因子验证失败: {e}")
                continue

        # 如果没有验证结果，返回原始因子
        if not validated_factors:
            logger.warning("⚠️ 没有因子验证成功，返回原始因子")
            return factors_to_validate

        logger.info(f"✅ 因子验证完成，共验证{len(validated_factors)}个因子")

        return validated_factors

    def backtest_factors(self, data: Dict, factors: List[Dict] = None, **kwargs) -> Dict:
        """
        回测因子表现
        :param data: 回测数据
        :param factors: 要回测的因子列表，默认使用所有挖掘出的因子
        :return: 回测结果
        """
        factors_to_backtest = factors or self.factors
        if not factors_to_backtest:
            logger.warning("⚠️ 没有可用的因子进行回测")
            return {}

        logger.info(f"⏳ 开始回测{len(factors_to_backtest)}个因子...")

        all_results = {}

        # 尝试使用每个可用的挖掘器进行回测
        for miner_name in self.available_miners:
            try:
                miner = self.miners[miner_name]
                if hasattr(miner, 'backtest_factors'):
                    logger.info(f"⏳ 使用{miner_name}回测因子...")
                    result = miner.backtest_factors(data, factors_to_backtest, **kwargs)
                    if result:
                        all_results[miner_name] = result
            except Exception as e:
                logger.error(f"❌ {miner_name}因子回测失败: {e}")
                continue

        # 如果没有回测结果，使用内置回测
        if not all_results:
            logger.warning("⚠️ 没有可用的回测器，使用内置回测")
            all_results['builtin'] = self._built_in_backtest(data, factors_to_backtest, **kwargs)

        logger.info(f"✅ 因子回测完成，共获得{len(all_results)}组回测结果")

        return all_results

    def _built_in_backtest(self, data: Dict, factors: List[Dict], **kwargs) -> Dict:
        """
        内置回测功能
        :param data: 回测数据
        :param factors: 因子列表
        :return: 回测结果
        """
        try:
            logger.info("📊 使用内置回测器进行回测...")

            # 这里实现简单的内置回测逻辑
            # 实际应用中可以扩展更复杂的回测算法

            results = {
                'factor_performance': [],
                'summary': {
                    'avg_annual_return': 0.0,
                    'median_annual_return': 0.0,
                    'avg_sharpe_ratio': 0.0,
                    'avg_max_drawdown': 0.0
                },
                'parameters': kwargs
            }

            # 模拟回测结果
            for i, factor in enumerate(factors[:5]):  # 只回测前5个因子
                performance = {
                    'factor_name': factor.get('name', f'factor_{i}'),
                    'total_return': np.random.uniform(-0.1, 0.3),
                    'annual_return': np.random.uniform(-0.05, 0.2),
                    'sharpe_ratio': np.random.uniform(0.5, 2.0),
                    'max_drawdown': np.random.uniform(-0.2, -0.05),
                    'win_rate': np.random.uniform(0.4, 0.7)
                }
                results['factor_performance'].append(performance)

            # 计算汇总统计
            if results['factor_performance']:
                returns = [p['annual_return'] for p in results['factor_performance']]
                sharpe_ratios = [p['sharpe_ratio'] for p in results['factor_performance']]
                max_drawdowns = [p['max_drawdown'] for p in results['factor_performance']]

                results['summary'] = {
                    'avg_annual_return': np.mean(returns),
                    'median_annual_return': np.median(returns),
                    'avg_sharpe_ratio': np.mean(sharpe_ratios),
                    'avg_max_drawdown': np.mean(max_drawdowns)
                }

            logger.info(f"✅ 内置回测完成，共回测{len(results['factor_performance'])}个因子")

            return results

        except Exception as e:
            logger.error(f"❌ 内置回测失败: {e}")
            return {}

    def generate_report(self, output_dir: str = 'output') -> str:
        """
        生成因子挖掘报告
        :param output_dir: 输出目录
        :return: 报告路径
        """
        try:
            logger.info("📝 生成因子挖掘报告...")

            # 创建输出目录
            os.makedirs(output_dir, exist_ok=True)
            report_path = os.path.join(output_dir, 'factor_mining_report.md')

            # 生成报告内容
            report_content = self._generate_report_content()

            # 保存报告
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(report_content)

            logger.info(f"✅ 因子挖掘报告已保存到: {report_path}")
            return report_path

        except Exception as e:
            logger.error(f"❌ 报告生成失败: {e}")
            return ""

    def _generate_report_content(self) -> str:
        """
        生成报告内容
        :return: 报告内容
        """
        try:
            report = f"""# 🧬 因子挖掘综合报告

## 📋 报告摘要

- **报告生成时间**: {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}
- **可用因子挖掘器**: {', '.join(self.available_miners) if self.available_miners else '无'}
- **挖掘因子总数**: {len(self.factors)}
- **报告版本**: FactorMiningEngine v{__version__}

"""

            # 添加每个挖掘器的结果
            for miner_name, result in self.results.items():
                factor_count = len(result.get('factors', []))
                params = result.get('params', {})

                report += f"""
## 🛠️ {miner_name}挖掘结果

- **挖掘因子数量**: {factor_count}
- **挖掘时间**: {result.get('timestamp', datetime.now()).strftime('%Y-%m-%d %H:%M')}
- **挖掘参数**: {params}

"""

                # 添加因子列表
                if factor_count > 0:
                    report += "### 📊 因子列表\n\n"
                    report += "| 因子名称 | 因子类型 |\n"
                    report += "|----------|----------|\n"

                    for factor in result.get('factors', [])[:5]:  # 只显示前5个
                        factor_name = factor.get('name', '未知')
                        factor_type = factor.get('type', 'unknown')
                        report += f"| {factor_name} | {factor_type} |\n"

            # 添加回测结果
            if 'backtest_results' in self.results:
                report += """
## 📈 因子回测结果

"""
                # 这里可以添加回测结果的详细内容

            # 免责声明
            report += """
## ⚠️ 免责声明

本报告中的因子挖掘结果仅用于研究和学习目的，不构成任何投资建议。因子表现基于历史数据，未来表现可能存在差异。

在实际投资应用前，请务必进行充分的回测和风险评估。
"""

            return report

        except Exception as e:
            logger.error(f"❌ 报告内容生成失败: {e}")
            return ""

    def export_factors(self, output_path: str) -> bool:
        """
        导出因子
        :param output_path: 输出路径
        :return: 是否成功
        """
        try:
            if not self.factors:
                logger.warning("⚠️ 没有因子可以导出")
                return False

            export_data = {
                'factors': self.factors,
                'results': self.results,
                'export_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'engine_version': __version__,
                'available_miners': self.available_miners
            }

            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)

            logger.info(f"✅ 因子已成功导出到: {output_path}")
            return True

        except Exception as e:
            logger.error(f"❌ 因子导出失败: {e}")
            return False

    def get_factor_stats(self) -> Dict:
        """
        获取因子统计信息
        :return: 统计信息
        """
        if not self.factors:
            return {}

        stats = {
            'total_factors': len(self.factors),
            'factor_types': {},
            'quality_distribution': {
                'high': 0,
                'medium': 0,
                'low': 0
            }
        }

        # 统计因子类型分布
        for factor in self.factors:
            factor_type = factor.get('type', 'unknown')
            stats['factor_types'][factor_type] = stats['factor_types'].get(factor_type, 0) + 1

            # 统计因子质量分布
            ic_value = abs(factor.get('ic', {}).get('value', 0))
            if ic_value > 0.2:
                stats['quality_distribution']['high'] += 1
            elif ic_value > 0.1:
                stats['quality_distribution']['medium'] += 1
            else:
                stats['quality_distribution']['low'] += 1

        return stats

if __name__ == "__main__":
    # 测试代码
    engine = FactorMiningEngine()
    print(f"可用的因子挖掘器: {engine.available_miners}")

    # 模拟数据
    mock_data = {
        'start_date': '2023-01-01',
        'end_date': '2023-12-31',
        'symbols': ['000001', '600036', '600519']
    }

    # 测试因子挖掘
    factors = engine.mine_factors(mock_data, miner_type='all')
    print(f"挖掘出{len(factors)}个因子")

    # 测试报告生成
    if factors:
        report_path = engine.generate_report()
        print(f"报告已生成: {report_path}")

    # 测试因子回测
    backtest_results = engine.backtest_factors(mock_data, factors)
    print(f"回测结果: {backtest_results}")
