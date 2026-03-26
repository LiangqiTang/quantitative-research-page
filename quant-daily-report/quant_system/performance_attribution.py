"""
业绩归因模块 - Brinson归因和因子归因

提供专业的业绩归因分析：
- Brinson归因（BF模型）：资产配置、个股选择、交互收益
- 因子归因：分解收益到各个风险因子
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass


@dataclass
class BrinsonAttributionResult:
    """Brinson归因结果"""
    allocation_return: float
    selection_return: float
    interaction_return: float
    total_excess_return: float
    industry_details: pd.DataFrame
    period: Optional[str] = None


@dataclass
class FactorAttributionResult:
    """因子归因结果"""
    factor_contributions: pd.Series
    specific_contribution: float
    total_return: float
    period: Optional[str] = None


class BrinsonAttribution:
    """
    Brinson业绩归因（BF模型）

    将超额收益分解为三个部分：
    1. 资产配置收益（Allocation）：超配/低配行业带来的收益
    2. 个股选择收益（Selection）：行业内选股带来的收益
    3. 交互收益（Interaction）：配置和选择的交叉影响
    """

    def __init__(
        self,
        portfolio_weights: pd.Series,
        benchmark_weights: pd.Series,
        stock_returns: pd.Series,
        industry_classification: Optional[pd.Series] = None
    ):
        """
        初始化Brinson归因

        Args:
            portfolio_weights: 组合权重（股票 -> 权重）
            benchmark_weights: 基准权重（股票 -> 权重）
            stock_returns: 股票收益率（股票 -> 收益率）
            industry_classification: 行业分类（股票 -> 行业名称，可选）
        """
        self.portfolio_weights = portfolio_weights
        self.benchmark_weights = benchmark_weights
        self.stock_returns = stock_returns
        self.industry_classification = industry_classification

        # 对齐索引
        common_stocks = portfolio_weights.index.intersection(
            benchmark_weights.index
        ).intersection(stock_returns.index)

        self.portfolio_weights = portfolio_weights.loc[common_stocks]
        self.benchmark_weights = benchmark_weights.loc[common_stocks]
        self.stock_returns = stock_returns.loc[common_stocks]

    def _calculate_industry_returns(self) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        计算行业层面的收益率和权重

        Returns:
            (组合行业权重, 基准行业权重, 行业收益率)
        """
        if self.industry_classification is None:
            # 如果没有行业分类，所有股票视为同一行业
            port_ind_weight = pd.Series({'all': self.portfolio_weights.sum()})
            bench_ind_weight = pd.Series({'all': self.benchmark_weights.sum()})
            ind_return = pd.Series({'all': self.stock_returns.mean()})
            return port_ind_weight, bench_ind_weight, ind_return

        # 按行业分组
        data = pd.DataFrame({
            'port_weight': self.portfolio_weights,
            'bench_weight': self.benchmark_weights,
            'return': self.stock_returns,
            'industry': self.industry_classification
        })

        # 计算行业权重
        port_ind_weight = data.groupby('industry')['port_weight'].sum()
        bench_ind_weight = data.groupby('industry')['bench_weight'].sum()

        # 计算行业收益率（基准权重加权）
        data['bench_weighted_return'] = data['bench_weight'] * data['return']
        ind_return = data.groupby('industry').apply(
            lambda x: x['bench_weighted_return'].sum() / x['bench_weight'].sum()
            if x['bench_weight'].sum() > 0 else 0
        )

        return port_ind_weight, bench_ind_weight, ind_return

    def _calculate_stock_selection_within_industry(self) -> pd.Series:
        """
        计算各行业内的个股选择收益

        Returns:
            行业 -> 选择收益的Series
        """
        if self.industry_classification is None:
            # 单行业情况
            port_return = (self.portfolio_weights * self.stock_returns).sum()
            bench_return = (self.benchmark_weights * self.stock_returns).sum()
            return pd.Series({'all': port_return - bench_return})

        # 按行业分组计算
        data = pd.DataFrame({
            'port_weight': self.portfolio_weights,
            'bench_weight': self.benchmark_weights,
            'return': self.stock_returns,
            'industry': self.industry_classification
        })

        def calc_selection(group):
            port_contrib = (group['port_weight'] * group['return']).sum()
            bench_contrib = (group['bench_weight'] * group['return']).sum()
            return port_contrib - bench_contrib

        selection_by_industry = data.groupby('industry').apply(calc_selection)
        return selection_by_industry

    def calculate_attribution(self, period: Optional[str] = None) -> BrinsonAttributionResult:
        """
        计算Brinson归因（BF模型）

        Args:
            period: 时期标签（可选）

        Returns:
            BrinsonAttributionResult: 归因结果
        """
        # 计算行业层面数据
        port_ind_weight, bench_ind_weight, ind_return = self._calculate_industry_returns()

        # 计算组合和基准总收益
        portfolio_return = (self.portfolio_weights * self.stock_returns).sum()
        benchmark_return = (self.benchmark_weights * self.stock_returns).sum()
        total_excess = portfolio_return - benchmark_return

        # 1. 资产配置收益
        # 超配行业 * 行业收益率 - 基准行业权重 * 行业收益率
        # 这里用：(w_p_i - w_b_i) * r_b_i
        allocation_return = ((port_ind_weight - bench_ind_weight) * ind_return).sum()

        # 2. 个股选择收益
        # 在行业内部，(w_p_i - w_b_i) * (r_p_i - r_b_i) ?
        # 或者更简单：w_b_i * (r_p_i - r_b_i)
        # 这里用BF模型：w_b_i * (r_p_i - r_b_i)
        # 即：用基准权重，乘以组合选股相对于行业的超额
        # 先计算行业内选择收益
        selection_by_industry = self._calculate_stock_selection_within_industry()

        # 但更标准的BF模型是：
        # Selection = sum_i [ w_b_i * (r_p_i - r_b_i) ]
        # 其中r_p_i是组合在行业i内的收益率，r_b_i是行业i的收益率

        # 重新计算行业内组合收益率
        if self.industry_classification is not None:
            data = pd.DataFrame({
                'port_weight': self.portfolio_weights,
                'return': self.stock_returns,
                'industry': self.industry_classification
            })

            # 行业内组合收益率
            def calc_port_return(group):
                total_weight = group['port_weight'].sum()
                if total_weight <= 0:
                    return 0
                return (group['port_weight'] * group['return']).sum() / total_weight

            port_ind_return = data.groupby('industry').apply(calc_port_return)

            # 计算选择收益：bench_weight * (port_ind_return - ind_return)
            selection_return = (bench_ind_weight * (port_ind_return - ind_return)).sum()

            # 3. 交互收益：(w_p_i - w_b_i) * (r_p_i - r_b_i)
            interaction_return = ((port_ind_weight - bench_ind_weight) *
                                  (port_ind_return - ind_return)).sum()
        else:
            # 单行业情况
            selection_return = selection_by_industry.iloc[0] if not selection_by_industry.empty else 0
            interaction_return = 0

        # 构建行业详情
        industry_details = []
        for industry in port_ind_weight.index:
            w_p = port_ind_weight.get(industry, 0)
            w_b = bench_ind_weight.get(industry, 0)
            r_i = ind_return.get(industry, 0)

            if self.industry_classification is not None:
                r_p = port_ind_return.get(industry, 0) if 'port_ind_return' in locals() else r_i
            else:
                r_p = r_i

            alloc = (w_p - w_b) * r_i
            select = w_b * (r_p - r_i) if 'port_ind_return' in locals() else 0
            interact = (w_p - w_b) * (r_p - r_i) if 'port_ind_return' in locals() else 0

            industry_details.append({
                'industry': industry,
                'portfolio_weight': w_p,
                'benchmark_weight': w_b,
                'weight_diff': w_p - w_b,
                'industry_return': r_i,
                'portfolio_industry_return': r_p,
                'allocation': alloc,
                'selection': select,
                'interaction': interact,
                'total': alloc + select + interact
            })

        industry_details_df = pd.DataFrame(industry_details)
        if not industry_details_df.empty:
            industry_details_df = industry_details_df.set_index('industry')

        return BrinsonAttributionResult(
            allocation_return=float(allocation_return),
            selection_return=float(selection_return),
            interaction_return=float(interaction_return),
            total_excess_return=float(total_excess),
            industry_details=industry_details_df,
            period=period
        )


