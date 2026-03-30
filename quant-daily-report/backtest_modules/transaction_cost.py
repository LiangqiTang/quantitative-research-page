"""
交易成本模型 - 专业交易成本计算
包含手续费、印花税、过户费、滑点、冲击成本、涨跌停处理
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum


class OrderDirection(Enum):
    """订单方向"""
    BUY = "buy"
    SELL = "sell"


class SlippageModel(Enum):
    """滑点模型"""
    FIXED = "fixed"           # 固定滑点
    PERCENTAGE = "percentage"  # 比例滑点
    VOLATILITY = "volatility"  # 基于波动率的滑点


@dataclass
class TransactionCost:
    """单笔交易成本"""
    commission: float          # 佣金
    stamp_duty: float          # 印花税
    transfer_fee: float        # 过户费
    slippage_cost: float       # 滑点成本
    impact_cost: float         # 冲击成本
    total_cost: float          # 总成本
    cost_ratio: float          # 成本占交易金额的比例


@dataclass
class PriceLimitCheck:
    """涨跌停检查结果"""
    can_trade: bool            # 是否可以交易
    reason: str                # 原因
    limit_price: Optional[float] = None  # 涨跌停价格
    current_price: Optional[float] = None  # 当前价格


class TransactionCostModel:
    """
    交易成本模型

    支持的成本类型：
    - 佣金：券商佣金（默认万分之3）
    - 印花税：仅卖出时征收（默认千分之1）
    - 过户费：沪市股票（默认十万分之2）
    - 滑点：固定滑点或比例滑点
    - 冲击成本：考虑交易量的价格冲击（Almgren-Chriss模型）
    """

    def __init__(self,
                 commission_rate: float = 0.0003,
                 min_commission: float = 5.0,
                 stamp_duty_rate: float = 0.001,
                 transfer_fee_rate: float = 0.00002,
                 min_transfer_fee: float = 1.0,
                 slippage_model: SlippageModel = SlippageModel.PERCENTAGE,
                 slippage: float = 0.001,
                 impact_coef: float = 0.1):
        """
        初始化交易成本模型

        Args:
            commission_rate: 佣金率（默认万分之3）
            min_commission: 最低佣金（默认5元）
            stamp_duty_rate: 印花税率（默认千分之1，仅卖出）
            transfer_fee_rate: 过户费率（默认十万分之2，仅沪市）
            min_transfer_fee: 最低过户费（默认1元）
            slippage_model: 滑点模型
            slippage: 滑点参数（固定金额或比例）
            impact_coef: 冲击成本系数
        """
        self.commission_rate = commission_rate
        self.min_commission = min_commission
        self.stamp_duty_rate = stamp_duty_rate
        self.transfer_fee_rate = transfer_fee_rate
        self.min_transfer_fee = min_transfer_fee
        self.slippage_model = slippage_model
        self.slippage = slippage
        self.impact_coef = impact_coef

        print(f"✅ 交易成本模型初始化完成")
        print(f"   佣金率: {commission_rate:.2%}, 最低: {min_commission}元")
        print(f"   印花税: {stamp_duty_rate:.2%} (仅卖出)")
        print(f"   过户费: {transfer_fee_rate:.2%}, 最低: {min_transfer_fee}元")
        print(f"   滑点模型: {slippage_model.value}, 参数: {slippage}")

    def calculate_cost(self,
                       quantity: int,
                       price: float,
                       direction: OrderDirection,
                       ts_code: Optional[str] = None,
                       daily_volume: Optional[float] = None,
                       volatility: Optional[float] = None) -> TransactionCost:
        """
        计算单笔交易成本

        Args:
            quantity: 交易数量（股数）
            price: 交易价格
            direction: 交易方向（买入/卖出）
            ts_code: 股票代码（用于判断是否沪市）
            daily_volume: 日成交量（用于冲击成本计算）
            volatility: 波动率（用于基于波动率的滑点）

        Returns:
            TransactionCost: 交易成本明细
        """
        if quantity <= 0 or price <= 0:
            return TransactionCost(
                commission=0, stamp_duty=0, transfer_fee=0,
                slippage_cost=0, impact_cost=0, total_cost=0, cost_ratio=0
            )

        trade_value = quantity * price

        # 1. 佣金
        commission = max(self.min_commission, trade_value * self.commission_rate)

        # 2. 印花税（仅卖出时征收）
        stamp_duty = trade_value * self.stamp_duty_rate if direction == OrderDirection.SELL else 0

        # 3. 过户费（仅沪市股票，600/601/603/605开头）
        transfer_fee = 0
        if ts_code and (ts_code.startswith('600') or ts_code.startswith('601') or
                        ts_code.startswith('603') or ts_code.startswith('605')):
            transfer_fee = max(self.min_transfer_fee, trade_value * self.transfer_fee_rate)

        # 4. 滑点成本
        slippage_cost = self._calculate_slippage(quantity, price, direction, volatility)

        # 5. 冲击成本
        impact_cost = self._calculate_impact_cost(quantity, price, daily_volume)

        # 总成本
        total_cost = commission + stamp_duty + transfer_fee + slippage_cost + impact_cost
        cost_ratio = total_cost / trade_value if trade_value > 0 else 0

        return TransactionCost(
            commission=commission,
            stamp_duty=stamp_duty,
            transfer_fee=transfer_fee,
            slippage_cost=slippage_cost,
            impact_cost=impact_cost,
            total_cost=total_cost,
            cost_ratio=cost_ratio
        )

    def _calculate_slippage(self,
                             quantity: int,
                             price: float,
                             direction: OrderDirection,
                             volatility: Optional[float] = None) -> float:
        """计算滑点成本"""
        trade_value = quantity * price

        if self.slippage_model == SlippageModel.FIXED:
            # 固定滑点：每股固定金额
            return quantity * self.slippage

        elif self.slippage_model == SlippageModel.VOLATILITY:
            # 基于波动率的滑点：滑点 = 波动率 * 系数
            if volatility is None:
                volatility = 0.02  # 默认2%的日波动率
            slippage_per_share = price * volatility * self.slippage
            return quantity * slippage_per_share

        else:  # PERCENTAGE
            # 比例滑点：交易金额的一定比例
            return trade_value * self.slippage

    def _calculate_impact_cost(self,
                                quantity: int,
                                price: float,
                                daily_volume: Optional[float] = None) -> float:
        """
        计算冲击成本（参考Almgren-Chriss模型）

        冲击成本 = 0.5 * λ * σ * sqrt(Q/V) * Q * P

        其中：
        - λ: 冲击成本系数
        - σ: 波动率（简化为常数）
        - Q: 交易量
        - V: 日成交量
        - P: 价格
        """
        if daily_volume is None or daily_volume <= 0:
            return 0

        if quantity <= 0:
            return 0

        # 简化版冲击成本模型
        participation_rate = quantity / daily_volume

        if participation_rate > 0.1:  # 成交量占比超过10%才有显著冲击
            # 冲击成本随参与率非线性增长
            impact = self.impact_coef * (participation_rate ** 1.5) * quantity * price
            return impact
        else:
            return 0

    def calculate_execution_price(self,
                                   quantity: int,
                                   price: float,
                                   direction: OrderDirection,
                                   ts_code: Optional[str] = None,
                                   daily_volume: Optional[float] = None) -> float:
        """
        计算实际执行价格（考虑滑点和冲击成本）

        Args:
            quantity: 交易数量
            price: 原始价格
            direction: 交易方向
            ts_code: 股票代码
            daily_volume: 日成交量

        Returns:
            float: 实际执行价格
        """
        cost = self.calculate_cost(quantity, price, direction, ts_code, daily_volume)

        # 计算每股成本
        per_share_cost = cost.total_cost / quantity if quantity > 0 else 0

        if direction == OrderDirection.BUY:
            # 买入：实际价格 = 原始价格 + 每股成本
            return price + per_share_cost
        else:
            # 卖出：实际价格 = 原始价格 - 每股成本
            return price - per_share_cost

    def estimate_round_trip_cost(self,
                                  quantity: int,
                                  price: float,
                                  ts_code: Optional[str] = None) -> TransactionCost:
        """
        估算一个完整来回（买入+卖出）的交易成本

        Args:
            quantity: 交易数量
            price: 交易价格
            ts_code: 股票代码

        Returns:
            TransactionCost: 来回总成本
        """
        buy_cost = self.calculate_cost(quantity, price, OrderDirection.BUY, ts_code)
        sell_cost = self.calculate_cost(quantity, price, OrderDirection.SELL, ts_code)

        return TransactionCost(
            commission=buy_cost.commission + sell_cost.commission,
            stamp_duty=buy_cost.stamp_duty + sell_cost.stamp_duty,
            transfer_fee=buy_cost.transfer_fee + sell_cost.transfer_fee,
            slippage_cost=buy_cost.slippage_cost + sell_cost.slippage_cost,
            impact_cost=buy_cost.impact_cost + sell_cost.impact_cost,
            total_cost=buy_cost.total_cost + sell_cost.total_cost,
            cost_ratio=(buy_cost.total_cost + sell_cost.total_cost) / (price * quantity * 2)
        )


class PriceLimitHandler:
    """
    涨跌停处理器

    功能：
    - 计算涨跌停价格
    - 检查是否可以交易
    - 处理涨跌停情况下的订单调整
    """

    def __init__(self,
                 st_limit_rate: float = 0.1,
                 st_st_limit_rate: float = 0.05,
                 new_stock_limit_rate: float = 0.44):
        """
        初始化涨跌停处理器

        Args:
            st_limit_rate: 普通股涨跌幅限制（默认10%）
            st_st_limit_rate: ST股票涨跌幅限制（默认5%）
            new_stock_limit_rate: 新股首日涨跌幅限制（默认44%）
        """
        self.st_limit_rate = st_limit_rate
        self.st_st_limit_rate = st_st_limit_rate
        self.new_stock_limit_rate = new_stock_limit_rate

    def calculate_limit_prices(self,
                                 prev_close: float,
                                 is_st: bool = False,
                                 is_new_stock: bool = False) -> Tuple[float, float]:
        """
        计算涨跌停价格

        Args:
            prev_close: 前收盘价
            is_st: 是否为ST股票
            is_new_stock: 是否为新股首日

        Returns:
            Tuple[float, float]: (跌停价, 涨停价)
        """
        if prev_close <= 0:
            return 0, 0

        if is_new_stock:
            limit_rate = self.new_stock_limit_rate
        elif is_st:
            limit_rate = self.st_st_limit_rate
        else:
            limit_rate = self.st_limit_rate

        # 计算涨跌停价格，保留2位小数（精确到分）
        limit_down = round(prev_close * (1 - limit_rate), 2)
        limit_up = round(prev_close * (1 + limit_rate), 2)

        return limit_down, limit_up

    def check_tradable(self,
                        current_price: float,
                        limit_down: float,
                        limit_up: float,
                        direction: OrderDirection,
                        volume: Optional[float] = None) -> PriceLimitCheck:
        """
        检查是否可以交易

        Args:
            current_price: 当前价格
            limit_down: 跌停价
            limit_up: 涨停价
            direction: 交易方向
            volume: 当前成交量（用于判断是否封死涨跌停）

        Returns:
            PriceLimitCheck: 涨跌停检查结果
        """
        # 允许1分的价格误差
        epsilon = 0.01

        if current_price >= limit_up - epsilon:
            # 涨停
            if direction == OrderDirection.SELL:
                # 涨停可以卖出
                return PriceLimitCheck(
                    can_trade=True,
                    reason="涨停，可以卖出",
                    limit_price=limit_up,
                    current_price=current_price
                )
            else:
                # 涨停买入需检查是否有卖单
                # 简化判断：假设有成交量就可以买入
                if volume and volume > 0:
                    return PriceLimitCheck(
                        can_trade=True,
                        reason="涨停，但有成交，可以尝试买入",
                        limit_price=limit_up,
                        current_price=current_price
                    )
                else:
                    return PriceLimitCheck(
                        can_trade=False,
                        reason="涨停封死，无法买入",
                        limit_price=limit_up,
                        current_price=current_price
                    )

        elif current_price <= limit_down + epsilon:
            # 跌停
            if direction == OrderDirection.BUY:
                # 跌停可以买入
                return PriceLimitCheck(
                    can_trade=True,
                    reason="跌停，可以买入",
                    limit_price=limit_down,
                    current_price=current_price
                )
            else:
                # 跌停卖出需检查是否有买单
                if volume and volume > 0:
                    return PriceLimitCheck(
                        can_trade=True,
                        reason="跌停，但有成交，可以尝试卖出",
                        limit_price=limit_down,
                        current_price=current_price
                    )
                else:
                    return PriceLimitCheck(
                        can_trade=False,
                        reason="跌停封死，无法卖出",
                        limit_price=limit_down,
                        current_price=current_price
                    )

        else:
            # 正常价格区间，可以交易
            return PriceLimitCheck(
                can_trade=True,
                reason="正常交易区间",
                limit_price=None,
                current_price=current_price
            )

    def adjust_order_price(self,
                           target_price: float,
                           limit_down: float,
                           limit_up: float,
                           direction: OrderDirection) -> float:
        """
        调整订单价格到涨跌停范围内

        Args:
            target_price: 目标价格
            limit_down: 跌停价
            limit_up: 涨停价
            direction: 交易方向

        Returns:
            float: 调整后的价格
        """
        if target_price > limit_up:
            return limit_up
        elif target_price < limit_down:
            return limit_down
        else:
            return target_price


class TradingCalendar:
    """
    交易日历

    功能：
    - 判断是否为交易日
    - 获取下一个交易日
    - 判断是否停牌
    """

    def __init__(self, trading_dates: Optional[List[str]] = None):
        """
        初始化交易日历

        Args:
            trading_dates: 交易日列表（格式：YYYYMMDD）
        """
        self.trading_dates = set(trading_dates) if trading_dates else set()
        self.suspended_stocks: Dict[str, List[str]] = {}  # ts_code -> [suspend_dates]

    def is_trading_day(self, date: str) -> bool:
        """判断是否为交易日"""
        if not self.trading_dates:
            # 如果没有交易日历，默认周一到周五是交易日
            try:
                dt = pd.to_datetime(date)
                return dt.weekday() < 5
            except:
                return False
        return date in self.trading_dates

    def is_suspended(self, ts_code: str, date: str) -> bool:
        """判断股票是否停牌"""
        if ts_code in self.suspended_stocks:
            return date in self.suspended_stocks[ts_code]
        return False

    def add_suspended_stock(self, ts_code: str, suspend_dates: List[str]):
        """添加停牌股票"""
        if ts_code not in self.suspended_stocks:
            self.suspended_stocks[ts_code] = []
        self.suspended_stocks[ts_code].extend(suspend_dates)


def get_average_cost_model() -> TransactionCostModel:
    """
    获取平均成本模型（行业平均水平）

    Returns:
        TransactionCostModel: 平均成本模型
    """
    return TransactionCostModel(
        commission_rate=0.0003,      # 万分之3佣金
        min_commission=5.0,            # 最低5元
        stamp_duty_rate=0.001,         # 千分之1印花税
        transfer_fee_rate=0.00002,     # 十万分之2过户费
        min_transfer_fee=1.0,           # 最低1元
        slippage_model=SlippageModel.PERCENTAGE,
        slippage=0.001,                 # 千分之1滑点
        impact_coef=0.1
    )


def get_conservative_cost_model() -> TransactionCostModel:
    """
    获取保守成本模型（假设较高成本）

    Returns:
        TransactionCostModel: 保守成本模型
    """
    return TransactionCostModel(
        commission_rate=0.0005,      # 万分之5佣金
        min_commission=5.0,
        stamp_duty_rate=0.001,
        transfer_fee_rate=0.00002,
        min_transfer_fee=1.0,
        slippage_model=SlippageModel.PERCENTAGE,
        slippage=0.002,                 # 千分之2滑点
        impact_coef=0.2
    )


def get_aggressive_cost_model() -> TransactionCostModel:
    """
    获取激进成本模型（假设较低成本，如量化专用席位）

    Returns:
        TransactionCostModel: 激进成本模型
    """
    return TransactionCostModel(
        commission_rate=0.0001,      # 万分之1佣金
        min_commission=0.0,            # 无最低佣金
        stamp_duty_rate=0.001,
        transfer_fee_rate=0.00001,     # 十万分之1过户费
        min_transfer_fee=0.0,
        slippage_model=SlippageModel.PERCENTAGE,
        slippage=0.0005,                # 万分之5滑点
        impact_coef=0.05
    )
