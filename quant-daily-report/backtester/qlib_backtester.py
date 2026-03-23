"""
基于Qlib的回测引擎
实现基于Qlib的量化策略回测功能
"""

import qlib
from qlib.constant import REG_CN
from qlib.data import D
from qlib.data.dataset import DatasetH
from qlib.contrib.data.handler import Alpha158
from qlib.contrib.strategy import TopkDropoutStrategy
from qlib.backtest import BacktestConf, create_backtest
from qlib.contrib.model import LSTM
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any
from datetime import datetime
import tempfile
import os

class QlibBacktestEngine:
    """基于Qlib的回测引擎"""

    def __init__(self, data_path: str = './qlib_data'):
        """
        初始化Qlib回测引擎
        :param data_path: Qlib数据存储路径
        """
        self.data_path = data_path
        self.qlib_initialized = False
        self.strategy = None
        self.model = None
        self.backtest_config = None

    def initialize_qlib(self, force_reinit: bool = False):
        """
        初始化Qlib
        :param force_reinit: 是否强制重新初始化
        """
        if self.qlib_initialized and not force_reinit:
            return

        try:
            # 初始化Qlib
            qlib.init(
                provider_uri=self.data_path,
                region=REG_CN,
                auto_mount=False
            )
            self.qlib_initialized = True
            print("✅ Qlib初始化成功")
        except Exception as e:
            print(f"❌ Qlib初始化失败: {e}")
            raise

    def fetch_data(self, symbols: List[str], start_date: str, end_date: str,
                   features: List[str] = None) -> Dict:
        """
        获取回测所需数据
        :param symbols: 股票代码列表
        :param start_date: 开始日期
        :param end_date: 结束日期
        :param features: 需要的特征列表
        :return: 包含数据的字典
        """
        try:
            self.initialize_qlib()

            # 获取行情数据
            df = D.history(
                symbols,
                fields=['$open', '$high', '$low', '$close', '$volume'],
                start_time=start_date,
                end_time=end_date,
                freq='day'
            )

            # 获取财务数据
            finance_df = D.history(
                symbols,
                fields=['$pe', '$pb', '$eps', '$revenue', '$profit'],
                start_time=start_date,
                end_time=end_date,
                freq='day'
            )

            # 获取技术指标
            tech_df = D.history(
                symbols,
                fields=['$ma5', '$ma20', '$ma60', '$macd', '$rsi', '$boll'],
                start_time=start_date,
                end_time=end_date,
                freq='day'
            )

            return {
                'price_data': df,
                'financial_data': finance_df,
                'technical_data': tech_df,
                'start_date': start_date,
                'end_date': end_date,
                'symbols': symbols
            }

        except Exception as e:
            print(f"❌ 获取数据失败: {e}")
            raise

    def build_dataset(self, data: Dict, handler_config: Dict = None) -> DatasetH:
        """
        构建Qlib数据集
        :param data: 原始数据
        :param handler_config: 数据处理配置
        :return: Qlib数据集
        """
        try:
            self.initialize_qlib()

            # 默认配置
            if handler_config is None:
                handler_config = {
                    "start_time": data['start_date'],
                    "end_time": data['end_date'],
                    "fit_start_time": data['start_date'],
                    "fit_end_time": data['end_date'],
                    "instruments": data['symbols'],
                }

            # 创建数据处理对象
            handler = Alpha158(**handler_config)

            # 创建数据集
            dataset = DatasetH(handler)

            return dataset

        except Exception as e:
            print(f"❌ 构建数据集失败: {e}")
            raise

    def create_strategy(self, strategy_type: str = 'topk',
                       strategy_config: Dict = None) -> Any:
        """
        创建回测策略
        :param strategy_type: 策略类型
        :param strategy_config: 策略配置
        :return: Qlib策略对象
        """
        try:
            self.initialize_qlib()

            if strategy_config is None:
                strategy_config = {}

            # 根据策略类型创建策略
            if strategy_type == 'topk':
                # 配置TopK策略
                topk = strategy_config.get('topk', 50)
                n_drop = strategy_config.get('n_drop', 20)
                self.strategy = TopkDropoutStrategy(
                    topk=topk,
                    n_drop=n_drop,
                    **strategy_config
                )

            elif strategy_type == 'custom':
                # 自定义策略
                self.strategy = strategy_config.get('strategy_class')(**strategy_config.get('params', {}))

            else:
                raise ValueError(f"不支持的策略类型: {strategy_type}")

            return self.strategy

        except Exception as e:
            print(f"❌ 创建策略失败: {e}")
            raise

    def create_model(self, model_type: str = 'lstm', model_config: Dict = None) -> Any:
        """
        创建预测模型
        :param model_type: 模型类型
        :param model_config: 模型配置
        :return: Qlib模型对象
        """
        try:
            self.initialize_qlib()

            if model_config is None:
                model_config = {}

            # 根据模型类型创建模型
            if model_type == 'lstm':
                self.model = LSTM(**model_config)
            elif model_type == 'xgboost':
                from qlib.contrib.model import XGBModel
                self.model = XGBModel(**model_config)
            elif model_type == 'linear':
                from qlib.contrib.model import LinearModel
                self.model = LinearModel(**model_config)
            elif model_type == 'custom':
                self.model = model_config.get('model_class')(**model_config.get('params', {}))
            else:
                raise ValueError(f"不支持的模型类型: {model_type}")

            return self.model

        except Exception as e:
            print(f"❌ 创建模型失败: {e}")
            raise

    def run_backtest(self, data: Dict, strategy: Any = None,
                    model: Any = None, backtest_config: Dict = None) -> Dict:
        """
        运行回测
        :param data: 回测数据
        :param strategy: 策略对象
        :param model: 模型对象
        :param backtest_config: 回测配置
        :return: 回测结果
        """
        try:
            self.initialize_qlib()

            # 使用默认策略和模型
            if strategy is None:
                strategy = self.create_strategy()
            if model is None:
                model = self.create_model()

            # 构建数据集
            dataset = self.build_dataset(data)

            # 训练模型
            print("🔧 开始训练模型...")
            model.fit(dataset)

            # 生成预测结果
            print("🔮 生成预测结果...")
            preds = model.predict(dataset)

            # 运行回测
            print("⏳ 开始回测...")
            backtest_result = self._run_qlib_backtest(
                preds, strategy, data, backtest_config
            )

            # 分析结果
            print("📊 分析回测结果...")
            analysis_result = self._analyze_backtest_result(backtest_result)

            return {
                'backtest_result': backtest_result,
                'analysis_result': analysis_result,
                'predictions': preds,
                'model': model,
                'strategy': strategy
            }

        except Exception as e:
            print(f"❌ 回测失败: {e}")
            raise

    def _run_qlib_backtest(self, predictions: pd.DataFrame, strategy: Any,
                           data: Dict, backtest_config: Dict = None) -> Any:
        """
        运行Qlib回测
        :param predictions: 预测结果
        :param strategy: 策略对象
        :param data: 回测数据
        :param backtest_config: 回测配置
        :return: 回测结果
        """
        try:
            # 默认回测配置
            if backtest_config is None:
                backtest_config = {
                    'start_time': data['start_date'],
                    'end_time': data['end_date'],
                    'account': 10000000,
                    'benchmark': 'SH000300',
                    'deal_price': 'close',
                    'open_cost': 0.0005,
                    'close_cost': 0.0015,
                    'min_cost': 5,
                }

            # 创建回测配置
            bt_conf = BacktestConf(
                strategy=strategy,
                **backtest_config
            )

            # 运行回测
            backtest = create_backtest(
                bt_conf,
                dataset=None,
                executor=None
            )

            # 传入预测结果并运行回测
            result = backtest.execute(predictions)

            return result

        except Exception as e:
            print(f"❌ 运行Qlib回测失败: {e}")
            raise

    def _analyze_backtest_result(self, backtest_result: Any) -> Dict:
        """
        分析回测结果
        :param backtest_result: Qlib回测结果
        :return: 分析结果
        """
        try:
            # 获取回测统计指标
            statistics = backtest_result.get_stat()

            # 提取关键指标
            analysis = {
                'total_return': statistics['total_return'],
                'annual_return': statistics['annualized_return'],
                'max_drawdown': statistics['max_drawdown'],
                'sharpe_ratio': statistics['sharpe_ratio'],
                'volatility': statistics['volatility'],
                'win_rate': statistics['win_rate'],
                'profit_loss_ratio': statistics['profit_loss_ratio'],
                'turnover': statistics['turnover'],
                'alpha': statistics.get('alpha', 0),
                'beta': statistics.get('beta', 0)
            }

            # 计算额外指标
            analysis['information_ratio'] = analysis.get('total_return', 0) / analysis.get('volatility', 1)
            analysis['calmar_ratio'] = analysis.get('annual_return', 0) / abs(analysis.get('max_drawdown', 1))

            # 提取每日收益
            daily_returns = backtest_result.get_portfolio_return()
            analysis['daily_returns'] = daily_returns

            # 提取持仓记录
            positions = backtest_result.get_positions()
            analysis['positions'] = positions

            return analysis

        except Exception as e:
            print(f"❌ 分析回测结果失败: {e}")
            raise

    def optimize_parameters(self, data: Dict, param_grid: Dict,
                          strategy_type: str = 'topk') -> Dict:
        """
        参数优化
        :param data: 回测数据
        :param param_grid: 参数网格
        :param strategy_type: 策略类型
        :return: 优化结果
        """
        try:
            best_score = -float('inf')
            best_params = None
            best_result = None

            # 生成所有参数组合
            param_combinations = self._generate_param_combinations(param_grid)

            print(f"🔍 开始参数优化，共{len(param_combinations)}种参数组合")

            for i, params in enumerate(param_combinations):
                print(f"\n⏳ 测试第{i+1}/{len(param_combinations)}组参数: {params}")

                try:
                    # 创建策略
                    strategy = self.create_strategy(strategy_type, params)

                    # 运行回测
                    result = self.run_backtest(data, strategy=strategy)

                    # 评估结果
                    score = self._evaluate_result(result['analysis_result'])

                    print(f"📊 策略评分: {score:.4f}")

                    # 更新最优参数
                    if score > best_score:
                        best_score = score
                        best_params = params
                        best_result = result
                        print(f"✨ 发现更优参数，评分提升至{best_score:.4f}")

                except Exception as e:
                    print(f"❌ 测试参数{params}失败: {e}")
                    continue

            if best_result is None:
                raise Exception("所有参数组合测试都失败")

            return {
                'best_params': best_params,
                'best_score': best_score,
                'best_result': best_result,
                'all_results': param_combinations
            }

        except Exception as e:
            print(f"❌ 参数优化失败: {e}")
            raise

    def _generate_param_combinations(self, param_grid: Dict) -> List[Dict]:
        """
        生成参数组合
        :param param_grid: 参数网格
        :return: 参数组合列表
        """
        from itertools import product

        # 获取参数名称和取值
        param_names = list(param_grid.keys())
        param_values = list(param_grid.values())

        # 生成所有组合
        combinations = []
        for values in product(*param_values):
            combination = dict(zip(param_names, values))
            combinations.append(combination)

        return combinations

    def _evaluate_result(self, analysis_result: Dict) -> float:
        """
        评估回测结果
        :param analysis_result: 分析结果
        :return: 评分
        """
        # 多指标综合评分
        weights = {
            'sharpe_ratio': 0.3,
            'max_drawdown': 0.2,
            'annual_return': 0.3,
            'win_rate': 0.1,
            'information_ratio': 0.1
        }

        # 归一化处理
        normalized_scores = {
            'sharpe_ratio': max(0, analysis_result.get('sharpe_ratio', 0) / 5),
            'max_drawdown': max(0, 1 + analysis_result.get('max_drawdown', 0) / 0.5),
            'annual_return': max(0, analysis_result.get('annual_return', 0) / 0.5),
            'win_rate': max(0, analysis_result.get('win_rate', 0) / 1),
            'information_ratio': max(0, analysis_result.get('information_ratio', 0) / 2)
        }

        # 计算综合评分
        score = sum(
            normalized_scores[metric] * weights[metric]
            for metric in weights
        )

        return score

    def generate_report(self, backtest_result: Dict, symbol: str = '') -> str:
        """
        生成回测报告
        :param backtest_result: 回测结果
        :param symbol: 股票代码
        :return: 文本报告
        """
        analysis_result = backtest_result['analysis_result']

        report = f"""📊 Qlib量化策略回测报告

📈 回测概览
开始日期: {backtest_result.get('start_date', '')}
结束日期: {backtest_result.get('end_date', '')}
初始资金: ¥10,000,000

📊 核心指标
| 指标 | 数值 | 说明 |
|------|------|------|
| 总收益率 | {analysis_result.get('total_return', 0):.2%} | 回测期间总收益 |
| 年化收益率 | {analysis_result.get('annual_return', 0):.2%} | 年化收益水平 |
| 最大回撤 | {analysis_result.get('max_drawdown', 0):.2%} | 最大亏损幅度 |
| 夏普比率 | {analysis_result.get('sharpe_ratio', 0):.4f} | 风险调整后收益 |
| 波动率 | {analysis_result.get('volatility', 0):.2%} | 收益波动水平 |
| 胜率 | {analysis_result.get('win_rate', 0):.2%} | 盈利交易占比 |
| 盈亏比 | {analysis_result.get('profit_loss_ratio', 0):.2f} | 盈利/亏损幅度 |
| 信息比率 | {analysis_result.get('information_ratio', 0):.4f} | 相对于基准的超额收益 |
| Calmar比率 | {analysis_result.get('calmar_ratio', 0):.4f} | 收益/最大回撤比 |

🎯 策略评估
"""

        # 策略评估
        sharpe_ratio = analysis_result.get('sharpe_ratio', 0)
        max_drawdown = analysis_result.get('max_drawdown', 0)
        annual_return = analysis_result.get('annual_return', 0)

        if sharpe_ratio > 1.5:
            report += "✅ 夏普比率优秀，策略风险调整后收益出色\n"
        elif sharpe_ratio > 1.0:
            report += "👍 夏普比率良好，策略风险调整后收益较好\n"
        else:
            report += "⚠️ 夏普比率一般，策略风险调整后收益有待提升\n"

        if max_drawdown > -0.2:
            report += "✅ 最大回撤控制良好，风险较低\n"
        elif max_drawdown > -0.3:
            report += "👍 最大回撤控制一般，风险适中\n"
        else:
            report += "⚠️ 最大回撤较大，风险较高\n"

        if annual_return > 0.2:
            report += "✅ 年化收益率优秀，盈利能力强\n"
        elif annual_return > 0.1:
            report += "👍 年化收益率良好，盈利能力较好\n"
        else:
            report += "⚠️ 年化收益率一般，盈利能力有待提升\n"

        report += """
💡 投资建议
"""

        if sharpe_ratio > 1.5 and max_drawdown > -0.2 and annual_return > 0.2:
            report += "✅ 策略表现优秀，建议考虑实盘应用\n"
        elif sharpe_ratio > 1.0 and max_drawdown > -0.3 and annual_return > 0.1:
            report += "👍 策略表现良好，建议进一步优化后考虑实盘\n"
        else:
            report += "⚠️ 策略表现一般，建议进行参数优化或策略改进\n"

        report += f"\n📅 报告生成时间: {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}\n"

        return report

if __name__ == "__main__":
    # 测试代码
    backtester = QlibBacktestEngine()

    # 初始化Qlib
    backtester.initialize_qlib()

    # 获取数据
    data = backtester.fetch_data(
        symbols=['000001', '600036', '600519', '002415', '300750'],
        start_date='2021-01-01',
        end_date='2022-12-31'
    )

    print(f"📊 获取到{len(data['price_data'])}条行情数据")
    print(f"💰 获取到{len(data['financial_data'])}条财务数据")
    print(f"📈 获取到{len(data['technical_data'])}条技术指标数据")

    # 运行回测
    result = backtester.run_backtest(data)

    # 生成报告
    report = backtester.generate_report(result)
    print(report)

    # 保存报告
    with open('qlib_backtest_report.txt', 'w', encoding='utf-8') as f:
        f.write(report)
    print("\n📝 回测报告已保存到qlib_backtest_report.txt")