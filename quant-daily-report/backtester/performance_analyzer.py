#!/usr/bin/env python3
"""
绩效分析模块
分析策略回测绩效指标
"""

import numpy as np
import pandas as pd
from datetime import datetime


class PerformanceAnalyzer:
    """绩效分析器"""

    def __init__(self):
        self.returns = None
        self.portfolio_value = None
        self.benchmark_returns = None

    def analyze_performance(self, backtest_result):
        """分析回测绩效"""
        self.portfolio_value = backtest_result['portfolio_value']
        self.returns = self._calculate_returns(self.portfolio_value)
        self.benchmark_returns = backtest_result.get('benchmark_returns')

        performance_metrics = {
            'return_metrics': self._calculate_return_metrics(),
            'risk_metrics': self._calculate_risk_metrics(),
            'risk_adjusted_metrics': self._calculate_risk_adjusted_metrics(),
            'drawdown_metrics': self._calculate_drawdown_metrics(),
            'trade_metrics': self._calculate_trade_metrics(backtest_result)
        }

        return performance_metrics

    def _calculate_returns(self, portfolio_value):
        """计算每日收益率"""
        returns = portfolio_value.pct_change().dropna()
        return returns

    def _calculate_return_metrics(self):
        """计算收益指标"""
        total_return = self.portfolio_value.iloc[-1] / self.portfolio_value.iloc[0] - 1

        # 计算年化收益率
        days = len(self.returns)
        annualized_return = (1 + total_return) ** (365 / days) - 1

        # 计算平均每日收益率
        avg_daily_return = self.returns.mean()
        avg_annual_return = avg_daily_return * 252

        return {
            'total_return': total_return,
            'annualized_return': annualized_return,
            'avg_daily_return': avg_daily_return,
            'avg_annual_return': avg_annual_return,
            'cumulative_return': (1 + self.returns).cumprod() - 1
        }

    def _calculate_risk_metrics(self):
        """计算风险指标"""
        std_dev = self.returns.std()
        annualized_volatility = std_dev * np.sqrt(252)

        # 计算下行风险
        downside_returns = self.returns[self.returns < 0]
        downside_risk = downside_returns.std() * np.sqrt(252) if len(downside_returns) > 0 else 0

        # 计算最大回撤
        rolling_max = self.portfolio_value.cummax()
        drawdown = (self.portfolio_value - rolling_max) / rolling_max
        max_drawdown = drawdown.min()

        return {
            'volatility': annualized_volatility,
            'downside_risk': downside_risk,
            'max_drawdown': max_drawdown,
            'var_95': np.percentile(self.returns, 5),
            'cvar_95': self.returns[self.returns <= np.percentile(self.returns, 5)].mean()
        }

    def _calculate_risk_adjusted_metrics(self):
        """计算风险调整后收益指标"""
        # 计算夏普比率
        sharpe_ratio = self.returns.mean() / self.returns.std() * np.sqrt(252)

        # 计算索提诺比率
        downside_returns = self.returns[self.returns < 0]
        downside_std = downside_returns.std() if len(downside_returns) > 0 else float('inf')
        sortino_ratio = self.returns.mean() / downside_std * np.sqrt(252) if downside_std != 0 else 0

        # 计算信息比率
        if self.benchmark_returns is not None:
            excess_returns = self.returns - self.benchmark_returns
            information_ratio = excess_returns.mean() / excess_returns.std() * np.sqrt(252)
        else:
            information_ratio = None

        return {
            'sharpe_ratio': sharpe_ratio,
            'sortino_ratio': sortino_ratio,
            'information_ratio': information_ratio,
            'calmar_ratio': self._calculate_return_metrics()['annualized_return'] /
                           abs(self._calculate_risk_metrics()['max_drawdown'])
        }

    def _calculate_drawdown_metrics(self):
        """计算回撤指标"""
        rolling_max = self.portfolio_value.cummax()
        drawdown = (self.portfolio_value - rolling_max) / rolling_max

        max_drawdown = drawdown.min()

        # 计算最长回撤持续时间
        in_drawdown = drawdown < 0
        drawdown_periods = []
        current_start = None

        for date, in_dd in in_drawdown.items():
            if in_dd and current_start is None:
                current_start = date
            elif not in_dd and current_start is not None:
                drawdown_periods.append((current_start, date))
                current_start = None

        if current_start is not None:
            drawdown_periods.append((current_start, drawdown.index[-1]))

        if drawdown_periods:
            longest_drawdown = max((end - start).days for start, end in drawdown_periods)
        else:
            longest_drawdown = 0

        return {
            'max_drawdown': max_drawdown,
            'longest_drawdown_days': longest_drawdown,
            'average_drawdown': drawdown[drawdown < 0].mean(),
            'drawdown_frequency': (drawdown < 0).mean()
        }

    def _calculate_trade_metrics(self, backtest_result):
        """计算交易指标"""
        transactions = backtest_result.get('transactions')
        if transactions is None or len(transactions) == 0:
            return {}

        # 计算胜率
        winning_trades = transactions[transactions['profit'] > 0]
        win_rate = len(winning_trades) / len(transactions) if len(transactions) > 0 else 0

        # 计算盈亏比
        avg_win = winning_trades['profit'].mean() if len(winning_trades) > 0 else 0
        losing_trades = transactions[transactions['profit'] <= 0]
        avg_loss = abs(losing_trades['profit'].mean()) if len(losing_trades) > 0 else 0
        profit_factor = avg_win / avg_loss if avg_loss != 0 else float('inf')

        # 计算交易频率
        start_date = transactions['date'].iloc[0]
        end_date = transactions['date'].iloc[-1]
        days = (end_date - start_date).days
        trade_frequency = len(transactions) / days if days > 0 else 0

        return {
            'total_trades': len(transactions),
            'win_rate': win_rate,
            'profit_factor': profit_factor,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'total_profit': transactions['profit'].sum(),
            'trade_frequency': trade_frequency
        }

    def generate_performance_report(self, performance_metrics):
        """生成绩效报告"""
        report = """
# 📊 策略绩效报告

## 🎯 收益指标
- 总收益率: {:.2%}
- 年化收益率: {:.2%}
- 平均每日收益率: {:.2%}

## 🛡️ 风险指标
- 年化波动率: {:.2%}
- 最大回撤: {:.2%}
- 下行风险: {:.2%}
- VaR(95%): {:.2%}

## ⚖️ 风险调整后收益
- 夏普比率: {:.2f}
- 索提诺比率: {:.2f}
- 卡玛比率: {:.2f}

## 📉 回撤分析
- 最大回撤: {:.2%}
- 最长回撤天数: {}天
- 平均回撤: {:.2%}
- 回撤频率: {:.1%}

"""

        return report.format(
            performance_metrics['return_metrics']['total_return'],
            performance_metrics['return_metrics']['annualized_return'],
            performance_metrics['return_metrics']['avg_daily_return'],
            performance_metrics['risk_metrics']['volatility'],
            performance_metrics['risk_metrics']['max_drawdown'],
            performance_metrics['risk_metrics']['downside_risk'],
            performance_metrics['risk_metrics']['var_95'],
            performance_metrics['risk_adjusted_metrics']['sharpe_ratio'],
            performance_metrics['risk_adjusted_metrics']['sortino_ratio'],
            performance_metrics['risk_adjusted_metrics']['calmar_ratio'],
            performance_metrics['drawdown_metrics']['max_drawdown'],
            performance_metrics['drawdown_metrics']['longest_drawdown_days'],
            performance_metrics['drawdown_metrics']['average_drawdown'],
            performance_metrics['drawdown_metrics']['drawdown_frequency']
        )