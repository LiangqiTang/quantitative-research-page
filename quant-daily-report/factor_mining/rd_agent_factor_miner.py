#!/usr/bin/env python3
"""
基于RD-Agent的因子挖掘引擎
实现因子挖掘、分析和回测功能
"""

import os
import sys
from typing import Dict, List, Optional, Any
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import tempfile
import json

class RDAgentFactorMiner:
    """基于RD-Agent的因子挖掘引擎"""

    def __init__(self, rd_agent_path: str = None):
        """
        初始化因子挖掘引擎
        :param rd_agent_path: RD-Agent的路径
        """
        self.rd_agent_path = rd_agent_path or 'rd_agent'
        self.rd_agent_available = False
        self.factors = []
        self.factor_results = {}

        # 检查RD-Agent是否可用
        self._check_rd_agent_availability()

    def _check_rd_agent_availability(self):
        """检查RD-Agent是否可用"""
        try:
            # 尝试导入RD-Agent相关模块
            import rdagent
            from rdagent import RDAgent
            from rdagent.core import Task
            from rdagent.factors import FactorDiscoverer, FactorValidator

            self.rd_agent_available = True
            self.rdagent = rdagent
            self.RDAgent = RDAgent
            self.Task = Task
            self.FactorDiscoverer = FactorDiscoverer
            self.FactorValidator = FactorValidator

            print("✅ RD-Agent 已安装并可用")
        except ImportError as e:
            print(f"⚠️ RD-Agent 不可用: {e}")
            print("   请先安装RD-Agent: pip install rdagent")
            print("   或者访问: https://github.com/your-org/rdagent 获取安装说明")

    def mine_factors(self, data: Dict, **kwargs) -> List[Dict]:
        """
        使用RD-Agent进行因子挖掘
        :param data: 包含行情、财务等数据的字典
        :return: 挖掘出的因子列表
        """
        if not self.rd_agent_available:
            print("❌ RD-Agent 不可用，无法进行因子挖掘")
            return []

        try:
            print("🔍 开始使用RD-Agent进行因子挖掘...")

            # 准备数据
            factor_data = self._prepare_factor_data(data)

            # 创建因子挖掘任务
            task = self.Task(
                type="factor_discovery",
                data=factor_data,
                parameters={
                    "min_significance": kwargs.get("min_significance", 0.05),
                    "max_factors": kwargs.get("max_factors", 20),
                    "factor_types": kwargs.get("factor_types", ["price", "volume", "volatility", "fundamental"]),
                    "time_window": kwargs.get("time_window", 60),
                    **kwargs.get("rd_agent_params", {})
                }
            )

            # 初始化因子发现器
            discoverer = self.FactorDiscoverer()

            # 运行因子挖掘
            print("⏳ 正在挖掘因子，这可能需要几分钟...")
            self.factors = discoverer.discover(task)

            print(f"✅ 因子挖掘完成，共发现{len(self.factors)}个因子")

            # 验证因子有效性
            validated_factors = self._validate_factors(data)

            return validated_factors

        except Exception as e:
            print(f"❌ 因子挖掘失败: {e}")
            return []

    def _prepare_factor_data(self, data: Dict) -> Dict:
        """
        准备因子挖掘所需的数据格式
        :param data: 原始数据
        :return: 格式化后的因子数据
        """
        try:
            factor_data = {
                "price_data": {},
                "financial_data": {},
                "technical_data": {},
                "metadata": {
                    "start_date": data.get("start_date"),
                    "end_date": data.get("end_date"),
                    "symbols": data.get("symbols", []),
                    "frequency": "daily"
                }
            }

            # 处理行情数据
            if data.get("price_data") is not None:
                factor_data["price_data"] = data["price_data"].to_dict(orient="records")

            # 处理财务数据
            if data.get("financial_data") is not None:
                factor_data["financial_data"] = data["financial_data"].to_dict(orient="records")

            # 处理技术指标数据
            if data.get("technical_data") is not None:
                factor_data["technical_data"] = data["technical_data"].to_dict(orient="records")

            return factor_data

        except Exception as e:
            print(f"❌ 数据准备失败: {e}")
            return {}

    def _validate_factors(self, data: Dict) -> List[Dict]:
        """
        验证因子的有效性
        :param data: 原始数据
        :return: 验证后的因子列表
        """
        if not self.rd_agent_available or not self.factors:
            return self.factors

        try:
            print("📊 开始验证因子有效性...")

            # 初始化因子验证器
            validator = self.FactorValidator()

            # 准备验证数据
            validation_data = self._prepare_validation_data(data)

            # 运行验证
            validated_factors = validator.validate(
                factors=self.factors,
                data=validation_data,
                metrics=["ic", "icir", "sharpe_ratio", "max_drawdown"]
            )

            # 分析验证结果
            self._analyze_validation_results(validated_factors)

            return validated_factors

        except Exception as e:
            print(f"❌ 因子验证失败: {e}")
            return self.factors

    def _prepare_validation_data(self, data: Dict) -> Dict:
        """
        准备因子验证所需的数据
        :param data: 原始数据
        :return: 验证数据
        """
        try:
            # 这里需要根据RD-Agent的要求准备验证数据
            validation_data = {
                "returns": self._calculate_returns(data.get("price_data")),
                "factors": {},
                "metadata": data.get("metadata", {})
            }

            return validation_data

        except Exception as e:
            print(f"❌ 验证数据准备失败: {e}")
            return {}

    def _calculate_returns(self, price_data: pd.DataFrame) -> pd.DataFrame:
        """
        计算收益率数据
        :param price_data: 行情数据
        :return: 收益率数据
        """
        if price_data is None:
            return pd.DataFrame()

        try:
            # 计算日收益率
            returns = price_data['close'].pct_change().dropna()
            returns.name = "return"
            return returns.to_frame()

        except Exception as e:
            print(f"❌ 收益率计算失败: {e}")
            return pd.DataFrame()

    def _analyze_validation_results(self, validated_factors: List[Dict]):
        """
        分析因子验证结果
        :param validated_factors: 验证后的因子列表
        """
        try:
            print("\n📈 因子验证结果分析:")
            print("=" * 60)

            # 按IC值排序
            top_factors = sorted(
                validated_factors,
                key=lambda x: x.get("ic", {}).get("value", 0),
                reverse=True
            )

            # 显示前5个因子
            for i, factor in enumerate(top_factors[:5]):
                factor_name = factor.get("name", f"因子{i+1}")
                ic_value = factor.get("ic", {}).get("value", 0)
                icir_value = factor.get("icir", {}).get("value", 0)
                sharpe_ratio = factor.get("sharpe_ratio", {}).get("value", 0)

                print(f"\n{i+1}. {factor_name}")
                print(f"   📊 IC值: {ic_value:.4f}")
                print(f"   🚀 ICIR: {icir_value:.4f}")
                print(f"   💎 夏普比率: {sharpe_ratio:.4f}")

                # 评估因子质量
                if abs(ic_value) > 0.2:
                    print("   ✅ 因子质量优秀")
                elif abs(ic_value) > 0.1:
                    print("   👍 因子质量良好")
                else:
                    print("   ⚠️  因子质量一般")

            # 保存验证结果
            self.factor_results = {
                "validated_factors": validated_factors,
                "top_factors": top_factors[:5],
                "total_validated": len(validated_factors),
                "analysis_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }

        except Exception as e:
            print(f"❌ 验证结果分析失败: {e}")

    def backtest_factors(self, data: Dict, factors: List[Dict] = None) -> Dict:
        """
        回测因子表现
        :param data: 回测数据
        :param factors: 要回测的因子列表，默认使用所有挖掘出的因子
        :return: 回测结果
        """
        if not self.rd_agent_available:
            print("❌ RD-Agent 不可用，无法进行因子回测")
            return {}

        try:
            factors_to_backtest = factors or self.factors
            if not factors_to_backtest:
                print("⚠️ 没有可用的因子进行回测")
                return {}

            print(f"⏳ 开始回测{len(factors_to_backtest)}个因子...")

            # 准备回测数据
            backtest_data = self._prepare_backtest_data(data)

            # 使用RD-Agent进行因子回测
            from rdagent.backtest import FactorBacktester

            backtester = FactorBacktester()
            results = backtester.run(
                factors=factors_to_backtest,
                data=backtest_data,
                strategy="long_short",
                initial_capital=1000000,
                commission=0.0003
            )

            print("✅ 因子回测完成")

            # 分析回测结果
            analysis_results = self._analyze_backtest_results(results)

            return {
                "raw_results": results,
                "analysis": analysis_results
            }

        except Exception as e:
            print(f"❌ 因子回测失败: {e}")
            return {}

    def _prepare_backtest_data(self, data: Dict) -> Dict:
        """
        准备因子回测所需的数据
        :param data: 原始数据
        :return: 回测数据
        """
        try:
            backtest_data = {
                "price_data": data.get("price_data", pd.DataFrame()),
                "factor_data": {},
                "metadata": {
                    "start_date": data.get("start_date"),
                    "end_date": data.get("end_date"),
                    "symbols": data.get("symbols", [])
                }
            }

            return backtest_data

        except Exception as e:
            print(f"❌ 回测数据准备失败: {e}")
            return {}

    def _analyze_backtest_results(self, backtest_results: Dict) -> Dict:
        """
        分析因子回测结果
        :param backtest_results: 原始回测结果
        :return: 分析后的结果
        """
        try:
            analysis = {
                "factor_performance": [],
                "summary": {},
                "top_performers": []
            }

            # 计算每个因子的绩效指标
            for factor_name, result in backtest_results.items():
                performance = {
                    "factor_name": factor_name,
                    "total_return": result.get("total_return", 0),
                    "annual_return": result.get("annual_return", 0),
                    "sharpe_ratio": result.get("sharpe_ratio", 0),
                    "max_drawdown": result.get("max_drawdown", 0),
                    "win_rate": result.get("win_rate", 0),
                    "ic": result.get("information_coefficient", 0)
                }

                analysis["factor_performance"].append(performance)

            # 计算整体汇总指标
            if analysis["factor_performance"]:
                returns = [p["annual_return"] for p in analysis["factor_performance"]]
                sharpe_ratios = [p["sharpe_ratio"] for p in analysis["factor_performance"]]
                max_drawdowns = [p["max_drawdown"] for p in analysis["factor_performance"]]

                analysis["summary"] = {
                    "avg_annual_return": np.mean(returns),
                    "median_annual_return": np.median(returns),
                    "avg_sharpe_ratio": np.mean(sharpe_ratios),
                    "avg_max_drawdown": np.mean(max_drawdowns),
                    "top_5_average": np.mean(sorted(returns, reverse=True)[:5])
                }

                # 找出表现最好的因子
                analysis["top_performers"] = sorted(
                    analysis["factor_performance"],
                    key=lambda x: x["sharpe_ratio"],
                    reverse=True
                )[:3]

            return analysis

        except Exception as e:
            print(f"❌ 回测结果分析失败: {e}")
            return {}

    def generate_factor_report(self, output_dir: str = "output") -> str:
        """
        生成因子挖掘报告
        :param output_dir: 输出目录
        :return: 报告路径
        """
        try:
            if not self.factor_results:
                print("⚠️ 没有因子结果可以生成报告")
                return ""

            # 创建输出目录
            os.makedirs(output_dir, exist_ok=True)
            report_path = os.path.join(output_dir, "factor_mining_report.md")

            # 生成报告内容
            report_content = self._generate_report_content()

            # 保存报告
            with open(report_path, "w", encoding="utf-8") as f:
                f.write(report_content)

            print(f"✅ 因子挖掘报告已保存到: {report_path}")
            return report_path

        except Exception as e:
            print(f"❌ 报告生成失败: {e}")
            return ""

    def _generate_report_content(self) -> str:
        """
        生成报告内容
        :return: 报告内容
        """
        try:
            report = f"""# 🧬 因子挖掘报告

## 📋 报告摘要

- **报告生成时间**: {datetime.now().strftime("%Y年%m月%d日 %H:%M:%S")}
- **挖掘因子总数**: {len(self.factor_results.get("validated_factors", []))}
- **优质因子数量**: {sum(1 for f in self.factor_results.get("validated_factors", [])
                     if abs(f.get("ic", {}).get("value", 0)) > 0.1)}

## 📊 因子质量统计

| 指标 | 数值 |
|------|------|
| 平均IC值 | {np.mean([f.get("ic", {}).get("value", 0) for f in self.factor_results.get("validated_factors", [])]):.4f} |
| 平均ICIR | {np.mean([f.get("icir", {}).get("value", 0) for f in self.factor_results.get("validated_factors", [])]):.4f} |
| 平均夏普比率 | {np.mean([f.get("sharpe_ratio", {}).get("value", 0) for f in self.factor_results.get("validated_factors", [])]):.4f} |

## 🏆 最佳因子表现

"""

            # 添加最佳因子表现
            for i, factor in enumerate(self.factor_results.get("top_factors", [])):
                factor_name = factor.get("name", f"因子{i+1}")
                ic_value = factor.get("ic", {}).get("value", 0)
                icir_value = factor.get("icir", {}).get("value", 0)
                sharpe_ratio = factor.get("sharpe_ratio", {}).get("value", 0)
                description = factor.get("description", "无描述")

                report += f"""
### {i+1}. {factor_name}

- **IC值**: {ic_value:.4f} ({"正相关" if ic_value > 0 else "负相关"})
- **ICIR**: {icir_value:.4f}
- **夏普比率**: {sharpe_ratio:.4f}
- **因子描述**: {description}

"""

            # 添加回测结果分析
            if "analysis" in self.factor_results:
                analysis = self.factor_results["analysis"]
                report += f"""
## 📈 因子回测分析

### 整体表现统计

| 指标 | 数值 |
|------|------|
| 平均年化收益率 | {analysis.get("summary", {}).get("avg_annual_return", 0):.2%} |
| 中位数年化收益率 | {analysis.get("summary", {}).get("median_annual_return", 0):.2%} |
| 平均夏普比率 | {analysis.get("summary", {}).get("avg_sharpe_ratio", 0):.2f} |
| 最大回撤均值 | {analysis.get("summary", {}).get("avg_max_drawdown", 0):.2%} |

"""

            # 免责声明
            report += """
## ⚠️ 免责声明

本报告中的因子挖掘结果仅用于研究和学习目的，不构成任何投资建议。因子表现基于历史数据，未来表现可能存在差异。

在实际投资应用前，请务必进行充分的回测和风险评估。
"""

            return report

        except Exception as e:
            print(f"❌ 报告内容生成失败: {e}")
            return ""

    def export_factors(self, output_path: str) -> bool:
        """
        导出因子定义
        :param output_path: 输出路径
        :return: 是否成功
        """
        try:
            if not self.factors:
                print("⚠️ 没有因子可以导出")
                return False

            # 准备导出数据
            export_data = {
                "factors": self.factors,
                "factor_results": self.factor_results,
                "export_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "rd_agent_version": getattr(self.rdagent, '__version__', 'unknown')
            }

            # 保存到文件
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)

            print(f"✅ 因子已成功导出到: {output_path}")
            return True

        except Exception as e:
            print(f"❌ 因子导出失败: {e}")
            return False

if __name__ == "__main__":
    # 测试代码
    miner = RDAgentFactorMiner()

    # 模拟数据
    mock_data = {
        'start_date': '2023-01-01',
        'end_date': '2023-12-31',
        'symbols': ['000001', '600036', '600519']
    }

    # 测试因子挖掘
    factors = miner.mine_factors(mock_data)
    print(f"挖掘出{len(factors)}个因子")

    # 测试报告生成
    if factors:
        report_path = miner.generate_factor_report()
        if report_path:
            print(f"报告已生成: {report_path}")

    # 测试因子回测
    backtest_result = miner.backtest_factors(mock_data, factors)
    if backtest_result:
        print(f"回测完成，结果包含{len(backtest_result.get('factor_performance', []))}个因子的表现")
