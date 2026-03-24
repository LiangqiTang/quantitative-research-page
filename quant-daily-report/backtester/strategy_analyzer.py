"""
策略分析器
负责分析策略表现、评估策略优劣
"""

import pandas as pd
import numpy as np
from scipy import stats
from typing import Dict, List, Optional
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns

class StrategyAnalyzer:
    """策略分析器"""

    def __init__(self):
        self.metrics = {
            'return': ['total_return', 'annual_return', 'daily_return'],
            'risk': ['max_drawdown', 'volatility', 'var', 'cvar'],
            'risk_adjusted': ['sharpe_ratio', 'sortino_ratio', 'information_ratio', 'calmar_ratio'],
            'performance': ['win_rate', 'profit_loss_ratio', 'expectancy', 'kelly_criterion'],
            'timing': ['alpha', 'beta', 'tracking_error']
        }

    def analyze_strategy_performance(self, backtest_result: Dict) -> Dict:
        """
        全面分析策略表现
        :param backtest_result: 回测结果
        :return: 分析报告
        """
        report = {
            'overview': {},
            'return_metrics': {},
            'risk_metrics': {},
            'risk_adjusted_metrics': {},
            'performance_metrics': {},
            'timing_metrics': {},
            'attribution_analysis': {},
            'drawdown_analysis': {},
            'transaction_analysis': {},
            'conclusion': '',
            'suggestions': []
        }

        try:
            # 提取数据
            portfolio_value = backtest_result.get('portfolio_value', pd.Series())
            daily_returns = backtest_result.get('daily_returns', pd.Series())
            benchmark_returns = backtest_result.get('benchmark_returns', pd.Series())
            transactions = backtest_result.get('transactions', pd.DataFrame())

            # 计算各类指标
            report['return_metrics'] = self._calculate_return_metrics(daily_returns)
            report['risk_metrics'] = self._calculate_risk_metrics(daily_returns, portfolio_value)
            report['risk_adjusted_metrics'] = self._calculate_risk_adjusted_metrics(
                daily_returns, benchmark_returns
            )
            report['performance_metrics'] = self._calculate_performance_metrics(transactions, daily_returns)
            report['timing_metrics'] = self._calculate_timing_metrics(daily_returns, benchmark_returns)
            report['attribution_analysis'] = self._perform_attribution_analysis(backtest_result)
            report['drawdown_analysis'] = self._analyze_drawdowns(portfolio_value)
            report['transaction_analysis'] = self._analyze_transactions(transactions)

            # 生成概述
            report['overview'] = self._generate_overview(report)

            # 生成结论和建议
            report['conclusion'] = self._generate_conclusion(report)
            report['suggestions'] = self._generate_suggestions(report, backtest_result)

            return report

        except Exception as e:
            print(f"❌ 策略分析失败: {e}")
            raise

    def _calculate_return_metrics(self, daily_returns: pd.Series) -> Dict:
        """计算收益指标"""
        if daily_returns.empty:
            return {}

        total_return = (1 + daily_returns).prod() - 1
        annual_return = (1 + total_return) ** (252 / len(daily_returns)) - 1
        daily_return_avg = daily_returns.mean()
        daily_return_std = daily_returns.std()

        positive_days = (daily_returns > 0).sum()
        negative_days = (daily_returns < 0).sum()

        return {
            'total_return': total_return,
            'annual_return': annual_return,
            'daily_return_mean': daily_return_avg,
            'daily_return_std': daily_return_std,
            'positive_days_ratio': positive_days / len(daily_returns),
            'negative_days_ratio': negative_days / len(daily_returns),
            'best_day': daily_returns.max(),
            'worst_day': daily_returns.min(),
            'win_days': positive_days,
            'loss_days': negative_days
        }

    def _calculate_risk_metrics(self, daily_returns: pd.Series, portfolio_value: pd.Series) -> Dict:
        """计算风险指标"""
        if daily_returns.empty:
            return {}

        # 计算最大回撤
        if not portfolio_value.empty:
            peak = portfolio_value.cummax()
            drawdown = (portfolio_value - peak) / peak
            max_drawdown = drawdown.min()
            drawdown_duration = self._calculate_drawdown_duration(drawdown)
        else:
            max_drawdown = float('nan')
            drawdown_duration = {}

        # 计算VaR和CVaR
        var_95 = np.percentile(daily_returns, 5)
        cvar_95 = daily_returns[daily_returns <= var_95].mean()

        return {
            'volatility': daily_returns.std() * np.sqrt(252),
            'downside_deviation': self._calculate_downside_deviation(daily_returns),
            'max_drawdown': max_drawdown,
            'max_drawdown_duration': drawdown_duration.get('max_duration', 0),
            'average_drawdown_duration': drawdown_duration.get('avg_duration', 0),
            'var_95': var_95,
            'cvar_95': cvar_95,
            'skewness': daily_returns.skew(),
            'kurtosis': daily_returns.kurtosis()
        }

    def _calculate_risk_adjusted_metrics(self, daily_returns: pd.Series,
                                       benchmark_returns: pd.Series = None) -> Dict:
        """计算风险调整后收益指标"""
        if daily_returns.empty:
            return {}

        metrics = {}

        # 夏普比率
        sharpe_ratio = self._calculate_sharpe_ratio(daily_returns)
        metrics['sharpe_ratio'] = sharpe_ratio

        # Sortino比率
        sortino_ratio = self._calculate_sortino_ratio(daily_returns)
        metrics['sortino_ratio'] = sortino_ratio

        # Calmar比率
        total_return = (1 + daily_returns).prod() - 1
        if not portfolio_value.empty:
            peak = portfolio_value.cummax()
            drawdown = (portfolio_value - peak) / peak
            max_drawdown = drawdown.min()
            if max_drawdown < 0:
                metrics['calmar_ratio'] = total_return / abs(max_drawdown)

        # 信息比率
        if benchmark_returns is not None and not benchmark_returns.empty:
            active_returns = daily_returns - benchmark_returns
            information_ratio = active_returns.mean() / active_returns.std() * np.sqrt(252)
            metrics['information_ratio'] = information_ratio

        return metrics

    def _calculate_performance_metrics(self, transactions: pd.DataFrame,
                                     daily_returns: pd.Series) -> Dict:
        """计算绩效指标"""
        metrics = {}

        if transactions is not None and not transactions.empty:
            # 计算胜率和盈亏比
            winning_trades = transactions[transactions['profit'] > 0]
            losing_trades = transactions[transactions['profit'] <= 0]

            win_rate = len(winning_trades) / len(transactions) if len(transactions) > 0 else 0
            avg_win = winning_trades['profit'].mean() if len(winning_trades) > 0 else 0
            avg_loss = abs(losing_trades['profit'].mean()) if len(losing_trades) > 0 else 0
            profit_loss_ratio = avg_win / avg_loss if avg_loss > 0 else float('inf')

            # 计算期望收益
            expectancy = win_rate * avg_win - (1 - win_rate) * avg_loss
            metrics.update({
                'win_rate': win_rate,
                'profit_loss_ratio': profit_loss_ratio,
                'avg_win_trade': avg_win,
                'avg_loss_trade': avg_loss,
                'expectancy': expectancy,
                'total_trades': len(transactions),
                'winning_trades': len(winning_trades),
                'losing_trades': len(losing_trades)
            })

            # 计算凯利准则
            if avg_loss > 0:
                kelly_fraction = (win_rate / avg_loss) - ((1 - win_rate) / avg_win) if avg_win > 0 else 0
                metrics['kelly_criterion'] = max(0, kelly_fraction)

        else:
            # 如果没有交易记录，使用日线数据估算
            winning_days = (daily_returns > 0).sum()
            total_days = len(daily_returns)
            win_rate = winning_days / total_days if total_days > 0 else 0
            metrics['win_rate_estimate'] = win_rate

        return metrics

    def _calculate_timing_metrics(self, daily_returns: pd.Series,
                                 benchmark_returns: pd.Series = None) -> Dict:
        """计算时机选择指标"""
        if daily_returns.empty:
            return {}

        metrics = {}

        if benchmark_returns is not None and not benchmark_returns.empty:
            # 计算Alpha和Beta
            if len(daily_returns) == len(benchmark_returns):
                cov_matrix = np.cov(daily_returns, benchmark_returns)
                beta = cov_matrix[0, 1] / cov_matrix[1, 1] if cov_matrix[1, 1] > 0 else 0

                # 使用CAPM计算Alpha
                risk_free_rate = 0.02  # 假设无风险利率为2%
                excess_return = daily_returns.mean() - risk_free_rate / 252
                benchmark_excess_return = benchmark_returns.mean() - risk_free_rate / 252
                alpha = excess_return - beta * benchmark_excess_return

                metrics.update({
                    'alpha': alpha * 252,  # 年化Alpha
                    'beta': beta,
                    'tracking_error': np.std(daily_returns - benchmark_returns) * np.sqrt(252)
                })

        return metrics

    def _calculate_drawdown_duration(self, drawdown: pd.Series) -> Dict:
        """计算回撤持续时间"""
        if drawdown.empty:
            return {}

        # 识别回撤期
        in_drawdown = drawdown < 0
        drawdown_periods = []
        current_period_start = None

        for date, in_dd in in_drawdown.items():
            if in_dd and current_period_start is None:
                current_period_start = date
            elif not in_dd and current_period_start is not None:
                drawdown_periods.append((current_period_start, date))
                current_period_start = None

        # 处理未结束的回撤
        if current_period_start is not None:
            drawdown_periods.append((current_period_start, drawdown.index[-1]))

        # 计算回撤持续时间
        if drawdown_periods:
            durations = []
            for start, end in drawdown_periods:
                duration = (end - start).days
                if duration > 0:
                    durations.append(duration)

            if durations:
                return {
                    'max_duration': max(durations),
                    'avg_duration': np.mean(durations),
                    'periods_count': len(durations),
                    'period_details': drawdown_periods
                }

        return {}

    def _calculate_downside_deviation(self, returns: pd.Series, target_return: float = 0) -> float:
        """计算下行偏差"""
        downside_returns = returns[returns < target_return]
        if len(downside_returns) == 0:
            return 0
        return np.sqrt(np.mean((downside_returns - target_return) ** 2)) * np.sqrt(252)

    def _calculate_sharpe_ratio(self, returns: pd.Series, risk_free_rate: float = 0.02) -> float:
        """计算夏普比率"""
        excess_returns = returns - risk_free_rate / 252
        return_ratio = excess_returns.mean() / excess_returns.std() if excess_returns.std() > 0 else 0
        return return_ratio * np.sqrt(252)

    def _calculate_sortino_ratio(self, returns: pd.Series, risk_free_rate: float = 0.02) -> float:
        """计算Sortino比率"""
        excess_returns = returns - risk_free_rate / 252
        downside_returns = excess_returns[excess_returns < 0]
        downside_deviation = np.sqrt(np.mean(downside_returns ** 2)) if len(downside_returns) > 0 else 0
        return_ratio = excess_returns.mean() / downside_deviation if downside_deviation > 0 else 0
        return return_ratio * np.sqrt(252)

    def _perform_attribution_analysis(self, backtest_result: Dict) -> Dict:
        """绩效归因分析"""
        attribution = {
            'sector_attribution': {},
            'factor_attribution': {},
            'timing_attribution': {},
            'selection_attribution': {}
        }

        try:
            # 简单的归因分析实现
            positions = backtest_result.get('positions', pd.DataFrame())
            returns = backtest_result.get('daily_returns', pd.Series())

            if not positions.empty and not returns.empty:
                # 计算行业贡献（假设positions包含行业信息）
                if 'sector' in positions.columns:
                    sector_returns = self._calculate_sector_returns(positions, returns)
                    attribution['sector_attribution'] = sector_returns

                # 计算选股和择时贡献
                attribution['selection_attribution'] = self._calculate_selection_attribution(backtest_result)
                attribution['timing_attribution'] = self._calculate_timing_attribution(backtest_result)

        except Exception as e:
            print(f"❌ 绩效归因分析失败: {e}")

        return attribution

    def _calculate_sector_returns(self, positions: pd.DataFrame, returns: pd.Series) -> Dict:
        """计算行业收益贡献"""
        sector_contributions = {}

        try:
            # 计算每个行业的持仓权重
            sector_weights = positions.groupby('sector')['weight'].mean()
            sector_weights = sector_weights / sector_weights.sum()

            # 估算行业收益（简化实现）
            for sector in sector_weights.index:
                sector_contributions[sector] = {
                    'weight': sector_weights[sector],
                    'contribution': sector_weights[sector] * returns.mean() * 252
                }

        except Exception as e:
            print(f"❌ 计算行业收益贡献失败: {e}")

        return sector_contributions

    def _calculate_selection_attribution(self, backtest_result: Dict) -> float:
        """计算选股能力贡献"""
        # 简化实现，实际需要更复杂的归因模型
        try:
            returns = backtest_result.get('daily_returns', pd.Series())
            benchmark_returns = backtest_result.get('benchmark_returns', pd.Series())

            if not returns.empty and not benchmark_returns.empty:
                # 选股贡献 = 总超额收益 - 择时贡献
                total_excess = returns.mean() - benchmark_returns.mean()
                timing_contribution = self._calculate_timing_attribution(backtest_result)
                return total_excess - timing_contribution.get('timing_contribution', 0)

        except Exception as e:
            print(f"❌ 计算选股能力贡献失败: {e}")

        return 0

    def _calculate_timing_attribution(self, backtest_result: Dict) -> Dict:
        """计算择时能力贡献"""
        # 简化实现
        try:
            returns = backtest_result.get('daily_returns', pd.Series())
            benchmark_returns = backtest_result.get('benchmark_returns', pd.Series())

            if not returns.empty and not benchmark_returns.empty:
                # 使用Henricksson-Merton模型估算择时能力
                up_market = benchmark_returns > 0
                down_market = benchmark_returns <= 0

                up_returns = returns[up_market]
                down_returns = returns[down_market]

                up_market_return = up_returns.mean() if len(up_returns) > 0 else 0
                down_market_return = down_returns.mean() if len(down_returns) > 0 else 0

                benchmark_up_return = benchmark_returns[up_market].mean() if len(up_returns) > 0 else 0
                benchmark_down_return = benchmark_returns[down_market].mean() if len(down_returns) > 0 else 0

                timing_skill = (up_market_return - benchmark_up_return) - (down_market_return - benchmark_down_return)

                return {
                    'timing_contribution': timing_skill,
                    'up_market_outperformance': up_market_return - benchmark_up_return,
                    'down_market_outperformance': down_market_return - benchmark_down_return
                }

        except Exception as e:
            print(f"❌ 计算择时能力贡献失败: {e}")

        return {}

    def _analyze_drawdowns(self, portfolio_value: pd.Series) -> Dict:
        """分析回撤情况"""
        if portfolio_value.empty:
            return {}

        try:
            peak = portfolio_value.cummax()
            drawdown = (portfolio_value - peak) / peak

            # 找出最大回撤期间
            min_drawdown_idx = drawdown.idxmin()
            peak_before_max_drawdown = portfolio_value.loc[:min_drawdown_idx].cummax().idxmax()

            recovery_date = None
            if portfolio_value.loc[min_drawdown_idx:].max() >= portfolio_value.loc[peak_before_max_drawdown]:
                recovery_date = portfolio_value.loc[min_drawdown_idx:][
                    portfolio_value >= portfolio_value.loc[peak_before_max_drawdown]
                ].index[0]

            return {
                'max_drawdown_info': {
                    'max_drawdown': drawdown.min(),
                    'peak_date': peak_before_max_drawdown,
                    'trough_date': min_drawdown_idx,
                    'recovery_date': recovery_date,
                    'duration_days': (min_drawdown_idx - peak_before_max_drawdown).days,
                    'recovery_days': (recovery_date - min_drawdown_idx).days if recovery_date else None
                },
                'drawdown_distribution': self._calculate_drawdown_distribution(drawdown),
                'underwater_plot_data': drawdown.to_dict()
            }

        except Exception as e:
            print(f"❌ 回撤分析失败: {e}")
            return {}

    def _calculate_drawdown_distribution(self, drawdown: pd.Series) -> Dict:
        """计算回撤分布"""
        if drawdown.empty:
            return {}

        # 统计不同回撤幅度的分布
        drawdown_bins = [0, -0.05, -0.1, -0.15, -0.2, -0.3, -0.5, float('-inf')]
        bin_labels = ['0~-5%', '-5~-10%', '-10~-15%', '-15~-20%', '-20~-30%', '-30~-50%', '<-50%']

        # 计算每个区间的天数
        bin_counts = pd.cut(drawdown, bins=drawdown_bins, labels=bin_labels).value_counts()
        bin_percentages = bin_counts / bin_counts.sum()

        return bin_percentages.to_dict()

    def _analyze_transactions(self, transactions: pd.DataFrame) -> Dict:
        """分析交易行为"""
        if transactions.empty:
            return {}

        try:
            # 计算交易频率
            trade_dates = transactions['date'].unique()
            total_days = (transactions['date'].max() - transactions['date'].min()).days
            trading_frequency = len(trade_dates) / total_days if total_days > 0 else 0

            # 计算持仓时间
            if 'holding_period' in transactions.columns:
                avg_holding_period = transactions['holding_period'].mean()
                holding_period_dist = transactions['holding_period'].value_counts().to_dict()
            else:
                avg_holding_period = float('nan')
                holding_period_dist = {}

            # 计算胜率和盈亏比
            profitable_trades = transactions[transactions['profit'] > 0]
            losing_trades = transactions[transactions['profit'] <= 0]

            win_rate = len(profitable_trades) / len(transactions) if len(transactions) > 0 else 0
            avg_profit = profitable_trades['profit'].mean() if len(profitable_trades) > 0 else 0
            avg_loss = abs(losing_trades['profit'].mean()) if len(losing_trades) > 0 else 0
            profit_loss_ratio = avg_profit / avg_loss if avg_loss > 0 else float('inf')

            # 计算交易成本
            if 'cost' in transactions.columns:
                total_cost = transactions['cost'].sum()
                cost_ratio = total_cost / transactions['notional'].sum() if transactions['notional'].sum() > 0 else 0
            else:
                total_cost = float('nan')
                cost_ratio = float('nan')

            return {
                'total_trades': len(transactions),
                'trading_frequency': trading_frequency,
                'average_holding_period': avg_holding_period,
                'holding_period_distribution': holding_period_dist,
                'win_rate': win_rate,
                'profit_loss_ratio': profit_loss_ratio,
                'total_trading_cost': total_cost,
                'cost_ratio': cost_ratio,
                'max_profit_trade': transactions['profit'].max() if 'profit' in transactions.columns else float('nan'),
                'max_loss_trade': transactions['profit'].min() if 'profit' in transactions.columns else float('nan')
            }

        except Exception as e:
            print(f"❌ 交易分析失败: {e}")
            return {}

    def _generate_overview(self, analysis_result: Dict) -> Dict:
        """生成概述信息"""
        try:
            return_metrics = analysis_result.get('return_metrics', {})
            risk_metrics = analysis_result.get('risk_metrics', {})
            risk_adjusted = analysis_result.get('risk_adjusted_metrics', {})

            overview = {
                'total_return': return_metrics.get('total_return', 0),
                'annual_return': return_metrics.get('annual_return', 0),
                'max_drawdown': risk_metrics.get('max_drawdown', 0),
                'sharpe_ratio': risk_adjusted.get('sharpe_ratio', 0),
                'summary': self._generate_performance_summary(analysis_result)
            }

            return overview

        except Exception as e:
            print(f"❌ 生成概述失败: {e}")
            return {}

    def _generate_performance_summary(self, analysis_result: Dict) -> str:
        """生成绩效摘要"""
        try:
            annual_return = analysis_result.get('return_metrics', {}).get('annual_return', 0)
            max_drawdown = analysis_result.get('risk_metrics', {}).get('max_drawdown', 0)
            sharpe_ratio = analysis_result.get('risk_adjusted_metrics', {}).get('sharpe_ratio', 0)

            summary_parts = []

            if annual_return > 0.2:
                summary_parts.append(f"年化收益率 {annual_return:.1%}，表现优秀")
            elif annual_return > 0.1:
                summary_parts.append(f"年化收益率 {annual_return:.1%}，表现良好")
            elif annual_return > 0:
                summary_parts.append(f"年化收益率 {annual_return:.1%}，表现一般")
            else:
                summary_parts.append(f"年化收益率 {annual_return:.1%}，表现不佳")

            if max_drawdown > -0.2:
                summary_parts.append(f"最大回撤 {max_drawdown:.1%}，风险控制良好")
            elif max_drawdown > -0.3:
                summary_parts.append(f"最大回撤 {max_drawdown:.1%}，风险控制一般")
            else:
                summary_parts.append(f"最大回撤 {max_drawdown:.1%}，风险较高")

            if sharpe_ratio > 1.5:
                summary_parts.append(f"夏普比率 {sharpe_ratio:.2f}，风险调整后收益出色")
            elif sharpe_ratio > 1.0:
                summary_parts.append(f"夏普比率 {sharpe_ratio:.2f}，风险调整后收益良好")
            else:
                summary_parts.append(f"夏普比率 {sharpe_ratio:.2f}，风险调整后收益一般")

            return '；'.join(summary_parts) + '。'

        except Exception as e:
            print(f"❌ 生成绩效摘要失败: {e}")
            return ""

    def _generate_conclusion(self, analysis_result: Dict) -> str:
        """生成结论"""
        try:
            sharpe_ratio = analysis_result.get('risk_adjusted_metrics', {}).get('sharpe_ratio', 0)
            max_drawdown = analysis_result.get('risk_metrics', {}).get('max_drawdown', 0)
            annual_return = analysis_result.get('return_metrics', {}).get('annual_return', 0)

            if sharpe_ratio > 1.5 and max_drawdown > -0.2 and annual_return > 0.2:
                return "策略表现优秀，在收益、风险控制和风险调整后收益方面都表现出色，建议考虑实盘应用。"
            elif sharpe_ratio > 1.0 and max_drawdown > -0.3 and annual_return > 0.1:
                return "策略表现良好，在多个维度都有不错的表现，建议进一步优化后考虑实盘应用。"
            elif sharpe_ratio > 0.5 and max_drawdown > -0.4 and annual_return > 0:
                return "策略表现一般，有一定的盈利能力，但风险控制和风险调整后收益还有提升空间。"
            else:
                return "策略表现不佳，未能在风险和收益之间取得良好平衡，建议进行重大改进或重新设计。"

        except Exception as e:
            print(f"❌ 生成结论失败: {e}")
            return ""

    def _generate_suggestions(self, analysis_result: Dict, backtest_result: Dict) -> List[str]:
        """生成改进建议"""
        suggestions = []

        try:
            # 根据不同指标生成建议
            risk_adjusted = analysis_result.get('risk_adjusted_metrics', {})
            risk_metrics = analysis_result.get('risk_metrics', {})
            performance = analysis_result.get('performance_metrics', {})

            # 针对夏普比率的建议
            sharpe_ratio = risk_adjusted.get('sharpe_ratio', 0)
            if sharpe_ratio < 1.0:
                suggestions.append("考虑优化策略以提高夏普比率，可以通过提高收益或降低风险来实现。")

            # 针对最大回撤的建议
            max_drawdown = risk_metrics.get('max_drawdown', 0)
            if max_drawdown < -0.3:
                suggestions.append("最大回撤较大，建议加入止损机制或优化仓位管理策略。")

            # 针对胜率的建议
            win_rate = performance.get('win_rate', 0)
            if win_rate < 0.5:
                suggestions.append("胜率较低，建议优化选股规则或交易时机选择。")

            # 针对盈亏比的建议
            profit_loss_ratio = performance.get('profit_loss_ratio', 0)
            if profit_loss_ratio < 1.5:
                suggestions.append("盈亏比不足，建议设置更严格的止盈止损规则，控制单笔亏损。")

            # 交易成本分析
            transaction_analysis = analysis_result.get('transaction_analysis', {})
            cost_ratio = transaction_analysis.get('cost_ratio', 0)
            if cost_ratio > 0.002:  # 0.2%
                suggestions.append("交易成本较高，建议降低交易频率或寻找更便宜的交易渠道。")

            # 持仓时间分析
            avg_holding_period = transaction_analysis.get('average_holding_period', 0)
            if avg_holding_period < 3:  # 平均持仓小于3天
                suggestions.append("平均持仓时间过短，可能导致较高的交易成本和滑点，建议适当延长持仓时间。")
            elif avg_holding_period > 30:  # 平均持仓大于30天
                suggestions.append("平均持仓时间过长，可能错过短期交易机会，考虑优化退出策略。")

            return suggestions

        except Exception as e:
            print(f"❌ 生成改进建议失败: {e}")
            return suggestions

    def generate_strategy_report(self, backtest_result: Dict, symbol: str = '') -> str:
        """
        生成策略分析报告
        :param backtest_result: 回测结果
        :param symbol: 策略名称
        :return: 文本报告
        """
        analysis_result = self.analyze_strategy_performance(backtest_result)

        report = f"""📊 量化策略绩效分析报告

📋 策略概览
策略名称: {symbol}
分析日期: {datetime.now().strftime('%Y年%m月%d日 %H:%M')}

📈 核心指标摘要
| 指标 | 数值 |
|------|------|
"""

        # 添加核心指标
        core_metrics = [
            ('年化收益率', analysis_result.get('return_metrics', {}).get('annual_return', 0), '{:.2%}'),
            ('总收益率', analysis_result.get('return_metrics', {}).get('total_return', 0), '{:.2%}'),
            ('最大回撤', analysis_result.get('risk_metrics', {}).get('max_drawdown', 0), '{:.2%}'),
            ('夏普比率', analysis_result.get('risk_adjusted_metrics', {}).get('sharpe_ratio', 0), '{:.2f}'),
            ('波动率', analysis_result.get('risk_metrics', {}).get('volatility', 0), '{:.2%}'),
            ('胜率', analysis_result.get('performance_metrics', {}).get('win_rate', 0), '{:.2%}'),
            ('盈亏比', analysis_result.get('performance_metrics', {}).get('profit_loss_ratio', 0), '{:.2f}'),
            ('Alpha', analysis_result.get('timing_metrics', {}).get('alpha', 0), '{:.2%}'),
            ('Beta', analysis_result.get('timing_metrics', {}).get('beta', 0), '{:.2f}'),
        ]

        for name, value, fmt in core_metrics:
            if not pd.isna(value):
                report += f"| {name} | {fmt.format(value)} |\n"

        # 添加结论和建议
        report += f"""

🎯 策略评估结论
{analysis_result.get('conclusion', '')}

💡 改进建议
"""

        suggestions = analysis_result.get('suggestions', [])
        for i, suggestion in enumerate(suggestions, 1):
            report += f"{i}. {suggestion}\n"

        # 添加详细分析
        report += """

📊 详细绩效分析

1️⃣ 收益表现分析
"""

        return_metrics = analysis_result.get('return_metrics', {})
        if return_metrics:
            report += f"- 总收益率: {return_metrics.get('total_return', 0):.2%}\n"
            report += f"- 年化收益率: {return_metrics.get('annual_return', 0):.2%}\n"
            report += f"- 日均收益率: {return_metrics.get('daily_return_mean', 0):.2%}\n"
            report += f"- 上涨天数占比: {return_metrics.get('positive_days_ratio', 0):.2%}\n"
            report += f"- 最佳单日收益: {return_metrics.get('best_day', 0):.2%}\n"
            report += f"- 最差单日收益: {return_metrics.get('worst_day', 0):.2%}\n"

        report += """

2️⃣ 风险特征分析
"""

        risk_metrics = analysis_result.get('risk_metrics', {})
        if risk_metrics:
            report += f"- 年化波动率: {risk_metrics.get('volatility', 0):.2%}\n"
            report += f"- 最大回撤: {risk_metrics.get('max_drawdown', 0):.2%}\n"
            report += f"- 最大回撤持续天数: {risk_metrics.get('max_drawdown_duration', 0)}天\n"
            report += f"- 95% VaR: {risk_metrics.get('var_95', 0):.2%}\n"
            report += f"- 95% CVaR: {risk_metrics.get('cvar_95', 0):.2%}\n"

        report += """

3️⃣ 风险调整后收益分析
"""

        risk_adjusted = analysis_result.get('risk_adjusted_metrics', {})
        if risk_adjusted:
            report += f"- 夏普比率: {risk_adjusted.get('sharpe_ratio', 0):.2f}\n"
            report += f"- Sortino比率: {risk_adjusted.get('sortino_ratio', 0):.2f}\n"
            report += f"- Calmar比率: {risk_adjusted.get('calmar_ratio', 0):.2f}\n"
            if 'information_ratio' in risk_adjusted:
                report += f"- 信息比率: {risk_adjusted.get('information_ratio', 0):.2f}\n"

        return report

