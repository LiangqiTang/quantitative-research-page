"""
扩展绩效指标模块 - 专业的风险与收益分析

提供全面的绩效指标：
- 风险调整收益：Sortino、Omega、Calmar、Sterling
- 收益分布：偏度、峰度、VaR、CVaR
- 交易统计：胜率、盈亏比、平均持仓时间、最大连续亏损
- 基准比较：超额收益、信息比率、跟踪误差、CAPM Alpha/Beta
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from scipy import stats


@dataclass
class TradeRecord:
    """交易记录（用于交易统计）"""
    ts_code: str
    direction: str  # 'buy' or 'sell'
    quantity: int
    price: float
    entry_price: float
    exit_price: float
    entry_date: str
    exit_date: str
    pnl: float
    pnl_pct: float


class ExtendedPerformanceMetrics:
    """
    扩展绩效指标计算器

    提供专业的风险与收益分析指标
    """

    def __init__(
        self,
        returns: pd.Series,
        benchmark_returns: Optional[pd.Series] = None,
        risk_free_rate: float = 0.03,
        frequency: int = 252,
        trades: Optional[List[TradeRecord]] = None
    ):
        """
        初始化绩效指标计算器

        Args:
            returns: 收益率序列（日频或其他频率）
            benchmark_returns: 基准收益率序列（可选）
            risk_free_rate: 年化无风险利率
            frequency: 年化频率 (日频: 252, 周频: 52, 月频: 12)
            trades: 交易记录列表（可选，用于交易统计）
        """
        self.returns = returns.dropna()
        self.benchmark_returns = benchmark_returns.dropna() if benchmark_returns is not None else None
        self.risk_free_rate = risk_free_rate
        self.frequency = frequency
        self.trades = trades or []

        # 对齐基准收益率
        if self.benchmark_returns is not None:
            common_idx = self.returns.index.intersection(self.benchmark_returns.index)
            self.returns = self.returns.loc[common_idx]
            self.benchmark_returns = self.benchmark_returns.loc[common_idx]

        # 计算日度无风险利率
        self.daily_rf = (1 + risk_free_rate) ** (1 / frequency) - 1

    # ========== 风险调整收益指标 ==========

    def sharpe_ratio(self) -> float:
        """
        夏普比率 (Sharpe Ratio)

        定义：(组合收益 - 无风险利率) / 组合波动率

        Returns:
            年化夏普比率
        """
        excess_returns = self.returns - self.daily_rf
        if excess_returns.std() == 0:
            return 0.0
        return float(excess_returns.mean() / excess_returns.std() * np.sqrt(self.frequency))

    def sortino_ratio(self, threshold: Optional[float] = None) -> float:
        """
        Sortino比率

        定义：(组合收益 - 目标收益) / 下行波动率

        只考虑下行风险，比夏普比率更适合评估偏度分布的策略

        Args:
            threshold: 目标收益率，默认使用无风险利率

        Returns:
            年化Sortino比率
        """
        target = threshold if threshold is not None else self.daily_rf
        excess_returns = self.returns - target

        # 只考虑负的超额收益计算下行波动率
        downside_returns = excess_returns[excess_returns < 0]
        if len(downside_returns) == 0 or downside_returns.std() == 0:
            return 0.0

        downside_vol = downside_returns.std() * np.sqrt(self.frequency)
        annual_excess = excess_returns.mean() * self.frequency

        return float(annual_excess / downside_vol) if downside_vol != 0 else 0.0

    def omega_ratio(self, threshold: Optional[float] = None) -> float:
        """
        Omega比率

        定义：(盈利概率 * 平均盈利) / (亏损概率 * 平均亏损)

        Omega比率考虑了整个收益分布，不受正态分布假设限制

        Args:
            threshold: 目标收益率，默认使用无风险利率

        Returns:
            Omega比率
        """
        target = threshold if threshold is not None else self.daily_rf
        excess_returns = self.returns - target

        # 盈利部分
        gains = excess_returns[excess_returns > 0]
        # 亏损部分（取绝对值）
        losses = -excess_returns[excess_returns < 0]

        if len(losses) == 0 or losses.mean() == 0:
            return float('inf') if len(gains) > 0 else 1.0

        omega = (len(gains) * gains.mean()) / (len(losses) * losses.mean())
        return float(omega)

    def calmar_ratio(self) -> float:
        """
        Calmar比率

        定义：年化收益率 / 最大回撤

        衡量每承担一单位的最大回撤，可以获得多少收益

        Returns:
            Calmar比率
        """
        annual_return = self.annual_return()
        max_dd = self.max_drawdown()

        return float(annual_return / abs(max_dd)) if max_dd != 0 else 0.0

    def sterling_ratio(self, average_drawdown_periods: int = 3) -> float:
        """
        Sterling比率

        类似Calmar，但使用平均最大回撤而不是单一最大回撤

        Args:
            average_drawdown_periods: 计算平均的回撤期数

        Returns:
            Sterling比率
        """
        annual_return = self.annual_return()
        drawdowns = self._get_drawdown_series()

        # 找出回撤的独立峰值
        dd_peaks = []
        in_drawdown = False
        current_dd = 0

        for dd in drawdowns:
            if dd < 0:
                in_drawdown = True
                current_dd = min(current_dd, dd)
            elif in_drawdown:
                dd_peaks.append(abs(current_dd))
                current_dd = 0
                in_drawdown = False

        if in_drawdown:
            dd_peaks.append(abs(current_dd))

        if not dd_peaks:
            return 0.0

        # 取最大的N个回撤的平均
        dd_peaks_sorted = sorted(dd_peaks, reverse=True)
        avg_dd = np.mean(dd_peaks_sorted[:average_drawdown_periods])

        return float(annual_return / avg_dd) if avg_dd != 0 else 0.0

    # ========== 收益分布指标 ==========

    def skewness(self) -> float:
        """
        偏度 (Skewness)

        衡量收益分布的不对称性
        - 正偏：长尾在右侧，存在较大的正收益
        - 负偏：长尾在左侧，存在较大的负亏损

        Returns:
            偏度
        """
        return float(stats.skew(self.returns))

    def kurtosis(self) -> float:
        """
        峰度 (Kurtosis)

        衡量收益分布的尖峭程度和尾部厚度
        - >0：尖峰厚尾，比正态分布有更多极端值
        - <0：低峰薄尾，比正态分布更平缓

        Returns:
            超额峰度（减去正态分布的峰度3）
        """
        return float(stats.kurtosis(self.returns))

    def var_historical(self, confidence: float = 0.95) -> float:
        """
        历史VaR (Value at Risk)

        定义：在给定置信水平下，未来一定时期内的最大可能损失

        使用历史模拟法，不假设分布

        Args:
            confidence: 置信水平 (0.95 = 95%)

        Returns:
            历史VaR（正数表示损失比例）
        """
        var_level = 1 - confidence
        var = float(np.percentile(self.returns, var_level * 100))
        return float(-var)  # 返回正数表示损失

    def var_parametric(self, confidence: float = 0.95) -> float:
        """
        参数VaR (Parametric VaR)

        假设收益服从正态分布

        Args:
            confidence: 置信水平

        Returns:
            参数VaR（正数表示损失比例）
        """
        mean = self.returns.mean()
        std = self.returns.std()
        z_score = stats.norm.ppf(1 - confidence)

        var = -(mean + z_score * std)
        return float(var)

    def cvar(self, confidence: float = 0.95) -> float:
        """
        条件VaR (CVaR / Expected Shortfall)

        定义：超过VaR的平均损失

        CVaR比VaR更保守，考虑了尾部风险

        Args:
            confidence: 置信水平

        Returns:
            CVaR（正数表示损失比例）
        """
        var_level = 1 - confidence
        var = np.percentile(self.returns, var_level * 100)

        # 计算低于VaR的平均损失
        tail_returns = self.returns[self.returns <= var]
        if len(tail_returns) == 0:
            return float(-var)

        cvar = -tail_returns.mean()
        return float(cvar)

    # ========== 交易统计指标 ==========

    def win_rate(self) -> float:
        """
        胜率 (Win Rate)

        定义：盈利交易次数 / 总交易次数

        Returns:
            胜率 (0-1)
        """
        if not self.trades:
            return 0.0

        winning_trades = sum(1 for t in self.trades if t.pnl > 0)
        return float(winning_trades / len(self.trades))

    def profit_loss_ratio(self) -> float:
        """
        盈亏比 (Profit/Loss Ratio)

        定义：平均盈利 / 平均亏损

        Returns:
            盈亏比
        """
        if not self.trades:
            return 0.0

        profits = [t.pnl for t in self.trades if t.pnl > 0]
        losses = [-t.pnl for t in self.trades if t.pnl < 0]

        if not losses or np.mean(losses) == 0:
            return float('inf') if profits else 0.0

        avg_profit = np.mean(profits) if profits else 0
        avg_loss = np.mean(losses)

        return float(avg_profit / avg_loss)

    def avg_holding_period(self) -> float:
        """
        平均持仓时间

        Returns:
            平均持仓天数
        """
        if not self.trades:
            return 0.0

        periods = []
        for t in self.trades:
            try:
                entry = pd.to_datetime(t.entry_date)
                exit = pd.to_datetime(t.exit_date)
                periods.append((exit - entry).days)
            except:
                continue

        return float(np.mean(periods)) if periods else 0.0

    def max_consecutive_losses(self) -> int:
        """
        最大连续亏损天数

        Returns:
            最大连续亏损天数
        """
        if len(self.returns) == 0:
            return 0

        max_streak = 0
        current_streak = 0

        for ret in self.returns:
            if ret < 0:
                current_streak += 1
                max_streak = max(max_streak, current_streak)
            else:
                current_streak = 0

        return max_streak

    def max_consecutive_wins(self) -> int:
        """
        最大连续盈利天数

        Returns:
            最大连续盈利天数
        """
        if len(self.returns) == 0:
            return 0

        max_streak = 0
        current_streak = 0

        for ret in self.returns:
            if ret > 0:
                current_streak += 1
                max_streak = max(max_streak, current_streak)
            else:
                current_streak = 0

        return max_streak

    # ========== 基准比较指标 ==========

    def excess_return(self) -> float:
        """
        超额收益率 (Excess Return)

        定义：组合收益率 - 基准收益率

        Returns:
            年化超额收益率
        """
        if self.benchmark_returns is None:
            return 0.0

        port_return = (1 + self.returns).prod() - 1
        bench_return = (1 + self.benchmark_returns).prod() - 1

        # 年化
        years = len(self.returns) / self.frequency
        annual_excess = (1 + port_return) ** (1 / years) - (1 + bench_return) ** (1 / years)

        return float(annual_excess)

    def information_ratio(self) -> float:
        """
        信息比率 (Information Ratio, IR)

        定义：超额收益均值 / 跟踪误差

        衡量相对于基准的风险调整后收益

        Returns:
            年化信息比率
        """
        if self.benchmark_returns is None:
            return 0.0

        active_returns = self.returns - self.benchmark_returns
        if active_returns.std() == 0:
            return 0.0

        ir = active_returns.mean() / active_returns.std() * np.sqrt(self.frequency)
        return float(ir)

    def tracking_error(self) -> float:
        """
        跟踪误差 (Tracking Error, TE)

        定义：超额收益的波动率

        衡量组合跟踪基准的紧密程度

        Returns:
            年化跟踪误差
        """
        if self.benchmark_returns is None:
            return 0.0

        active_returns = self.returns - self.benchmark_returns
        return float(active_returns.std() * np.sqrt(self.frequency))

    def capm_alpha_beta(self) -> Tuple[float, float]:
        """
        CAPM Alpha和Beta

        Alpha：超额收益（不能被市场解释的部分）
        Beta：系统风险暴露

        Returns:
            (Alpha, Beta) 都是年化值
        """
        if self.benchmark_returns is None:
            return 0.0, 1.0

        # 使用线性回归：r_p - r_f = alpha + beta * (r_b - r_f)
        excess_port = self.returns - self.daily_rf
        excess_bench = self.benchmark_returns - self.daily_rf

        # 添加常数项
        X = np.column_stack([np.ones(len(excess_bench)), excess_bench])
        y = excess_port.values

        try:
            beta, intercept = 0, 0
            # 最小二乘法回归
            coeffs, _, _, _ = np.linalg.lstsq(X, y, rcond=None)
            intercept, beta = coeffs[0], coeffs[1]

            # Alpha年化
            alpha = intercept * self.frequency

            return float(alpha), float(beta)
        except:
            return 0.0, 1.0

    # ========== 基础指标 ==========

    def total_return(self) -> float:
        """总收益率"""
        return float((1 + self.returns).prod() - 1)

    def annual_return(self) -> float:
        """年化收益率"""
        total = self.total_return()
        years = len(self.returns) / self.frequency
        return float((1 + total) ** (1 / years) - 1) if years > 0 else 0.0

    def volatility(self) -> float:
        """年化波动率"""
        return float(self.returns.std() * np.sqrt(self.frequency))

    def max_drawdown(self) -> float:
        """最大回撤（负数表示回撤）"""
        drawdowns = self._get_drawdown_series()
        return float(drawdowns.min())

    def _get_drawdown_series(self) -> pd.Series:
        """获取回撤序列"""
        cumulative = (1 + self.returns).cumprod()
        cummax = cumulative.cummax()
        drawdowns = (cumulative - cummax) / cummax
        return drawdowns

    # ========== 综合指标 ==========

    def calculate_all(self) -> Dict[str, Any]:
        """
        计算所有绩效指标

        Returns:
            包含所有指标的字典
        """
        metrics = {}

        # 基础收益指标
        metrics['total_return'] = self.total_return()
        metrics['annual_return'] = self.annual_return()
        metrics['volatility'] = self.volatility()
        metrics['max_drawdown'] = self.max_drawdown()

        # 风险调整收益
        metrics['sharpe_ratio'] = self.sharpe_ratio()
        metrics['sortino_ratio'] = self.sortino_ratio()
        metrics['omega_ratio'] = self.omega_ratio()
        metrics['calmar_ratio'] = self.calmar_ratio()
        metrics['sterling_ratio'] = self.sterling_ratio()

        # 收益分布
        metrics['skewness'] = self.skewness()
        metrics['kurtosis'] = self.kurtosis()
        metrics['var_historical_95'] = self.var_historical(0.95)
        metrics['var_historical_99'] = self.var_historical(0.99)
        metrics['var_parametric_95'] = self.var_parametric(0.95)
        metrics['cvar_95'] = self.cvar(0.95)
        metrics['cvar_99'] = self.cvar(0.99)

        # 交易统计
        if self.trades:
            metrics['win_rate'] = self.win_rate()
            metrics['profit_loss_ratio'] = self.profit_loss_ratio()
            metrics['avg_holding_period'] = self.avg_holding_period()

        metrics['max_consecutive_losses'] = self.max_consecutive_losses()
        metrics['max_consecutive_wins'] = self.max_consecutive_wins()

        # 基准比较
        if self.benchmark_returns is not None:
            metrics['excess_return'] = self.excess_return()
            metrics['information_ratio'] = self.information_ratio()
            metrics['tracking_error'] = self.tracking_error()
            alpha, beta = self.capm_alpha_beta()
            metrics['capm_alpha'] = alpha
            metrics['capm_beta'] = beta

        return metrics


def calculate_performance_summary(
    returns: pd.Series,
    benchmark_returns: Optional[pd.Series] = None,
    risk_free_rate: float = 0.03,
    frequency: int = 252
) -> Dict[str, Any]:
    """
    快速计算绩效摘要（便捷函数）

    Args:
        returns: 收益率序列
        benchmark_returns: 基准收益率（可选）
        risk_free_rate: 无风险利率
        frequency: 年化频率

    Returns:
        绩效指标字典
    """
    calculator = ExtendedPerformanceMetrics(
        returns=returns,
        benchmark_returns=benchmark_returns,
        risk_free_rate=risk_free_rate,
        frequency=frequency
    )
    return calculator.calculate_all()