class FactorAttribution:
    """
    因子归因

    将组合收益分解为各个风险因子的贡献和特异性贡献
    """

    def __init__(
        self,
        factor_exposures: pd.DataFrame,
        factor_returns: pd.Series,
        specific_returns: Optional[pd.Series] = None,
        portfolio_weights: Optional[pd.Series] = None
    ):
        """
        初始化因子归因

        Args:
            factor_exposures: 因子暴露（股票 x 因子）
            factor_returns: 因子收益率（因子 -> 收益率）
            specific_returns: 特异性收益率（股票 -> 收益率，可选）
            portfolio_weights: 组合权重（股票 -> 权重，可选）
        """
        self.factor_exposures = factor_exposures
        self.factor_returns = factor_returns
        self.specific_returns = specific_returns
        self.portfolio_weights = portfolio_weights

        # 对齐因子
        common_factors = factor_exposures.columns.intersection(factor_returns.index)
        self.factor_exposures = factor_exposures[common_factors]
        self.factor_returns = factor_returns.loc[common_factors]

        # 对齐股票
        if portfolio_weights is not None:
            common_stocks = factor_exposures.index.intersection(portfolio_weights.index)
            self.factor_exposures = self.factor_exposures.loc[common_stocks]
            self.portfolio_weights = portfolio_weights.loc[common_stocks]

            if specific_returns is not None:
                self.specific_returns = specific_returns.loc[common_stocks]

    def calculate_factor_attribution(self, period: Optional[str] = None) -> FactorAttributionResult:
        """
        计算因子归因

        Returns:
            FactorAttributionResult: 归因结果
        """
        # 获取权重
        if self.portfolio_weights is not None:
            weights = self.portfolio_weights.values
        else:
            # 等权重
            weights = np.ones(len(self.factor_exposures)) / len(self.factor_exposures)

        # 计算组合因子暴露
        portfolio_exposures = self.factor_exposures.T @ weights

        # 计算因子贡献：暴露 * 因子收益
        factor_contrib = portfolio_exposures * self.factor_returns

        # 计算特异性贡献
        specific_contrib = 0.0
        if self.specific_returns is not None:
            specific_contrib = float((self.specific_returns * weights).sum())

        # 计算总收益
        total_return = factor_contrib.sum() + specific_contrib

        return FactorAttributionResult(
            factor_contributions=factor_contrib,
            specific_contribution=specific_contrib,
            total_return=float(total_return),
            period=period
        )

    def calculate_stock_level_attribution(self) -> pd.DataFrame:
        """
        计算股票层面的归因分解

        Returns:
            股票 x (因子贡献, 特异贡献, 总贡献) 的DataFrame
        """
        # 计算每只股票的因子贡献
        stock_factor_contrib = self.factor_exposures.multiply(self.factor_returns, axis=1)

        # 汇总每只股票的总因子贡献
        stock_total_factor_contrib = stock_factor_contrib.sum(axis=1)

        # 构建结果
        result = pd.DataFrame({
            'factor_contribution': stock_total_factor_contrib
        })

        if self.specific_returns is not None:
            result['specific_contribution'] = self.specific_returns
            result['total_contribution'] = result['factor_contribution'] + result['specific_contribution']

        return result


