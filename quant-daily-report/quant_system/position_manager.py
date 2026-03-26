"""
仓位管理模块 - 专业仓位分配与管理
包含等权重、市值权重、风险预算、最大仓位限制等功能
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum


class PositionMethod(Enum):
    """仓位分配方法"""
    EQUAL_WEIGHT = "equal_weight"      # 等权重
    MARKET_CAP_WEIGHT = "market_cap"    # 市值权重
    RISK_BUDGET = "risk_budget"         # 风险预算
    RISK_PARITY = "risk_parity"         # 风险平价
    MAX_DIVERSIFICATION = "max_div"     # 最大分散化


@dataclass
class PositionTarget:
    """目标持仓"""
    ts_code: str
    target_weight: float         # 目标权重
    target_quantity: int         # 目标数量
    current_weight: float = 0.0  # 当前权重
    current_quantity: int = 0    # 当前数量
    price: float = 0.0           # 当前价格


@dataclass
class PositionAllocation:
    """仓位分配结果"""
    method: PositionMethod
    targets: List[PositionTarget]
    total_capital: float
    used_capital: float
    remaining_capital: float


class PositionManager:
    """
    仓位管理器

    核心功能：
    - 等权重分配
    - 市值权重分配
    - 风险预算分配
    - 最大仓位限制（单只股票/单个行业）
    - 最小交易单位处理（一手=100股）
    """

    def __init__(self,
                 total_capital: float,
                 max_single_position: float = 0.1,
                 max_industry_position: float = 0.3,
                 min_position_weight: float = 0.01,
                 lot_size: int = 100):
        """
        初始化仓位管理器

        Args:
            total_capital: 总资金
            max_single_position: 单只股票最大权重（默认10%）
            max_industry_position: 单个行业最大权重（默认30%）
            min_position_weight: 最小持仓权重（默认1%）
            lot_size: 一手股数（默认100股）
        """
        self.total_capital = total_capital
        self.max_single_position = max_single_position
        self.max_industry_position = max_industry_position
        self.min_position_weight = min_position_weight
        self.lot_size = lot_size

        print(f"✅ 仓位管理器初始化完成")
        print(f"   总资金: {total_capital:,.2f}")
        print(f"   单股最大权重: {max_single_position:.1%}")
        print(f"   行业最大权重: {max_industry_position:.1%}")
        print(f"   最小持仓权重: {min_position_weight:.1%}")
        print(f"   每手股数: {lot_size}")

    def calculate_equal_weight(self,
                                target_stocks: List[str],
                                prices: Dict[str, float],
                                current_positions: Optional[Dict[str, int]] = None,
                                industry_classification: Optional[Dict[str, str]] = None) -> PositionAllocation:
        """
        等权重分配

        Args:
            target_stocks: 目标股票列表
            prices: 股票价格字典
            current_positions: 当前持仓（股数）
            industry_classification: 行业分类字典

        Returns:
            PositionAllocation: 仓位分配结果
        """
        if not target_stocks:
            return PositionAllocation(
                method=PositionMethod.EQUAL_WEIGHT,
                targets=[],
                total_capital=self.total_capital,
                used_capital=0,
                remaining_capital=self.total_capital
            )

        # 基础权重
        n = len(target_stocks)
        base_weight = 1.0 / n

        # 应用单股上限
        weights = {}
        for stock in target_stocks:
            weights[stock] = min(base_weight, self.max_single_position)

        # 归一化
        total_weight = sum(weights.values())
        for stock in weights:
            weights[stock] = weights[stock] / total_weight

        # 应用行业上限
        if industry_classification:
            weights = self._apply_industry_limits(weights, industry_classification)

        # 转换为股数
        targets = self._weights_to_targets(weights, prices, current_positions)

        # 计算资金使用
        used_capital = sum(t.target_quantity * t.price for t in targets)
        remaining_capital = self.total_capital - used_capital

        return PositionAllocation(
            method=PositionMethod.EQUAL_WEIGHT,
            targets=targets,
            total_capital=self.total_capital,
            used_capital=used_capital,
            remaining_capital=remaining_capital
        )

    def calculate_market_cap_weight(self,
                                      target_stocks: List[str],
                                      prices: Dict[str, float],
                                      market_caps: Dict[str, float],
                                      current_positions: Optional[Dict[str, int]] = None,
                                      industry_classification: Optional[Dict[str, str]] = None) -> PositionAllocation:
        """
        市值权重分配

        Args:
            target_stocks: 目标股票列表
            prices: 股票价格字典
            market_caps: 市值字典
            current_positions: 当前持仓
            industry_classification: 行业分类

        Returns:
            PositionAllocation: 仓位分配结果
        """
        if not target_stocks or not market_caps:
            return self.calculate_equal_weight(target_stocks, prices, current_positions)

        # 按市值分配
        total_cap = sum(market_caps.get(stock, 0) for stock in target_stocks)

        if total_cap <= 0:
            return self.calculate_equal_weight(target_stocks, prices, current_positions)

        weights = {}
        for stock in target_stocks:
            cap = market_caps.get(stock, 0)
            weight = cap / total_cap if total_cap > 0 else 0
            weights[stock] = min(weight, self.max_single_position)

        # 归一化
        total_weight = sum(weights.values())
        for stock in weights:
            weights[stock] = weights[stock] / total_weight

        # 应用行业上限
        if industry_classification:
            weights = self._apply_industry_limits(weights, industry_classification)

        # 转换为股数
        targets = self._weights_to_targets(weights, prices, current_positions)

        used_capital = sum(t.target_quantity * t.price for t in targets)
        remaining_capital = self.total_capital - used_capital

        return PositionAllocation(
            method=PositionMethod.MARKET_CAP_WEIGHT,
            targets=targets,
            total_capital=self.total_capital,
            used_capital=used_capital,
            remaining_capital=remaining_capital
        )

    def calculate_risk_budget(self,
                               target_stocks: List[str],
                               prices: Dict[str, float],
                               volatilities: Dict[str, float],
                               risk_budgets: Optional[Dict[str, float]] = None,
                               current_positions: Optional[Dict[str, int]] = None,
                               industry_classification: Optional[Dict[str, str]] = None) -> PositionAllocation:
        """
        风险预算分配

        每个股票分配的权重与其风险贡献成反比

        Args:
            target_stocks: 目标股票列表
            prices: 股票价格字典
            volatilities: 波动率字典
            risk_budgets: 风险预算（可选，默认等风险预算）
            current_positions: 当前持仓
            industry_classification: 行业分类

        Returns:
            PositionAllocation: 仓位分配结果
        """
        if not target_stocks or not volatilities:
            return self.calculate_equal_weight(target_stocks, prices, current_positions)

        # 默认等风险预算
        if not risk_budgets:
            risk_budgets = {stock: 1.0 for stock in target_stocks}

        # 按波动率倒数分配权重
        weights = {}
        for stock in target_stocks:
            vol = volatilities.get(stock, 0.2)  # 默认20%波动率
            budget = risk_budgets.get(stock, 1.0)
            weight = budget / max(vol, 0.01)  # 避免除零
            weights[stock] = weight

        # 归一化
        total_weight = sum(weights.values())
        for stock in weights:
            weights[stock] = weights[stock] / total_weight

        # 应用单股上限
        for stock in weights:
            weights[stock] = min(weights[stock], self.max_single_position)

        # 再次归一化
        total_weight = sum(weights.values())
        for stock in weights:
            weights[stock] = weights[stock] / total_weight

        # 应用行业上限
        if industry_classification:
            weights = self._apply_industry_limits(weights, industry_classification)

        # 转换为股数
        targets = self._weights_to_targets(weights, prices, current_positions)

        used_capital = sum(t.target_quantity * t.price for t in targets)
        remaining_capital = self.total_capital - used_capital

        return PositionAllocation(
            method=PositionMethod.RISK_BUDGET,
            targets=targets,
            total_capital=self.total_capital,
            used_capital=used_capital,
            remaining_capital=remaining_capital
        )

    def calculate_risk_parity(self,
                               target_stocks: List[str],
                               prices: Dict[str, float],
                               returns_data: Optional[pd.DataFrame] = None,
                               cov_matrix: Optional[pd.DataFrame] = None,
                               current_positions: Optional[Dict[str, int]] = None) -> PositionAllocation:
        """
        风险平价分配（Risk Parity）

        使得每个股票对组合风险的贡献相等

        Args:
            target_stocks: 目标股票列表
            prices: 股票价格字典
            returns_data: 收益率数据（用于计算协方差矩阵）
            cov_matrix: 协方差矩阵（直接提供）
            current_positions: 当前持仓

        Returns:
            PositionAllocation: 仓位分配结果
        """
        if not target_stocks:
            return self.calculate_equal_weight(target_stocks, prices, current_positions)

        n = len(target_stocks)

        # 计算协方差矩阵
        if cov_matrix is None and returns_data is not None:
            cov_matrix = returns_data.cov()

        if cov_matrix is None:
            # 没有协方差矩阵，退化为基于波动率的风险预算
            volatilities = {stock: 0.2 for stock in target_stocks}
            return self.calculate_risk_budget(
                target_stocks, prices, volatilities, current_positions
            )

        # 简单风险平价：假设无相关性，仅使用波动率
        # 完整风险平价需要非线性优化
        weights = {}
        for stock in target_stocks:
            try:
                vol = np.sqrt(cov_matrix.loc[stock, stock]) if stock in cov_matrix.index else 0.2
            except:
                vol = 0.2
            weights[stock] = 1.0 / max(vol, 0.01)

        # 归一化
        total_weight = sum(weights.values())
        for stock in weights:
            weights[stock] = weights[stock] / total_weight

        # 应用单股上限
        for stock in weights:
            weights[stock] = min(weights[stock], self.max_single_position)

        # 再次归一化
        total_weight = sum(weights.values())
        for stock in weights:
            weights[stock] = weights[stock] / total_weight

        # 转换为股数
        targets = self._weights_to_targets(weights, prices, current_positions)

        used_capital = sum(t.target_quantity * t.price for t in targets)
        remaining_capital = self.total_capital - used_capital

        return PositionAllocation(
            method=PositionMethod.RISK_PARITY,
            targets=targets,
            total_capital=self.total_capital,
            used_capital=used_capital,
            remaining_capital=remaining_capital
        )

    def _apply_industry_limits(self,
                                  weights: Dict[str, float],
                                  industry_classification: Dict[str, str]) -> Dict[str, float]:
        """应用行业上限"""
        # 计算当前行业权重
        industry_weights = {}
        for stock, weight in weights.items():
            industry = industry_classification.get(stock, '其他')
            if industry not in industry_weights:
                industry_weights[industry] = 0
            industry_weights[industry] += weight

        # 检查并调整超限行业
        adjusted_weights = weights.copy()

        for industry, ind_weight in industry_weights.items():
            if ind_weight > self.max_industry_position:
                # 超限，按比例缩减
                scale = self.max_industry_position / ind_weight
                for stock in weights:
                    if industry_classification.get(stock) == industry:
                        adjusted_weights[stock] = weights[stock] * scale

        # 重新归一化
        total_weight = sum(adjusted_weights.values())
        for stock in adjusted_weights:
            adjusted_weights[stock] = adjusted_weights[stock] / total_weight

        return adjusted_weights

    def _weights_to_targets(self,
                              weights: Dict[str, float],
                              prices: Dict[str, float],
                              current_positions: Optional[Dict[str, int]] = None) -> List[PositionTarget]:
        """
        将权重转换为目标持仓（考虑一手股数）

        Args:
            weights: 目标权重字典
            prices: 股票价格字典
            current_positions: 当前持仓

        Returns:
            List[PositionTarget]: 目标持仓列表
        """
        current_positions = current_positions or {}

        targets = []
        remaining_capital = self.total_capital

        # 先过滤掉权重太小的
        valid_weights = {s: w for s, w in weights.items() if w >= self.min_position_weight}

        if not valid_weights:
            return []

        # 重新归一化
        total_weight = sum(valid_weights.values())
        for stock in valid_weights:
            valid_weights[stock] = valid_weights[stock] / total_weight

        # 按权重从大到小处理
        sorted_stocks = sorted(valid_weights.items(), key=lambda x: x[1], reverse=True)

        for stock, weight in sorted_stocks:
            price = prices.get(stock, 0)
            if price <= 0:
                continue

            # 计算目标资金
            target_capital = self.total_capital * weight

            # 实际可使用的资金（不超过剩余资金）
            available_capital = min(target_capital, remaining_capital)

            # 计算股数并取整到一手的整数倍
            quantity = self.round_to_lot_size(available_capital / price)

            # 计算实际使用的资金
            used_capital = quantity * price

            # 获取当前持仓
            current_qty = current_positions.get(stock, 0)
            current_weight = (current_qty * price) / self.total_capital if self.total_capital > 0 else 0

            targets.append(PositionTarget(
                ts_code=stock,
                target_weight=used_capital / self.total_capital if self.total_capital > 0 else 0,
                target_quantity=quantity,
                current_weight=current_weight,
                current_quantity=current_qty,
                price=price
            ))

            remaining_capital -= used_capital

        return targets

    def round_to_lot_size(self, quantity: float) -> int:
        """
        取整到一手的整数倍

        Args:
            quantity: 股数

        Returns:
            int: 取整后的股数
        """
        if quantity <= 0:
            return 0
        # 向下取整到一手
        return int(quantity // self.lot_size) * self.lot_size

    def generate_trades(self,
                        allocation: PositionAllocation,
                        current_positions: Dict[str, int]) -> List[Dict]:
        """
        生成交易清单

        Args:
            allocation: 仓位分配结果
            current_positions: 当前持仓

        Returns:
            List[Dict]: 交易清单
        """
        trades = []

        # 目标持仓字典
        target_dict = {t.ts_code: t for t in allocation.targets}

        # 卖出不再持有的股票
        for stock, qty in current_positions.items():
            if stock not in target_dict and qty > 0:
                trades.append({
                    'ts_code': stock,
                    'direction': 'sell',
                    'quantity': qty,
                    'reason': '移出组合'
                })

        # 调整现有持仓或新增
        for target in allocation.targets:
            current_qty = current_positions.get(target.ts_code, 0)
            target_qty = target.target_quantity

            diff = target_qty - current_qty

            if diff > 0:
                trades.append({
                    'ts_code': target.ts_code,
                    'direction': 'buy',
                    'quantity': diff,
                    'reason': '增持' if current_qty > 0 else '新建'
                })
            elif diff < 0:
                trades.append({
                    'ts_code': target.ts_code,
                    'direction': 'sell',
                    'quantity': -diff,
                    'reason': '减持'
                })

        return trades

    def calculate_turnover(self,
                           allocation: PositionAllocation,
                           current_positions: Dict[str, int],
                           prices: Dict[str, float]) -> float:
        """
        计算换手率

        Args:
            allocation: 仓位分配结果
            current_positions: 当前持仓
            prices: 股票价格

        Returns:
            float: 换手率
        """
        trades = self.generate_trades(allocation, current_positions)

        trade_value = 0
        for trade in trades:
            price = prices.get(trade['ts_code'], 0)
            trade_value += trade['quantity'] * price

        return trade_value / self.total_capital if self.total_capital > 0 else 0


def get_simple_position_manager(total_capital: float) -> PositionManager:
    """
    获取一个简单的仓位管理器（适合个人投资者）

    Args:
        total_capital: 总资金

    Returns:
        PositionManager: 仓位管理器
    """
    return PositionManager(
        total_capital=total_capital,
        max_single_position=0.15,      # 单股最大15%
        max_industry_position=0.4,     # 单行业最大40%
        min_position_weight=0.02,       # 最小2%（避免太分散）
        lot_size=100
    )


def get_institutional_position_manager(total_capital: float) -> PositionManager:
    """
    获取机构风格的仓位管理器

    Args:
        total_capital: 总资金

    Returns:
        PositionManager: 仓位管理器
    """
    return PositionManager(
        total_capital=total_capital,
        max_single_position=0.05,       # 单股最大5%
        max_industry_position=0.25,     # 单行业最大25%
        min_position_weight=0.005,      # 最小0.5%
        lot_size=100
    )