if __name__ == "__main__":
    # 测试代码
    analyzer = StrategyAnalyzer()

    # 创建模拟回测结果
    np.random.seed(42)
    dates = pd.date_range('2021-01-01', '2022-12-31', freq='B')
    daily_returns = np.random.normal(0.0005, 0.01, len(dates))
    portfolio_value = (1 + daily_returns).cumprod() * 1000000

    backtest_result = {
        'portfolio_value': portfolio_value,
        'daily_returns': pd.Series(daily_returns, index=dates),
        'benchmark_returns': pd.Series(np.random.normal(0.0003, 0.008, len(dates)), index=dates),
        'transactions': pd.DataFrame({
            'date': dates[:100],
            'symbol': ['000001'] * 100,
            'side': ['buy'] * 50 + ['sell'] * 50,
            'price': np.random.uniform(10, 20, 100),
            'quantity': np.random.randint(100, 1000, 100),
            'profit': np.random.normal(100, 500, 100),
            'cost': np.random.uniform(10, 50, 100)
        })
    }

    # 分析策略
    analysis_result = analyzer.analyze_strategy_performance(backtest_result)
    report = analyzer.generate_strategy_report(backtest_result, '测试策略')

    print(report)

    # 保存报告
    with open('strategy_analysis_report.txt', 'w', encoding='utf-8') as f:
        f.write(report)
    print("\n📝 分析报告已保存到strategy_analysis_report.txt")