class MultiPeriodAttribution:
    """
    多期归因分析

    支持时间序列的归因分析
    """

    def __init__(self):
        self.period_results: List[Any] = []

    def add_period_result(self, result: Any):
        """
        添加一期结果

        Args:
            result: BrinsonAttributionResult或FactorAttributionResult
        """
        self.period_results.append(result)

    def aggregate_brinson(self) -> Dict[str, Any]:
        """
        聚合多期Brinson归因结果

        Returns:
            聚合结果字典
        """
        if not self.period_results:
            return {}

        # 检查结果类型
        if not all(isinstance(r, BrinsonAttributionResult) for r in self.period_results):
            raise ValueError("All results must be BrinsonAttributionResult")

        # 聚合
        total_alloc = sum(r.allocation_return for r in self.period_results)
        total_select = sum(r.selection_return for r in self.period_results)
        total_interact = sum(r.interaction_return for r in self.period_results)
        total_excess = sum(r.total_excess_return for r in self.period_results)

        # 时间序列
        ts_data = []
        for r in self.period_results:
            ts_data.append({
                'period': r.period,
                'allocation': r.allocation_return,
                'selection': r.selection_return,
                'interaction': r.interaction_return,
                'total_excess': r.total_excess_return
            })
        ts_df = pd.DataFrame(ts_data)
        if not ts_df.empty and 'period' in ts_df.columns:
            ts_df = ts_df.set_index('period')

        return {
            'total_allocation': total_alloc,
            'total_selection': total_select,
            'total_interaction': total_interact,
            'total_excess_return': total_excess,
            'time_series': ts_df
        }

    def aggregate_factor(self) -> Dict[str, Any]:
        """
        聚合多期因子归因结果

        Returns:
            聚合结果字典
        """
        if not self.period_results:
            return {}

        # 检查结果类型
        if not all(isinstance(r, FactorAttributionResult) for r in self.period_results):
            raise ValueError("All results must be FactorAttributionResult")

        # 聚合因子贡献
        all_factors = set()
        for r in self.period_results:
            all_factors.update(r.factor_contributions.index)

        total_factor_contrib = pd.Series(0.0, index=list(all_factors))
        total_specific = 0.0

        for r in self.period_results:
            total_factor_contrib = total_factor_contrib.add(r.factor_contributions, fill_value=0)
            total_specific += r.specific_contribution

        # 时间序列
        ts_data = []
        for r in self.period_results:
            row = {'period': r.period, 'specific': r.specific_contribution}
            row.update(r.factor_contributions.to_dict())
            ts_data.append(row)
        ts_df = pd.DataFrame(ts_data)
        if not ts_df.empty and 'period' in ts_df.columns:
            ts_df = ts_df.set_index('period')

        return {
            'factor_contributions': total_factor_contrib,
            'specific_contribution': total_specific,
            'total_return': total_factor_contrib.sum() + total_specific,
            'time_series': ts_df
        }


