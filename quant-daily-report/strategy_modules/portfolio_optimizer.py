"""
组合优化模块 - 专业的投资组合优化方法

提供多种经典和现代的组合优化算法：
- 最小方差组合 (Minimum Variance)
- 最大夏普比率组合 (Maximum Sharpe Ratio)
- 风险平价组合 (Risk Parity)
- 最大分散化组合 (Most Diversified Portfolio, MDP)
- 均值方差优化 (Mean-Variance Optimization)
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import warnings

try:
    from scipy.optimize import minimize
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False
    warnings.warn("scipy not available, some optimization methods will not work")


class OptimizationMethod(Enum):
    """优化方法枚举"""
    MIN_VARIANCE = "min_variance"
    MAX_SHARPE = "max_sharpe"
    RISK_PARITY = "risk_parity"
    MOST_DIVERSIFIED = "most_diversified"
    MEAN_VARIANCE = "mean_variance"
    EQUAL_WEIGHT = "equal_weight"


@dataclass
class OptimizationResult:
    """优化结果"""
    method: OptimizationMethod
    weights: pd.Series
    expected_return: float
    expected_volatility: float
    sharpe_ratio: float
    diversification_ratio: Optional[float] = None
    risk_contributions: Optional[pd.Series] = None
    success: bool = True
    message: str = "Optimization successful"


class PortfolioOptimizer:
    """
    组合优化器

    提供多种专业的投资组合优化方法
    """

    def __init__(
        self,
        returns: pd.DataFrame,
        expected_returns: Optional[pd.Series] = None,
        risk_free_rate: float = 0.03,
        frequency: int = 252
    ):
        """
        初始化组合优化器

        Args:
            returns: 收益率数据框 (日期 x 资产)
            expected_returns: 预期收益率序列 (资产 -> 收益率)
            risk_free_rate: 无风险利率
            frequency: 年化频率 (日频: 252, 周频: 52, 月频: 12)
        """
        self.returns = returns
        self.expected_returns = expected_returns
        self.risk_free_rate = risk_free_rate
        self.frequency = frequency

        # 计算协方差矩阵
        self.cov_matrix = returns.cov() * frequency
        self.asset_names = returns.columns.tolist()
        self.n_assets = len(self.asset_names)

        # 计算资产波动率
        self.asset_vols = pd.Series(
            np.sqrt(np.diag(self.cov_matrix)),
            index=self.asset_names
        )

        # 如果没有提供预期收益，使用历史平均
        if expected_returns is None:
            self.expected_returns = returns.mean() * frequency
        else:
            self.expected_returns = expected_returns

    def _calculate_portfolio_stats(
        self,
        weights: np.ndarray
    ) -> Tuple[float, float, float]:
        """
        计算组合统计指标

        Args:
            weights: 权重数组

        Returns:
            (组合收益, 组合波动率, 夏普比率)
        """
        weights = weights.flatten()

        # 组合预期收益
        port_return = float(weights @ self.expected_returns.values)

        # 组合波动率
        port_vol = float(np.sqrt(weights @ self.cov_matrix.values @ weights))

        # 夏普比率
        sharpe = (port_return - self.risk_free_rate) / port_vol if port_vol > 0 else 0

        return port_return, port_vol, sharpe

    def _calculate_risk_contributions(
        self,
        weights: np.ndarray
    ) -> pd.Series:
        """
        计算各资产对组合的风险贡献

        Args:
            weights: 权重数组

        Returns:
            风险贡献序列
        """
        weights = weights.flatten()
        marginal_risk = self.cov_matrix.values @ weights
        total_risk = np.sqrt(weights @ marginal_risk)

        if total_risk <= 0:
            return pd.Series(0, index=self.asset_names)

        risk_contrib = (weights * marginal_risk) / total_risk
        return pd.Series(risk_contrib, index=self.asset_names)

    def _calculate_diversification_ratio(
        self,
        weights: np.ndarray
    ) -> float:
        """
        计算分散化比率

        分散化比率 = 加权平均波动率 / 组合波动率
        越高表示分散化效果越好

        Args:
            weights: 权重数组

        Returns:
            分散化比率
        """
        weights = weights.flatten()
        weighted_vol = float(weights @ self.asset_vols.values)
        port_vol = float(np.sqrt(weights @ self.cov_matrix.values @ weights))

        return weighted_vol / port_vol if port_vol > 0 else 1.0

    def optimize_min_variance(
        self,
        bounds: Tuple[float, float] = (0.0, 1.0),
        min_weight: float = 0.0,
        max_weight: float = 1.0
    ) -> OptimizationResult:
        """
        最小方差组合优化

        目标：在权重和为1的约束下，最小化组合方差

        Args:
            bounds: 权重边界 (min, max)
            min_weight: 单个资产最小权重
            max_weight: 单个资产最大权重

        Returns:
            OptimizationResult: 优化结果
        """
        if not SCIPY_AVAILABLE:
            return self._equal_weight_fallback("min_variance")

        # 目标函数：最小化组合方差
        def objective(weights):
            return weights @ self.cov_matrix.values @ weights

        # 约束：权重和为1
        constraints = [
            {'type': 'eq', 'fun': lambda w: np.sum(w) - 1.0}
        ]

        # 边界
        bounds_list = [(min_weight, max_weight) for _ in range(self.n_assets)]

        # 初始猜测：等权重
        x0 = np.ones(self.n_assets) / self.n_assets

        # 优化
        result = minimize(
            objective,
            x0,
            method='SLSQP',
            bounds=bounds_list,
            constraints=constraints,
            options={'maxiter': 1000}
        )

        if result.success:
            weights = pd.Series(result.x, index=self.asset_names)
            port_return, port_vol, sharpe = self._calculate_portfolio_stats(result.x)
            div_ratio = self._calculate_diversification_ratio(result.x)
            risk_contrib = self._calculate_risk_contributions(result.x)

            return OptimizationResult(
                method=OptimizationMethod.MIN_VARIANCE,
                weights=weights,
                expected_return=port_return,
                expected_volatility=port_vol,
                sharpe_ratio=sharpe,
                diversification_ratio=div_ratio,
                risk_contributions=risk_contrib,
                success=True,
                message="Minimum variance optimization successful"
            )
        else:
            return self._equal_weight_fallback("min_variance", result.message)

    def optimize_max_sharpe(
        self,
        min_weight: float = 0.0,
        max_weight: float = 1.0
    ) -> OptimizationResult:
        """
        最大夏普比率组合优化

        目标：最大化夏普比率 (组合收益 - 无风险利率) / 组合波动率

        Args:
            min_weight: 单个资产最小权重
            max_weight: 单个资产最大权重

        Returns:
            OptimizationResult: 优化结果
        """
        if not SCIPY_AVAILABLE:
            return self._equal_weight_fallback("max_sharpe")

        # 目标函数：负的夏普比率（因为我们要最小化）
        def objective(weights):
            port_return = weights @ self.expected_returns.values
            port_vol = np.sqrt(weights @ self.cov_matrix.values @ weights)
            sharpe = (port_return - self.risk_free_rate) / port_vol if port_vol > 0 else -1000
            return -sharpe

        # 约束：权重和为1
        constraints = [
            {'type': 'eq', 'fun': lambda w: np.sum(w) - 1.0}
        ]

        # 边界
        bounds_list = [(min_weight, max_weight) for _ in range(self.n_assets)]

        # 初始猜测：等权重
        x0 = np.ones(self.n_assets) / self.n_assets

        # 优化
        result = minimize(
            objective,
            x0,
            method='SLSQP',
            bounds=bounds_list,
            constraints=constraints,
            options={'maxiter': 1000}
        )

        if result.success:
            weights = pd.Series(result.x, index=self.asset_names)
            port_return, port_vol, sharpe = self._calculate_portfolio_stats(result.x)
            div_ratio = self._calculate_diversification_ratio(result.x)
            risk_contrib = self._calculate_risk_contributions(result.x)

            return OptimizationResult(
                method=OptimizationMethod.MAX_SHARPE,
                weights=weights,
                expected_return=port_return,
                expected_volatility=port_vol,
                sharpe_ratio=sharpe,
                diversification_ratio=div_ratio,
                risk_contributions=risk_contrib,
                success=True,
                message="Maximum Sharpe ratio optimization successful"
            )
        else:
            return self._equal_weight_fallback("max_sharpe", result.message)

    def optimize_risk_parity(
        self,
        min_weight: float = 0.0001,
        max_weight: float = 0.5
    ) -> OptimizationResult:
        """
        风险平价组合优化

        目标：使每个资产对组合的风险贡献相等

        Args:
            min_weight: 单个资产最小权重
            max_weight: 单个资产最大权重

        Returns:
            OptimizationResult: 优化结果
        """
        if not SCIPY_AVAILABLE:
            return self._equal_weight_fallback("risk_parity")

        # 目标函数：最小化风险贡献的差异
        def objective(weights):
            weights = weights.flatten()
            marginal_risk = self.cov_matrix.values @ weights
            total_risk = np.sqrt(weights @ marginal_risk)

            if total_risk <= 0:
                return 1e10

            risk_contrib = (weights * marginal_risk) / total_risk
            target_risk = 1.0 / len(weights)

            # 最小化风险贡献与目标的平方误差和
            return float(np.sum((risk_contrib - target_risk) ** 2))

        # 约束：权重和为1
        constraints = [
            {'type': 'eq', 'fun': lambda w: np.sum(w) - 1.0}
        ]

        # 边界
        bounds_list = [(min_weight, max_weight) for _ in range(self.n_assets)]

        # 初始猜测：按波动率倒数加权
        vol_inv = 1.0 / (self.asset_vols.values + 1e-10)
        x0 = vol_inv / np.sum(vol_inv)

        # 优化
        result = minimize(
            objective,
            x0,
            method='SLSQP',
            bounds=bounds_list,
            constraints=constraints,
            options={'maxiter': 1000}
        )

        if result.success:
            weights = pd.Series(result.x, index=self.asset_names)
            port_return, port_vol, sharpe = self._calculate_portfolio_stats(result.x)
            div_ratio = self._calculate_diversification_ratio(result.x)
            risk_contrib = self._calculate_risk_contributions(result.x)

            return OptimizationResult(
                method=OptimizationMethod.RISK_PARITY,
                weights=weights,
                expected_return=port_return,
                expected_volatility=port_vol,
                sharpe_ratio=sharpe,
                diversification_ratio=div_ratio,
                risk_contributions=risk_contrib,
                success=True,
                message="Risk parity optimization successful"
            )
        else:
            return self._equal_weight_fallback("risk_parity", result.message)

    def optimize_most_diversified(
        self,
        min_weight: float = 0.0,
        max_weight: float = 1.0
    ) -> OptimizationResult:
        """
        最大分散化组合优化

        目标：最大化分散化比率 = 加权平均波动率 / 组合波动率

        Args:
            min_weight: 单个资产最小权重
            max_weight: 单个资产最大权重

        Returns:
            OptimizationResult: 优化结果
        """
        if not SCIPY_AVAILABLE:
            return self._equal_weight_fallback("most_diversified")

        # 目标函数：负的分散化比率（因为我们要最小化）
        def objective(weights):
            weighted_vol = weights @ self.asset_vols.values
            port_vol = np.sqrt(weights @ self.cov_matrix.values @ weights)
            diversification_ratio = weighted_vol / port_vol if port_vol > 0 else 1.0
            return -diversification_ratio

        # 约束：权重和为1
        constraints = [
            {'type': 'eq', 'fun': lambda w: np.sum(w) - 1.0}
        ]

        # 边界
        bounds_list = [(min_weight, max_weight) for _ in range(self.n_assets)]

        # 初始猜测：等权重
        x0 = np.ones(self.n_assets) / self.n_assets

        # 优化
        result = minimize(
            objective,
            x0,
            method='SLSQP',
            bounds=bounds_list,
            constraints=constraints,
            options={'maxiter': 1000}
        )

        if result.success:
            weights = pd.Series(result.x, index=self.asset_names)
            port_return, port_vol, sharpe = self._calculate_portfolio_stats(result.x)
            div_ratio = self._calculate_diversification_ratio(result.x)
            risk_contrib = self._calculate_risk_contributions(result.x)

            return OptimizationResult(
                method=OptimizationMethod.MOST_DIVERSIFIED,
                weights=weights,
                expected_return=port_return,
                expected_volatility=port_vol,
                sharpe_ratio=sharpe,
                diversification_ratio=div_ratio,
                risk_contributions=risk_contrib,
                success=True,
                message="Most diversified portfolio optimization successful"
            )
        else:
            return self._equal_weight_fallback("most_diversified", result.message)

    def optimize_mean_variance(
        self,
        target_return: Optional[float] = None,
        risk_aversion: float = 1.0,
        min_weight: float = 0.0,
        max_weight: float = 1.0
    ) -> OptimizationResult:
        """
        均值方差优化 (Markowitz)

        可以有两种模式：
        1. 指定目标收益：在满足目标收益下最小化风险
        2. 不指定目标收益：最大化效用函数 = 收益 - λ * 方差

        Args:
            target_return: 目标年化收益率（可选）
            risk_aversion: 风险厌恶系数 λ
            min_weight: 单个资产最小权重
            max_weight: 单个资产最大权重

        Returns:
            OptimizationResult: 优化结果
        """
        if not SCIPY_AVAILABLE:
            return self._equal_weight_fallback("mean_variance")

        # 构建约束
        constraints = [{'type': 'eq', 'fun': lambda w: np.sum(w) - 1.0}]

        if target_return is not None:
            # 模式1：指定目标收益，最小化方差
            constraints.append({
                'type': 'eq',
                'fun': lambda w: w @ self.expected_returns.values - target_return
            })

            def objective(weights):
                return weights @ self.cov_matrix.values @ weights
        else:
            # 模式2：最大化效用函数
            def objective(weights):
                port_return = weights @ self.expected_returns.values
                port_var = weights @ self.cov_matrix.values @ weights
                utility = port_return - risk_aversion * port_var
                return -utility

        # 边界
        bounds_list = [(min_weight, max_weight) for _ in range(self.n_assets)]

        # 初始猜测：等权重
        x0 = np.ones(self.n_assets) / self.n_assets

        # 优化
        result = minimize(
            objective,
            x0,
            method='SLSQP',
            bounds=bounds_list,
            constraints=constraints,
            options={'maxiter': 1000}
        )

        if result.success:
            weights = pd.Series(result.x, index=self.asset_names)
            port_return, port_vol, sharpe = self._calculate_portfolio_stats(result.x)
            div_ratio = self._calculate_diversification_ratio(result.x)
            risk_contrib = self._calculate_risk_contributions(result.x)

            return OptimizationResult(
                method=OptimizationMethod.MEAN_VARIANCE,
                weights=weights,
                expected_return=port_return,
                expected_volatility=port_vol,
                sharpe_ratio=sharpe,
                diversification_ratio=div_ratio,
                risk_contributions=risk_contrib,
                success=True,
                message="Mean-variance optimization successful"
            )
        else:
            return self._equal_weight_fallback("mean_variance", result.message)

    def optimize_equal_weight(self) -> OptimizationResult:
        """
        等权重组合

        Returns:
            OptimizationResult: 等权重结果
        """
        weights = pd.Series(1.0 / self.n_assets, index=self.asset_names)
        port_return, port_vol, sharpe = self._calculate_portfolio_stats(weights.values)
        div_ratio = self._calculate_diversification_ratio(weights.values)
        risk_contrib = self._calculate_risk_contributions(weights.values)

        return OptimizationResult(
            method=OptimizationMethod.EQUAL_WEIGHT,
            weights=weights,
            expected_return=port_return,
            expected_volatility=port_vol,
            sharpe_ratio=sharpe,
            diversification_ratio=div_ratio,
            risk_contributions=risk_contrib,
            success=True,
            message="Equal weight allocation"
        )

    def _equal_weight_fallback(
        self,
        method_name: str,
        message: str = "Fallback to equal weight"
    ) -> OptimizationResult:
        """
        优化失败时回退到等权重

        Args:
            method_name: 原始优化方法名称
            message: 失败消息

        Returns:
            OptimizationResult: 等权重结果
        """
        result = self.optimize_equal_weight()
        result.success = False
        result.message = f"{method_name} failed: {message}, using equal weight"
        return result

    def optimize_all(
        self,
        min_weight: float = 0.0,
        max_weight: float = 1.0
    ) -> Dict[OptimizationMethod, OptimizationResult]:
        """
        运行所有优化方法并返回结果对比

        Args:
            min_weight: 单个资产最小权重
            max_weight: 单个资产最大权重

        Returns:
            优化结果字典
        """
        results = {}

        # 等权重（基准）
        results[OptimizationMethod.EQUAL_WEIGHT] = self.optimize_equal_weight()

        # 最小方差
        results[OptimizationMethod.MIN_VARIANCE] = self.optimize_min_variance(
            min_weight=min_weight, max_weight=max_weight
        )

        # 最大夏普
        results[OptimizationMethod.MAX_SHARPE] = self.optimize_max_sharpe(
            min_weight=min_weight, max_weight=max_weight
        )

        # 风险平价
        results[OptimizationMethod.RISK_PARITY] = self.optimize_risk_parity(
            min_weight=max(0.0001, min_weight),
            max_weight=max_weight
        )

        # 最大分散化
        results[OptimizationMethod.MOST_DIVERSIFIED] = self.optimize_most_diversified(
            min_weight=min_weight, max_weight=max_weight
        )

        return results

    def get_efficient_frontier(
        self,
        n_points: int = 50,
        min_weight: float = 0.0,
        max_weight: float = 1.0
    ) -> pd.DataFrame:
        """
        计算有效前沿

        Args:
            n_points: 有效前沿上的点数
            min_weight: 单个资产最小权重
            max_weight: 单个资产最大权重

        Returns:
            包含收益和波动率的DataFrame
        """
        if not SCIPY_AVAILABLE:
            return pd.DataFrame()

        # 获取最小方差和最大收益
        min_var_result = self.optimize_min_variance(
            min_weight=min_weight, max_weight=max_weight
        )
        min_return = min_var_result.expected_return

        # 最大收益（只持有预期收益最高的资产）
        max_return = self.expected_returns.max()

        # 在最小和最大收益之间生成点
        target_returns = np.linspace(min_return, max_return, n_points)

        frontier_points = []
        for target in target_returns:
            result = self.optimize_mean_variance(
                target_return=target,
                min_weight=min_weight,
                max_weight=max_weight
            )
            if result.success:
                frontier_points.append({
                    'return': result.expected_return,
                    'volatility': result.expected_volatility,
                    'sharpe': result.sharpe_ratio
                })

        return pd.DataFrame(frontier_points)


def compare_optimization_results(
    results: Dict[OptimizationMethod, OptimizationResult]
) -> pd.DataFrame:
    """
    对比不同优化方法的结果

    Args:
        results: 优化结果字典

    Returns:
        对比DataFrame
    """
    comparison_data = []

    for method, result in results.items():
        row = {
            'method': method.value,
            'expected_return': result.expected_return,
            'expected_volatility': result.expected_volatility,
            'sharpe_ratio': result.sharpe_ratio,
            'diversification_ratio': result.diversification_ratio,
            'success': result.success,
            'message': result.message
        }
        comparison_data.append(row)

    df = pd.DataFrame(comparison_data)
    df = df.set_index('method')
    return df


def get_simple_optimizer(
    returns: pd.DataFrame,
    risk_free_rate: float = 0.03
) -> PortfolioOptimizer:
    """
    创建一个简单的优化器实例（工厂函数）

    Args:
        returns: 收益率数据
        risk_free_rate: 无风险利率

    Returns:
        PortfolioOptimizer: 优化器实例
    """
    return PortfolioOptimizer(
        returns=returns,
        risk_free_rate=risk_free_rate
    )
