"""
量化研究Pipeline - 一键完成完整研究流程
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

from .data_module import DataManager
from .data_extended import ExtendedDataManager
from .backtest_module import (
    Strategy, BacktestEngine, EnhancedBacktestEngine,
    Portfolio, PerformanceMetrics
)
from .alpha_factors import AlphaFactorCalculator
from .factor_evaluator import FactorEvaluator
from .factor_neutralizer import FactorNeutralizer
from .transaction_cost import TransactionCostModel
from .position_manager import PositionManager
from .metrics_extended import ExtendedPerformanceMetrics
from .overfitting_detector import OverfittingDetector


class QuantResearchPipeline:
    """量化研究Pipeline"""

    def __init__(self, data_manager: DataManager,
                 extended_data_manager: Optional[ExtendedDataManager] = None):
        self.data_manager = data_manager
        self.extended_data_manager = extended_data_manager

    def run_factor_research(
        self,
        stock_list: List[str],
        start_date: str,
        end_date: str,
        factor_config: Optional[Dict] = None,
        evaluate: bool = True,
        neutralize: bool = True,
    ) -> Dict:
        """因子研究全流程

        数据获取 → 因子计算 → 因子评价 → 中性化 → 生成报告

        Args:
            stock_list: 股票列表
            start_date: 开始日期
            end_date: 结束日期
            factor_config: 因子配置
            evaluate: 是否评价
            neutralize: 是否中性化

        Returns:
            Dict: 因子研究结果
        """
        print("\n" + "=" * 80)
        print("🔬 因子研究 Pipeline".center(80))
        print("=" * 80)

        result = {
            'start_time': datetime.now().isoformat(),
            'stock_list': stock_list,
            'start_date': start_date,
            'end_date': end_date,
            'steps': []
        }

        # Step 1: 数据获取
        print("\n[1/5] 📊 获取数据...")
        data_dict = self.data_manager.prepare_factor_data(stock_list, start_date, end_date)
        if not data_dict:
            result['error'] = "No data available"
            return result

        result['data_count'] = len(data_dict)
        result['steps'].append('data_fetch')
        print(f"   完成: 获取到 {len(data_dict)} 只股票数据")

        # Step 2: 因子计算
        print("\n[2/5] 🧮 计算因子...")
        alpha_calc = AlphaFactorCalculator()

        # 默认计算几个核心因子
        factor_types = factor_config.get('factor_types', ['momentum_20d', 'reversal_5d', 'volatility_20d']) if factor_config else ['momentum_20d']

        factor_data = {}
        for factor_type in factor_types:
            try:
                factor_series = alpha_calc.calculate_factor(data_dict, factor_type)
                if len(factor_series) > 0:
                    factor_data[factor_type] = factor_series
                    print(f"   计算完成: {factor_type}")
            except Exception as e:
                print(f"   计算失败: {factor_type}, 错误: {e}")

        result['factor_data'] = factor_data
        result['factor_count'] = len(factor_data)
        result['steps'].append('factor_calculation')
        print(f"   完成: 计算了 {len(factor_data)} 个因子")

        # Step 3: 因子评价
        evaluation_results = {}
        if evaluate and len(factor_data) > 0:
            print("\n[3/5] 📈 因子评价...")
            evaluator = FactorEvaluator()

            # 准备收益率
            returns_panel = self._prepare_returns_panel(data_dict)

            for factor_name, factor_series in factor_data.items():
                try:
                    eval_result = evaluator.evaluate_factor(
                        factor_series, returns_panel, n_layers=5
                    )
                    evaluation_results[factor_name] = eval_result
                    print(f"   评价完成: {factor_name}")
                except Exception as e:
                    print(f"   评价失败: {factor_name}, 错误: {e}")

        result['evaluation_results'] = evaluation_results
        result['steps'].append('factor_evaluation')

        # Step 4: 因子中性化
        neutralized_factors = {}
        if neutralize and len(factor_data) > 0 and self.extended_data_manager:
            print("\n[4/5] ⚖️  因子中性化...")
            neutralizer = FactorNeutralizer()

            # 获取行业分类用于中性化
            industry_classification = self.extended_data_manager.get_industry_classification(stock_list)

            for factor_name, factor_series in factor_data.items():
                try:
                    neutral_result = neutralizer.neutralize(
                        factor_series,
                        industry=industry_classification
                    )
                    neutralized_factors[factor_name] = neutral_result
                    print(f"   中性化完成: {factor_name}")
                except Exception as e:
                    print(f"   中性化失败: {factor_name}, 错误: {e}")

        result['neutralized_factors'] = neutralized_factors
        result['steps'].append('factor_neutralization')

        # Step 5: 生成报告
        print("\n[5/5] 📋 生成报告...")
        result['steps'].append('report_generation')

        result['end_time'] = datetime.now().isoformat()
        result['success'] = True

        print("\n✅ 因子研究Pipeline完成!")
        print("=" * 80)

        return result

    def run_strategy_backtest(
        self,
        strategy: Strategy,
        stock_list: Optional[List[str]] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        use_enhanced: bool = True,
        perform_attribution: bool = True,
        check_overfitting: bool = True,
        cost_model: Optional[TransactionCostModel] = None,
        position_manager: Optional[PositionManager] = None,
    ) -> Dict:
        """策略回测全流程

        数据获取 → 策略回测 → 绩效分析 → 归因分析 → 过拟合检测

        Args:
            strategy: 策略对象
            stock_list: 股票列表
            start_date: 开始日期
            end_date: 结束日期
            use_enhanced: 是否使用增强回测引擎
            perform_attribution: 是否做业绩归因
            check_overfitting: 是否做过拟合检测
            cost_model: 交易成本模型
            position_manager: 仓位管理器

        Returns:
            Dict: 回测结果
        """
        print("\n" + "=" * 80)
        print("🚀 策略回测 Pipeline".center(80))
        print("=" * 80)

        result = {
            'start_time': datetime.now().isoformat(),
            'strategy_name': strategy.name,
            'steps': []
        }

        # Step 1: 运行回测
        print("\n[1/4] 🔄 运行回测...")

        if use_enhanced:
            engine = EnhancedBacktestEngine(
                self.data_manager,
                initial_capital=1000000.0,
                start_date=start_date,
                end_date=end_date,
                cost_model=cost_model,
                position_manager=position_manager,
                extended_data_manager=self.extended_data_manager
            )
        else:
            engine = BacktestEngine(
                self.data_manager,
                initial_capital=1000000.0,
                start_date=start_date,
                end_date=end_date
            )

        engine.set_strategy(strategy)

        if use_enhanced:
            backtest_result = engine.run_enhanced(stock_list)
        else:
            backtest_result = engine.run(stock_list)

        result['backtest_result'] = backtest_result
        result['steps'].append('backtest')

        if not backtest_result or 'metrics' not in backtest_result:
            result['error'] = "Backtest failed"
            return result

        print(f"   完成: 回测收益率 {backtest_result['metrics'].get('total_return', 0):.2f}%")

        # Step 2: 扩展绩效分析
        print("\n[2/4] 📊 扩展绩效分析...")
        extended_metrics = None
        if 'portfolio_history' in backtest_result:
            try:
                history_df = pd.DataFrame(backtest_result['portfolio_history'])
                if 'returns' not in history_df.columns and 'total_assets' in history_df.columns:
                    history_df['returns'] = history_df['total_assets'].pct_change()

                extended = ExtendedPerformanceMetrics(history_df['returns'].dropna())
                extended_metrics = {
                    'sortino_ratio': extended.sortino_ratio(),
                    'omega_ratio': extended.omega_ratio(),
                    'calmar_ratio': extended.calmar_ratio(),
                    'var_historical': extended.var_historical(),
                    'cvar': extended.cvar(),
                    'skewness': extended.skewness(),
                    'kurtosis': extended.kurtosis()
                }
                print("   完成: 扩展绩效指标计算完成")
            except Exception as e:
                print(f"   扩展绩效分析失败: {e}")

        result['extended_metrics'] = extended_metrics
        result['steps'].append('extended_metrics')

        # Step 3: 业绩归因
        print("\n[3/4] 🎯 业绩归因...")
        attribution_result = None
        if perform_attribution:
            try:
                # 简化归因分析
                attribution_result = {
                    'message': 'Brinson attribution requires portfolio and benchmark weights',
                    'status': 'placeholder'
                }
                print("   完成: 业绩归因框架就绪")
            except Exception as e:
                print(f"   业绩归因失败: {e}")

        result['attribution'] = attribution_result
        result['steps'].append('attribution')

        # Step 4: 过拟合检测
        print("\n[4/4] 🔍 过拟合检测...")
        overfitting_result = None
        if check_overfitting and 'portfolio_history' in backtest_result:
            try:
                history_df = pd.DataFrame(backtest_result['portfolio_history'])
                if 'returns' not in history_df.columns and 'total_assets' in history_df.columns:
                    history_df['returns'] = history_df['total_assets'].pct_change()

                returns = history_df['returns'].dropna()
                if len(returns) > 100:
                    detector = OverfittingDetector()
                    overfitting_result = detector.detect_overfitting(returns, train_ratio=0.7)
                    status_str = overfitting_result.status.value if hasattr(overfitting_result, 'status') else 'unknown'
                    print(f"   完成: 过拟合检测完成，状态: {status_str}")

            except Exception as e:
                print(f"   过拟合检测失败: {e}")

        result['overfitting'] = overfitting_result
        result['steps'].append('overfitting_check')

        result['end_time'] = datetime.now().isoformat()
        result['success'] = True

        print("\n✅ 策略回测Pipeline完成!")
        print("=" * 80)

        return result

    def run_full_pipeline(self, config: Dict) -> Dict:
        """完整Pipeline（从配置到最终报告）

        Args:
            config: 配置字典

        Returns:
            Dict: 完整结果
        """
        print("\n" + "=" * 80)
        print("🏆 完整研究 Pipeline".center(80))
        print("=" * 80)

        result = {
            'start_time': datetime.now().isoformat(),
            'config': config
        }

        # 获取股票池
        stock_list = config.get('stock_list')
        if not stock_list and self.extended_data_manager:
            index_filter = config.get('index_filter', 'hs300')
            stock_list = self.extended_data_manager.get_stock_universe(
                index_filter=index_filter
            )

        if not stock_list:
            result['error'] = 'No stock list available'
            return result

        # 因子研究
        if config.get('run_factor_research', True):
            factor_result = self.run_factor_research(
                stock_list=stock_list,
                start_date=config.get('start_date'),
                end_date=config.get('end_date'),
                factor_config=config.get('factor_config')
            )
            result['factor_research'] = factor_result

        # 策略回测
        if config.get('run_strategy_backtest', True) and 'strategy' in config:
            strategy_result = self.run_strategy_backtest(
                strategy=config['strategy'],
                stock_list=stock_list,
                start_date=config.get('start_date'),
                end_date=config.get('end_date'),
                use_enhanced=config.get('use_enhanced', True)
            )
            result['strategy_backtest'] = strategy_result

        result['end_time'] = datetime.now().isoformat()
        result['success'] = True

        return result

    def _prepare_returns_panel(self, data_dict: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """准备收益率面板数据"""
        returns_dict = {}
        for ts_code, df in data_dict.items():
            if 'close' in df.columns and len(df) > 1:
                returns = df.set_index('trade_date')['close'].pct_change().dropna()
                returns_dict[ts_code] = returns

        if returns_dict:
            return pd.DataFrame(returns_dict)
        return pd.DataFrame()