def calculate_brinson_attribution(
    portfolio_weights: pd.Series,
    benchmark_weights: pd.Series,
    stock_returns: pd.Series,
    industry_classification: Optional[pd.Series] = None,
    period: Optional[str] = None
) -> BrinsonAttributionResult:
    """
    便捷函数：计算Brinson归因

    Args:
        portfolio_weights: 组合权重
        benchmark_weights: 基准权重
        stock_returns: 股票收益率
        industry_classification: 行业分类（可选）
        period: 时期标签（可选）

    Returns:
        BrinsonAttributionResult: 归因结果
    """
    attribution = BrinsonAttribution(
        portfolio_weights=portfolio_weights,
        benchmark_weights=benchmark_weights,
        stock_returns=stock_returns,
        industry_classification=industry_classification
    )
    return attribution.calculate_attribution(period=period)


def calculate_factor_attribution(
    factor_exposures: pd.DataFrame,
    factor_returns: pd.Series,
    specific_returns: Optional[pd.Series] = None,
    portfolio_weights: Optional[pd.Series] = None,
    period: Optional[str] = None
) -> FactorAttributionResult:
    """
    便捷函数：计算因子归因

    Args:
        factor_exposures: 因子暴露
        factor_returns: 因子收益率
        specific_returns: 特异性收益率（可选）
        portfolio_weights: 组合权重（可选）
        period: 时期标签（可选）

    Returns:
        FactorAttributionResult: 归因结果
    """
    attribution = FactorAttribution(
        factor_exposures=factor_exposures,
        factor_returns=factor_returns,
        specific_returns=specific_returns,
        portfolio_weights=portfolio_weights
    )
    return attribution.calculate_factor_attribution(period=period)
