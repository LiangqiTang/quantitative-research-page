"""
过拟合检测模块 - 策略稳健性验证

提供专业的过拟合检测和策略稳健性验证：
- 样本内 vs 样本外对比
- Walk Forward Analysis（滚动窗口验证）
- 参数敏感性分析
- 策略退化检测
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any, Callable
from dataclasses import dataclass
from enum import Enum
import warnings


class OverfittingStatus(Enum):
    """过拟合状态"""
    NO_SIGNAL = "no_signal"              # 没有明显信号
    HEALTHY = "healthy"                  # 健康，无过拟合迹象
    WARNING = "warning"                  # 警告，可能存在过拟合
    OVERFITTING = "overfitting"          # 明显过拟合
    SEVERE = "severe"                    # 严重过拟合


@dataclass
class TrainTestResult:
    """样本内/外对比结果"""
    in_sample_metrics: Dict[str, float]
    out_sample_metrics: Dict[str, float]
    performance_decay: Dict[str, float]
    status: OverfittingStatus
    is_overfitting: bool
    warning_signs: List[str]


@dataclass
class WalkForwardResult:
    """Walk Forward分析结果"""
    period_results: pd.DataFrame
    aggregate_metrics: Dict[str, float]
    stability_score: float
    consistency_score: float


@dataclass
class ParameterSensitivityResult:
    """参数敏感性分析结果"""
    param_grid_results: pd.DataFrame
    best_params: Dict[str, Any]
    sensitivity_score: float
    robust_region: Optional[Dict[str, Tuple[float, float]]] = None


class OverfittingDetector:
    """
    过拟合检测器

    提供多种方法检测和验证策略是否存在过拟合
    """

    def __init__(
        self,
        strategy: Optional[Any] = None,
        data: Optional[pd.DataFrame] = None,
        returns: Optional[pd.Series] = None,
        decay_threshold: float = 0.5,
        min_training_periods: int = 60
    ):
        """
        初始化过拟合检测器

        Args:
            strategy: 策略对象（可选，用于回测）
            data: 价格/因子数据（可选）
            returns: 策略收益率序列（可选，用于分析）
            decay_threshold: 绩效衰减阈值 (0.5 = 50%)
            min_training_periods: 最小训练期数
        """
        self.strategy = strategy
        self.data = data
        self.returns = returns
        self.decay_threshold = decay_threshold
        self.min_training_periods = min_training_periods

    def in_sample_vs_out_sample(
        self,
        train_ratio: float = 0.7,
        returns: Optional[pd.Series] = None,
        metrics: Optional[List[str]] = None
    ) -> TrainTestResult:
        """
        样本内 vs 样本外对比

        Args:
            train_ratio: 训练集比例
            returns: 收益率序列（如果未在初始化时提供）
            metrics: 要比较的指标列表

        Returns:
            TrainTestResult: 对比结果
        """
        returns = returns if returns is not None else self.returns
        if returns is None:
            raise ValueError("Must provide returns data")

        metrics = metrics or ['total_return', 'sharpe_ratio', 'win_rate']

        # 分割数据
        n = len(returns)
        train_size = int(n * train_ratio)

        if train_size < self.min_training_periods:
            warnings.warn(f"Training period too short: {train_size} < {self.min_training_periods}")

        in_sample = returns.iloc[:train_size]
        out_sample = returns.iloc[train_size:]

        # 计算指标
        in_metrics = self._calculate_simple_metrics(in_sample)
        out_metrics = self._calculate_simple_metrics(out_sample)

        # 计算绩效衰减
        decay = {}
        for metric in in_metrics:
            if metric in out_metrics and in_metrics[metric] != 0:
                decay[metric] = (in_metrics[metric] - out_metrics[metric]) / abs(in_metrics[metric])

        # 检查过拟合迹象
        warning_signs = []
        is_overfitting = False

        # 1. 检查夏普比率衰减
        if 'sharpe_ratio' in decay:
            if decay['sharpe_ratio'] > self.decay_threshold:
                warning_signs.append(f"Sharpe ratio decayed by {decay['sharpe_ratio']:.1%}")
                is_overfitting = True

        # 2. 检查收益率衰减
        if 'total_return' in decay:
            if decay['total_return'] > self.decay_threshold:
                warning_signs.append(f"Total return decayed by {decay['total_return']:.1%}")
                is_overfitting = True

        # 3. 检查样本外是否亏损
        if out_metrics.get('total_return', 0) < 0 and in_metrics.get('total_return', 0) > 0:
            warning_signs.append("Positive in-sample, negative out-sample return")
            is_overfitting = True

        # 4. 检查胜率下降
        if 'win_rate' in decay:
            if decay['win_rate'] > self.decay_threshold:
                warning_signs.append(f"Win rate decayed by {decay['win_rate']:.1%}")

        # 判断状态
        if not warning_signs:
            if in_metrics.get('sharpe_ratio', 0) > 0.5:
                status = OverfittingStatus.HEALTHY
            else:
                status = OverfittingStatus.NO_SIGNAL
        elif is_overfitting:
            if len(warning_signs) >= 2:
                status = OverfittingStatus.SEVERE
            else:
                status = OverfittingStatus.OVERFITTING
        else:
            status = OverfittingStatus.WARNING

        return TrainTestResult(
            in_sample_metrics=in_metrics,
            out_sample_metrics=out_metrics,
            performance_decay=decay,
            status=status,
            is_overfitting=is_overfitting,
            warning_signs=warning_signs
        )

    def _calculate_simple_metrics(self, returns: pd.Series) -> Dict[str, float]:
        """计算简单绩效指标"""
        metrics = {}

        # 总收益率
        metrics['total_return'] = float((1 + returns).prod() - 1)

        # 年化收益率
        if len(returns) > 0:
            years = len(returns) / 252
            metrics['annual_return'] = float((1 + metrics['total_return']) ** (1 / years) - 1) if years > 0 else 0

            # 波动率
            metrics['volatility'] = float(returns.std() * np.sqrt(252))

            # 夏普比率
            if metrics['volatility'] > 0:
                metrics['sharpe_ratio'] = float(metrics['annual_return'] / metrics['volatility'])
            else:
                metrics['sharpe_ratio'] = 0

            # 胜率
            metrics['win_rate'] = float((returns > 0).sum() / len(returns))

            # 最大回撤
            cumulative = (1 + returns).cumprod()
            cummax = cumulative.cummax()
            drawdown = (cumulative - cummax) / cummax
            metrics['max_drawdown'] = float(drawdown.min())

        return metrics

    def walk_forward_analysis(
        self,
        window_size: int = 252,
        step_size: int = 60,
        returns: Optional[pd.Series] = None,
        backtest_func: Optional[Callable] = None
    ) -> WalkForwardResult:
        """
        Walk Forward Analysis（滚动窗口验证）

        使用滚动窗口训练和测试，模拟真实的策略开发流程

        Args:
            window_size: 滚动窗口大小（训练期）
            step_size: 步长（测试期）
            returns: 收益率序列
            backtest_func: 回测函数（可选，用于重新训练策略）

        Returns:
            WalkForwardResult: 分析结果
        """
        returns = returns if returns is not None else self.returns
        if returns is None:
            raise ValueError("Must provide returns data")

        n = len(returns)
        period_results = []

        # 滚动窗口
        for i in range(window_size, n, step_size):
            train_start = max(0, i - window_size)
            train_end = i
            test_end = min(i + step_size, n)

            in_sample = returns.iloc[train_start:train_end]
            out_sample = returns.iloc[train_end:test_end]

            # 如果有回测函数，使用它
            if backtest_func is not None:
                train_data = self.data.iloc[train_start:train_end] if self.data is not None else None
                test_data = self.data.iloc[train_end:test_end] if self.data is not None else None
                out_metrics = backtest_func(train_data, test_data)
            else:
                # 直接使用已有的收益率
                out_metrics = self._calculate_simple_metrics(out_sample)

            in_metrics = self._calculate_simple_metrics(in_sample)

            period_results.append({
                'period': i,
                'train_start': returns.index[train_start] if isinstance(returns.index, pd.DatetimeIndex) else train_start,
                'train_end': returns.index[train_end - 1] if isinstance(returns.index, pd.DatetimeIndex) else train_end - 1,
                'test_start': returns.index[train_end] if isinstance(returns.index, pd.DatetimeIndex) else train_end,
                'test_end': returns.index[test_end - 1] if isinstance(returns.index, pd.DatetimeIndex) else test_end - 1,
                'in_sample_return': in_metrics.get('total_return', 0),
                'out_sample_return': out_metrics.get('total_return', 0),
                'in_sample_sharpe': in_metrics.get('sharpe_ratio', 0),
                'out_sample_sharpe': out_metrics.get('sharpe_ratio', 0),
                'in_sample_winrate': in_metrics.get('win_rate', 0),
                'out_sample_winrate': out_metrics.get('win_rate', 0),
            })

        period_df = pd.DataFrame(period_results)

        # 计算聚合指标
        aggregate_metrics = {}
        if not period_df.empty:
            aggregate_metrics['avg_out_sample_return'] = period_df['out_sample_return'].mean()
            aggregate_metrics['std_out_sample_return'] = period_df['out_sample_return'].std()
            aggregate_metrics['positive_periods'] = float((period_df['out_sample_return'] > 0).sum() / len(period_df))
            aggregate_metrics['avg_sharpe_degradation'] = float(
                (period_df['in_sample_sharpe'] - period_df['out_sample_sharpe']).mean()
            )

            # 稳定性评分：各期收益率的一致性
            if period_df['out_sample_return'].std() > 0:
                stability_score = float(
                    period_df['out_sample_return'].mean() / period_df['out_sample_return'].std()
                )
            else:
                stability_score = 0

            # 一致性评分：正收益期数比例
            consistency_score = aggregate_metrics['positive_periods']
        else:
            stability_score = 0
            consistency_score = 0

        return WalkForwardResult(
            period_results=period_df,
            aggregate_metrics=aggregate_metrics,
            stability_score=stability_score,
            consistency_score=consistency_score
        )

    def parameter_sensitivity(
        self,
        param_grid: Dict[str, List[Any]],
        eval_func: Callable,
        base_params: Optional[Dict[str, Any]] = None
    ) -> ParameterSensitivityResult:
        """
        参数敏感性分析

        测试策略在不同参数下的表现，寻找稳健区域

        Args:
            param_grid: 参数网格 {参数名: [候选值列表]}
            eval_func: 评估函数，接收参数字典，返回指标字典
            base_params: 基准参数字典（可选）

        Returns:
            ParameterSensitivityResult: 敏感性分析结果
        """
        from itertools import product

        # 生成所有参数组合
        param_names = list(param_grid.keys())
        param_values = [param_grid[name] for name in param_names]

        results = []
        for value_combo in product(*param_values):
            params = dict(zip(param_names, value_combo))
            if base_params:
                params = {**base_params, **params}

            # 评估
            try:
                metrics = eval_func(params)
                result = {**params, **metrics}
                results.append(result)
            except Exception as e:
                warnings.warn(f"Evaluation failed for params {params}: {e}")

        if not results:
            return ParameterSensitivityResult(
                param_grid_results=pd.DataFrame(),
                best_params={},
                sensitivity_score=0
            )

        results_df = pd.DataFrame(results)

        # 找出最佳参数（按夏普比率或收益率）
        if 'sharpe_ratio' in results_df.columns:
            best_idx = results_df['sharpe_ratio'].idxmax()
        elif 'total_return' in results_df.columns:
            best_idx = results_df['total_return'].idxmax()
        else:
            best_idx = 0

        best_params = dict(results_df.iloc[best_idx][param_names])

        # 计算敏感性评分：参数变化导致的绩效变化
        sensitivity_scores = []
        for param in param_names:
            # 固定其他参数，计算该参数的影响
            unique_vals = results_df[param].unique()
            if len(unique_vals) < 2:
                continue

            # 计算该参数不同取值下的绩效标准差
            if 'sharpe_ratio' in results_df.columns:
                perf_by_val = results_df.groupby(param)['sharpe_ratio'].std()
            elif 'total_return' in results_df.columns:
                perf_by_val = results_df.groupby(param)['total_return'].std()
            else:
                continue

            if len(perf_by_val) > 0:
                sensitivity_scores.append(perf_by_val.mean())

        sensitivity_score = float(np.mean(sensitivity_scores)) if sensitivity_scores else 0

        return ParameterSensitivityResult(
            param_grid_results=results_df,
            best_params=best_params,
            sensitivity_score=sensitivity_score
        )

    def strategy_degradation_detection(
        self,
        returns: Optional[pd.Series] = None,
        recent_periods: int = 60,
        lookback_periods: int = 252
    ) -> Dict[str, Any]:
        """
        策略退化检测

        检测近期绩效是否显著下降

        Args:
            returns: 收益率序列
            recent_periods: 近期期数
            lookback_periods: 回看期数

        Returns:
            检测结果字典
        """
        returns = returns if returns is not None else self.returns
        if returns is None:
            raise ValueError("Must provide returns data")

        n = len(returns)
        if n < recent_periods + lookback_periods:
            warnings.warn("Insufficient data for degradation detection")

        # 分割近期和历史
        recent = returns.iloc[-recent_periods:] if n >= recent_periods else returns
        historical = returns.iloc[-(recent_periods + lookback_periods):-recent_periods] if n >= recent_periods + lookback_periods else returns.iloc[:-recent_periods]

        # 计算指标
        recent_metrics = self._calculate_simple_metrics(recent)
        historical_metrics = self._calculate_simple_metrics(historical)

        # 统计显著性检验
        t_stat, p_value = 0, 1
        if len(recent) >= 20 and len(historical) >= 20:
            try:
                from scipy import stats
                t_stat, p_value = stats.ttest_ind(recent, historical, equal_var=False)
            except:
                pass

        # 检测退化
        degradation_signs = []
        is_degrading = False

        # 收益率下降
        if 'annual_return' in recent_metrics and 'annual_return' in historical_metrics:
            if recent_metrics['annual_return'] < historical_metrics['annual_return'] * 0.5:
                degradation_signs.append("Recent return < 50% of historical")
                is_degrading = True

        # 夏普比率下降
        if 'sharpe_ratio' in recent_metrics and 'sharpe_ratio' in historical_metrics:
            if recent_metrics['sharpe_ratio'] < historical_metrics['sharpe_ratio'] * 0.5:
                degradation_signs.append("Recent Sharpe < 50% of historical")
                is_degrading = True

        # 统计显著
        if p_value < 0.05 and recent_metrics.get('annual_return', 0) < historical_metrics.get('annual_return', 0):
            degradation_signs.append(f"Statistically significant degradation (p={p_value:.3f})")
            is_degrading = True

        # 近期亏损
        if recent_metrics.get('total_return', 0) < -0.1:  # 近期亏损超过10%
            degradation_signs.append("Recent loss > 10%")

        return {
            'recent_metrics': recent_metrics,
            'historical_metrics': historical_metrics,
            'degradation_signs': degradation_signs,
            'is_degrading': is_degrading,
            't_statistic': float(t_stat),
            'p_value': float(p_value)
        }

    def comprehensive_check(
        self,
        returns: Optional[pd.Series] = None
    ) -> Dict[str, Any]:
        """
        全面的过拟合检测

        运行所有检测方法并返回综合报告

        Args:
            returns: 收益率序列

        Returns:
            综合检测报告
        """
        returns = returns if returns is not None else self.returns
        if returns is None:
            raise ValueError("Must provide returns data")

        report = {}

        # 1. 样本内/外对比
        try:
            report['train_test'] = self.in_sample_vs_out_sample(returns=returns)
        except Exception as e:
            report['train_test_error'] = str(e)

        # 2. Walk Forward分析
        try:
            window_size = min(252, len(returns) // 2)
            step_size = min(60, window_size // 4)
            if window_size > 30 and step_size > 5:
                report['walk_forward'] = self.walk_forward_analysis(
                    window_size=window_size,
                    step_size=step_size,
                    returns=returns
                )
        except Exception as e:
            report['walk_forward_error'] = str(e)

        # 3. 策略退化检测
        try:
            recent_periods = min(60, len(returns) // 4)
            lookback_periods = min(252, len(returns) // 2)
            if recent_periods > 10 and lookback_periods > 30:
                report['degradation'] = self.strategy_degradation_detection(
                    returns=returns,
                    recent_periods=recent_periods,
                    lookback_periods=lookback_periods
                )
        except Exception as e:
            report['degradation_error'] = str(e)

        # 综合判断
        all_warnings = []
        is_overfitting = False

        if 'train_test' in report:
            tt = report['train_test']
            all_warnings.extend(tt.warning_signs)
            if tt.is_overfitting:
                is_overfitting = True

        if 'degradation' in report:
            deg = report['degradation']
            all_warnings.extend(deg.get('degradation_signs', []))
            if deg.get('is_degrading', False):
                is_overfitting = True

        report['summary'] = {
            'all_warnings': all_warnings,
            'is_overfitting': is_overfitting,
            'warning_count': len(all_warnings)
        }

        return report


def detect_overfitting(
    returns: pd.Series,
    train_ratio: float = 0.7,
    decay_threshold: float = 0.5
) -> TrainTestResult:
    """
    便捷函数：检测过拟合

    Args:
        returns: 收益率序列
        train_ratio: 训练集比例
        decay_threshold: 绩效衰减阈值

    Returns:
        TrainTestResult: 检测结果
    """
    detector = OverfittingDetector(
        returns=returns,
        decay_threshold=decay_threshold
    )
    return detector.in_sample_vs_out_sample(train_ratio=train_ratio)


def walk_forward_validation(
    returns: pd.Series,
    window_size: int = 252,
    step_size: int = 60
) -> WalkForwardResult:
    """
    便捷函数：Walk Forward验证

    Args:
        returns: 收益率序列
        window_size: 滚动窗口大小
        step_size: 步长

    Returns:
        WalkForwardResult: 验证结果
    """
    detector = OverfittingDetector(returns=returns)
    return detector.walk_forward_analysis(
        window_size=window_size,
        step_size=step_size
    )
