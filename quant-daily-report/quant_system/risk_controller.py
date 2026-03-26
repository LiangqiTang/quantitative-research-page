"""
风险控制模块 - 专业的风险管理工具

提供完整的风险管理功能：
- 单笔止损止盈
- 组合最大回撤控制
- 单股/行业仓位限制
- 目标波动率策略
- 杠杆控制
- 风险调整订单生成
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timedelta


class StopType(Enum):
    """止损类型"""
    FIXED = "fixed"              # 固定价格止损
    TRAILING = "trailing"        # 移动止损
    ATR = "atr"                  # ATR动态止损


class RiskCheckResult(Enum):
    """风险检查结果"""
    OK = "ok"                      # 通过
    STOP_LOSS = "stop_loss"        # 触发止损
    STOP_PROFIT = "stop_profit"    # 触发止盈
    MAX_DRAWDOWN = "max_drawdown"  # 触发最大回撤
    POSITION_LIMIT = "position_limit"  # 仓位超限
    LEVERAGE_LIMIT = "leverage_limit"  # 杠杆超限
    VOLATILITY_HIGH = "volatility_high"  # 波动率过高


@dataclass
class PositionEntry:
    """持仓记录"""
    ts_code: str
    quantity: int
    entry_price: float
    current_price: float
    entry_date: str
    highest_price: float = 0.0      # 移动止损用：历史最高价
    lowest_price: float = float('inf')  # 移动止盈用：历史最低价
    stop_loss_price: Optional[float] = None
    stop_profit_price: Optional[float] = None


@dataclass
class RiskAdjustedOrder:
    """风险调整后的订单"""
    original_order: Any
    adjusted_order: Optional[Any]
    risk_check_result: RiskCheckResult
    reason: str = ""
    action: str = "keep"  # keep, adjust, cancel


class RiskController:
    """
    风险控制器

    提供全面的风险管理功能
    """

    def __init__(
        self,
        max_drawdown: float = 0.2,
        stop_loss_pct: float = 0.1,
        stop_profit_pct: Optional[float] = None,
        target_volatility: float = 0.2,
        max_leverage: float = 1.0,
        max_single_position: float = 0.1,
        max_sector_position: float = 0.3,
        trailing_stop_pct: Optional[float] = None,
        risk_free_rate: float = 0.03,
        frequency: int = 252
    ):
        """
        初始化风险控制器

        Args:
            max_drawdown: 组合最大回撤容忍度 (0.2 = 20%)
            stop_loss_pct: 单笔止损比例
            stop_profit_pct: 单笔止盈比例（可选）
            target_volatility: 目标波动率 (0.2 = 20%)
            max_leverage: 最大杠杆倍数
            max_single_position: 单股最大仓位比例
            max_sector_position: 单行业最大仓位比例
            trailing_stop_pct: 移动止损比例（可选）
            risk_free_rate: 无风险利率
            frequency: 年化频率
        """
        self.max_drawdown = max_drawdown
        self.stop_loss_pct = stop_loss_pct
        self.stop_profit_pct = stop_profit_pct
        self.target_volatility = target_volatility
        self.max_leverage = max_leverage
        self.max_single_position = max_single_position
        self.max_sector_position = max_sector_position
        self.trailing_stop_pct = trailing_stop_pct
        self.risk_free_rate = risk_free_rate
        self.frequency = frequency

        # 持仓记录
        self.position_entries: Dict[str, PositionEntry] = {}
        # 组合历史
        self.portfolio_history: List[Dict] = []
        # 行业分类（可选）
        self.sector_classification: Dict[str, str] = {}

    def set_sector_classification(self, sector_map: Dict[str, str]):
        """
        设置行业分类

        Args:
            sector_map: 股票代码 -> 行业名称的映射
        """
        self.sector_classification = sector_map

    def register_position(
        self,
        ts_code: str,
        quantity: int,
        price: float,
        date: str
    ):
        """
        登记新持仓

        Args:
            ts_code: 股票代码
            quantity: 数量
            price: 买入价格
            date: 日期
        """
        if quantity == 0:
            if ts_code in self.position_entries:
                del self.position_entries[ts_code]
            return

        if quantity > 0:
            # 新建或加仓
            if ts_code in self.position_entries:
                # 加仓：调整平均成本
                entry = self.position_entries[ts_code]
                total_qty = entry.quantity + quantity
                total_cost = entry.entry_price * entry.quantity + price * quantity
                entry.quantity = total_qty
                entry.entry_price = total_cost / total_qty
                entry.current_price = price
                entry.highest_price = max(entry.highest_price, price)
                entry.lowest_price = min(entry.lowest_price, price)
            else:
                # 新建持仓
                self.position_entries[ts_code] = PositionEntry(
                    ts_code=ts_code,
                    quantity=quantity,
                    entry_price=price,
                    current_price=price,
                    entry_date=date,
                    highest_price=price,
                    lowest_price=price
                )

            # 计算止损止盈价格
            self._update_stop_prices(ts_code)
        else:
            # 减仓
            if ts_code in self.position_entries:
                entry = self.position_entries[ts_code]
                entry.quantity += quantity  # quantity为负数
                if entry.quantity <= 0:
                    del self.position_entries[ts_code]

    def _update_stop_prices(self, ts_code: str):
        """
        更新止损止盈价格

        Args:
            ts_code: 股票代码
        """
        if ts_code not in self.position_entries:
            return

        entry = self.position_entries[ts_code]

        # 固定止损
        entry.stop_loss_price = entry.entry_price * (1 - self.stop_loss_pct)

        # 固定止盈
        if self.stop_profit_pct:
            entry.stop_profit_price = entry.entry_price * (1 + self.stop_profit_pct)

    def update_position_prices(self, current_prices: Dict[str, float]):
        """
        更新持仓的当前价格

        Args:
            current_prices: 股票代码 -> 当前价格的映射
        """
        for ts_code, price in current_prices.items():
            if ts_code in self.position_entries:
                entry = self.position_entries[ts_code]
                entry.current_price = price

                # 更新最高价/最低价（用于移动止损）
                if self.trailing_stop_pct:
                    entry.highest_price = max(entry.highest_price, price)
                    entry.lowest_price = min(entry.lowest_price, price)

                    # 更新移动止损价
                    entry.stop_loss_price = entry.highest_price * (1 - self.trailing_stop_pct)

                    # 更新移动止盈价（如果设置了）
                    if self.stop_profit_pct:
                        entry.stop_profit_price = entry.lowest_price * (1 + self.trailing_stop_pct)

    def check_stop_loss(self, ts_code: str) -> Tuple[bool, RiskCheckResult]:
        """
        检查单笔止损

        Args:
            ts_code: 股票代码

        Returns:
            (是否触发, 检查结果)
        """
        if ts_code not in self.position_entries:
            return False, RiskCheckResult.OK

        entry = self.position_entries[ts_code]

        if entry.stop_loss_price and entry.current_price <= entry.stop_loss_price:
            return True, RiskCheckResult.STOP_LOSS

        return False, RiskCheckResult.OK

    def check_stop_profit(self, ts_code: str) -> Tuple[bool, RiskCheckResult]:
        """
        检查单笔止盈

        Args:
            ts_code: 股票代码

        Returns:
            (是否触发, 检查结果)
        """
        if ts_code not in self.position_entries or not self.stop_profit_pct:
            return False, RiskCheckResult.OK

        entry = self.position_entries[ts_code]

        if entry.stop_profit_price and entry.current_price >= entry.stop_profit_price:
            return True, RiskCheckResult.STOP_PROFIT

        return False, RiskCheckResult.OK

    def check_position_stop(self, ts_code: str) -> Tuple[bool, RiskCheckResult]:
        """
        检查持仓的止损止盈

        Args:
            ts_code: 股票代码

        Returns:
            (是否触发, 检查结果)
        """
        # 先检查止损
        stop_loss, result = self.check_stop_loss(ts_code)
        if stop_loss:
            return True, result

        # 再检查止盈
        stop_profit, result = self.check_stop_profit(ts_code)
        if stop_profit:
            return True, result

        return False, RiskCheckResult.OK

    def record_portfolio_value(self, total_value: float, date: str):
        """
        记录组合净值

        Args:
            total_value: 组合总价值
            date: 日期
        """
        self.portfolio_history.append({
            'date': date,
            'total_value': total_value
        })

    def calculate_current_drawdown(self) -> float:
        """
        计算当前回撤

        Returns:
            当前回撤（正数表示回撤比例）
        """
        if len(self.portfolio_history) < 2:
            return 0.0

        values = [h['total_value'] for h in self.portfolio_history]
        cummax = np.maximum.accumulate(values)
        drawdown = (cummax[-1] - values[-1]) / cummax[-1]

        return drawdown

    def check_max_drawdown(self) -> Tuple[bool, RiskCheckResult]:
        """
        检查组合最大回撤

        Returns:
            (是否触发, 检查结果)
        """
        drawdown = self.calculate_current_drawdown()

        if drawdown >= self.max_drawdown:
            return True, RiskCheckResult.MAX_DRAWDOWN

        return False, RiskCheckResult.OK

    def check_position_limit(
        self,
        ts_code: str,
        target_weight: float,
        portfolio_value: float
    ) -> Tuple[bool, RiskCheckResult]:
        """
        检查单股仓位限制

        Args:
            ts_code: 股票代码
            target_weight: 目标权重
            portfolio_value: 组合总价值

        Returns:
            (是否超限, 检查结果)
        """
        if target_weight > self.max_single_position:
            return True, RiskCheckResult.POSITION_LIMIT

        return False, RiskCheckResult.OK

    def check_sector_limits(
        self,
        target_weights: Dict[str, float]
    ) -> Dict[str, Tuple[bool, RiskCheckResult]]:
        """
        检查行业仓位限制

        Args:
            target_weights: 目标权重字典

        Returns:
            行业 -> (是否超限, 检查结果) 的映射
        """
        if not self.sector_classification:
            return {}

        sector_weights: Dict[str, float] = {}
        for ts_code, weight in target_weights.items():
            sector = self.sector_classification.get(ts_code, 'unknown')
            sector_weights[sector] = sector_weights.get(sector, 0.0) + weight

        results = {}
        for sector, weight in sector_weights.items():
            if weight > self.max_sector_position:
                results[sector] = (True, RiskCheckResult.POSITION_LIMIT)
            else:
                results[sector] = (False, RiskCheckResult.OK)

        return results

    def check_leverage(
        self,
        total_exposure: float,
        portfolio_value: float
    ) -> Tuple[bool, RiskCheckResult]:
        """
        检查杠杆限制

        Args:
            total_exposure: 总敞口
            portfolio_value: 组合净值

        Returns:
            (是否超限, 检查结果)
        """
        leverage = total_exposure / portfolio_value if portfolio_value > 0 else 0

        if leverage > self.max_leverage:
            return True, RiskCheckResult.LEVERAGE_LIMIT

        return False, RiskCheckResult.OK

    def calculate_volatility(
        self,
        returns: Optional[pd.Series] = None,
        window: int = 20
    ) -> float:
        """
        计算组合波动率

        Args:
            returns: 收益率序列（可选，否则用历史计算）
            window: 滚动窗口

        Returns:
            年化波动率
        """
        if returns is not None:
            return float(returns.std() * np.sqrt(self.frequency))

        if len(self.portfolio_history) < window + 1:
            return 0.0

        # 从组合历史计算收益率
        values = [h['total_value'] for h in self.portfolio_history[-window-1:]]
        returns = pd.Series(values).pct_change().dropna()

        return float(returns.std() * np.sqrt(self.frequency))

    def adjust_for_volatility(
        self,
        target_weights: Dict[str, float],
        current_vol: Optional[float] = None,
        returns: Optional[pd.Series] = None
    ) -> Dict[str, float]:
        """
        根据波动率调整仓位（目标波动率策略）

        Args:
            target_weights: 原始目标权重
            current_vol: 当前波动率（可选）
            returns: 收益率序列（可选）

        Returns:
            调整后的目标权重
        """
        if current_vol is None:
            current_vol = self.calculate_volatility(returns)

        if current_vol <= 0:
            return target_weights

        # 波动率调整倍数
        vol_scalar = self.target_volatility / current_vol
        # 限制调整范围在 [0.5, 2.0] 之间
        vol_scalar = max(0.5, min(2.0, vol_scalar))

        # 调整所有权重
        adjusted_weights = {
            ts_code: weight * vol_scalar
            for ts_code, weight in target_weights.items()
        }

        return adjusted_weights

    def check_all_positions(self) -> List[Tuple[str, RiskCheckResult]]:
        """
        检查所有持仓的止损止盈

        Returns:
            (股票代码, 检查结果) 列表
        """
        results = []
        for ts_code in list(self.position_entries.keys()):
            triggered, result = self.check_position_stop(ts_code)
            if triggered:
                results.append((ts_code, result))
        return results

    def generate_risk_adjusted_orders(
        self,
        orders: List[Any],
        portfolio: Any,
        current_prices: Dict[str, float]
    ) -> List[RiskAdjustedOrder]:
        """
        生成风险调整后的订单

        Args:
            orders: 原始订单列表
            portfolio: 组合对象
            current_prices: 当前价格

        Returns:
            风险调整后的订单列表
        """
        adjusted_orders = []

        # 先更新价格
        self.update_position_prices(current_prices)

        # 检查所有持仓的止损止盈
        stop_positions = self.check_all_positions()

        # 为触发止损止盈的持仓生成平仓订单
        for ts_code, result in stop_positions:
            if ts_code in self.position_entries:
                entry = self.position_entries[ts_code]
                # 生成平仓订单（这里需要根据实际Order类型调整）
                adjusted_orders.append(RiskAdjustedOrder(
                    original_order=None,
                    adjusted_order=None,  # 需要根据实际Order类型构造
                    risk_check_result=result,
                    reason=f"{result.value} triggered for {ts_code}",
                    action="close"
                ))

        # 检查组合最大回撤
        drawdown_triggered, drawdown_result = self.check_max_drawdown()
        if drawdown_triggered:
            # 最大回撤触发：清仓所有持仓
            for ts_code in list(self.position_entries.keys()):
                adjusted_orders.append(RiskAdjustedOrder(
                    original_order=None,
                    adjusted_order=None,
                    risk_check_result=drawdown_result,
                    reason=f"Max drawdown triggered, closing {ts_code}",
                    action="close"
                ))

        # 处理原始订单
        for order in orders:
            ts_code = getattr(order, 'ts_code', None)
            if not ts_code:
                adjusted_orders.append(RiskAdjustedOrder(
                    original_order=order,
                    adjusted_order=order,
                    risk_check_result=RiskCheckResult.OK,
                    action="keep"
                ))
                continue

            # 检查该股票是否需要平仓（止损止盈已触发）
            has_stop = any(ts_code == t for t, _ in stop_positions)
            if has_stop:
                adjusted_orders.append(RiskAdjustedOrder(
                    original_order=order,
                    adjusted_order=None,
                    risk_check_result=RiskCheckResult.STOP_LOSS,
                    reason=f"Position {ts_code} marked for closing",
                    action="cancel"
                ))
                continue

            # 检查仓位限制
            # 这里需要获取目标权重来检查
            # 暂时直接通过
            adjusted_orders.append(RiskAdjustedOrder(
                original_order=order,
                adjusted_order=order,
                risk_check_result=RiskCheckResult.OK,
                action="keep"
            ))

        return adjusted_orders

    def get_risk_summary(self) -> Dict[str, Any]:
        """
        获取风险概览

        Returns:
            风险指标字典
        """
        summary = {
            'current_drawdown': self.calculate_current_drawdown(),
            'max_drawdown_limit': self.max_drawdown,
            'position_count': len(self.position_entries),
            'stop_loss_pct': self.stop_loss_pct,
            'stop_profit_pct': self.stop_profit_pct,
            'trailing_stop_pct': self.trailing_stop_pct,
            'target_volatility': self.target_volatility,
            'max_leverage': self.max_leverage,
            'max_single_position': self.max_single_position,
            'max_sector_position': self.max_sector_position
        }

        # 持仓详情
        summary['positions'] = []
        for ts_code, entry in self.position_entries.items():
            pnl = (entry.current_price - entry.entry_price) / entry.entry_price if entry.entry_price > 0 else 0
            summary['positions'].append({
                'ts_code': ts_code,
                'quantity': entry.quantity,
                'entry_price': entry.entry_price,
                'current_price': entry.current_price,
                'pnl_pct': pnl,
                'stop_loss_price': entry.stop_loss_price,
                'stop_profit_price': entry.stop_profit_price
            })

        return summary


def get_simple_risk_controller() -> RiskController:
    """
    创建一个简单的风险控制器实例（工厂函数）

    Returns:
        RiskController: 风险控制器实例
    """
    return RiskController(
        max_drawdown=0.2,
        stop_loss_pct=0.1,
        target_volatility=0.2,
        max_single_position=0.1
    )


def get_conservative_risk_controller() -> RiskController:
    """
    创建一个保守型的风险控制器实例

    Returns:
        RiskController: 保守型风险控制器
    """
    return RiskController(
        max_drawdown=0.1,
        stop_loss_pct=0.05,
        stop_profit_pct=0.1,
        target_volatility=0.15,
        max_leverage=1.0,
        max_single_position=0.05,
        max_sector_position=0.2,
        trailing_stop_pct=0.05
    )


def get_aggressive_risk_controller() -> RiskController:
    """
    创建一个激进型的风险控制器实例

    Returns:
        RiskController: 激进型风险控制器
    """
    return RiskController(
        max_drawdown=0.3,
        stop_loss_pct=0.15,
        target_volatility=0.3,
        max_leverage=1.5,
        max_single_position=0.2,
        max_sector_position=0.4
    )
