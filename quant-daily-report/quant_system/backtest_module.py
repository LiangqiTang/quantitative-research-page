"""
回测模块 - 事件驱动回测引擎
包含策略执行、组合管理、绩效分析
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Callable, Set, Tuple
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timedelta


class OrderType(Enum):
    """订单类型"""
    MARKET = "market"
    LIMIT = "limit"


class OrderDirection(Enum):
    """订单方向"""
    BUY = "buy"
    SELL = "sell"


@dataclass
class Order:
    """订单"""
    ts_code: str
    direction: OrderDirection
    type: OrderType
    quantity: int
    price: Optional[float] = None
    time: Optional[str] = None


@dataclass
class Trade:
    """成交记录"""
    ts_code: str
    direction: OrderDirection
    quantity: int
    price: float
    time: str
    commission: float = 0.0
    slippage: float = 0.0
    impact_cost: float = 0.0
    total_cost: float = 0.0


@dataclass
class Position:
    """持仓"""
    ts_code: str
    quantity: int
    avg_price: float
    current_price: float
    market_value: float
    pnl: float
    pnl_ratio: float


class Strategy:
    """
    策略基类
    """

    def __init__(self, name: str = "BaseStrategy"):
        self.name = name

    def generate_signals(self, data: Dict[str, pd.DataFrame],
                       current_positions: Dict[str, Position]) -> List[Order]:
        """
        生成交易信号

        Args:
            data: 市场数据
            current_positions: 当前持仓

        Returns:
            List[Order]: 订单列表
        """
        raise NotImplementedError

    def on_bar(self, date: str, data: Dict[str, pd.DataFrame],
              current_positions: Dict[str, Position]) -> List[Order]:
        """
        每个时间片调用

        Args:
            date: 日期
            data: 数据
            current_positions: 当前持仓

        Returns:
            List[Order]: 订单列表
        """
        return self.generate_signals(data, current_positions)


class EqualWeightStrategy(Strategy):
    """
    等权重策略 - 基准策略
    """

    def __init__(self, stock_list: List[str], rebalance_freq: int = 20):
        super().__init__("EqualWeight")
        self.stock_list = stock_list
        self.rebalance_freq = rebalance_freq
        self.day_count = 0

    def generate_signals(self, data: Dict[str, pd.DataFrame],
                       current_positions: Dict[str, Position]) -> List[Order]:
        orders = []

        # 只在再平衡日调仓
        self.day_count += 1
        if self.day_count % self.rebalance_freq != 0:
            return orders

        # 等权重买入
        target_weight = 1.0 / len(self.stock_list)

        # 简化实现：等权重配置
        for ts_code in self.stock_list[:10]:  # 限制10只股票
            if ts_code not in current_positions:
                orders.append(Order(
                    ts_code=ts_code,
                    direction=OrderDirection.BUY,
                    type=OrderType.MARKET,
                    quantity=100
                ))

        return orders


class FactorStrategy(Strategy):
    """
    因子策略 - 基于因子选股
    """

    def __init__(self, factor_scores: Dict[str, float],
                 top_n: int = 10, rebalance_freq: int = 20):
        super().__init__("FactorStrategy")
        self.factor_scores = factor_scores
        self.top_n = top_n
        self.rebalance_freq = rebalance_freq
        self.day_count = 0

    def generate_signals(self, data: Dict[str, pd.DataFrame],
                       current_positions: Dict[str, Position]) -> List[Order]:
        orders = []

        self.day_count += 1
        if self.day_count % self.rebalance_freq != 0:
            return orders

        # 选择因子得分最高的股票
        sorted_stocks = sorted(
            self.factor_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )
        target_stocks = [s[0] for s in sorted_stocks[:self.top_n]]

        # 买入目标股票
        for ts_code in target_stocks:
            if ts_code not in current_positions:
                orders.append(Order(
                    ts_code=ts_code,
                    direction=OrderDirection.BUY,
                    type=OrderType.MARKET,
                    quantity=100
                ))

        # 卖出不在目标中的持仓
        for ts_code in list(current_positions.keys()):
            if ts_code not in target_stocks:
                orders.append(Order(
                    ts_code=ts_code,
                    direction=OrderDirection.SELL,
                    type=OrderType.MARKET,
                    quantity=current_positions[ts_code].quantity
                ))

        return orders


class Portfolio:
    """
    组合管理
    """

    def __init__(self, initial_capital: float = 1000000.0,
                 commission_rate: float = 0.0003):
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.commission_rate = commission_rate
        self.positions: Dict[str, Position] = {}
        self.trades: List[Trade] = []
        self.history: List[Dict] = []

    def update_market_data(self, data: Dict[str, pd.DataFrame], date: str):
        """
        更新市场数据

        Args:
            data: 市场数据
            date: 日期
        """
        # 更新持仓市值
        for ts_code, pos in self.positions.items():
            if ts_code in data:
                df = data[ts_code]
                df_date = df[df['trade_date'] == date]
                if not df_date.empty:
                    pos.current_price = float(df_date['close'].iloc[0])
                    pos.market_value = pos.quantity * pos.current_price
                    pos.pnl = (pos.current_price - pos.avg_price) * pos.quantity
                    pos.pnl_ratio = pos.pnl / (pos.avg_price * pos.quantity) if pos.avg_price > 0 else 0

        # 记录历史
        total_market_value = sum(p.market_value for p in self.positions.values())
        self.history.append({
            'date': date,
            'capital': self.current_capital,
            'market_value': total_market_value,
            'total_assets': self.current_capital + total_market_value,
            'position_count': len(self.positions),
            'trade_count': len(self.trades)
        })

    def execute_order(self, order: Order, data: Dict[str, pd.DataFrame], date: str) -> Optional[Trade]:
        """
        执行订单

        Args:
            order: 订单
            data: 市场数据
            date: 日期

        Returns:
            Trade: 成交记录
        """
        # 获取当前价格
        price = 0.0
        if order.ts_code in data:
            df = data[order.ts_code]
            df_date = df[df['trade_date'] == date]
            if not df_date.empty:
                price = float(df_date['close'].iloc[0])

        if price <= 0:
            return None

        # 计算手续费
        trade_value = price * order.quantity
        commission = trade_value * self.commission_rate

        # 执行交易
        if order.direction == OrderDirection.BUY:
            if self.current_capital < trade_value + commission:
                return None

            self.current_capital -= (trade_value + commission)

            # 更新持仓
            if order.ts_code in self.positions:
                pos = self.positions[order.ts_code]
                total_quantity = pos.quantity + order.quantity
                total_cost = pos.avg_price * pos.quantity + price * order.quantity
                pos.quantity = total_quantity
                pos.avg_price = total_cost / total_quantity
                pos.current_price = price
                pos.market_value = total_quantity * price
            else:
                self.positions[order.ts_code] = Position(
                    ts_code=order.ts_code,
                    quantity=order.quantity,
                    avg_price=price,
                    current_price=price,
                    market_value=order.quantity * price,
                    pnl=0,
                    pnl_ratio=0
                )

        else:  # SELL
            if order.ts_code not in self.positions:
                return None

            pos = self.positions[order.ts_code]
            if pos.quantity < order.quantity:
                return None

            # 计算卖出实现的盈亏
            realized_pnl = (price - pos.avg_price) * order.quantity
            self.current_capital += (trade_value - commission)
            pos.quantity -= order.quantity

            if pos.quantity <= 0:
                del self.positions[order.ts_code]
            else:
                pos.market_value = pos.quantity * price

        # 记录成交
        trade = Trade(
            ts_code=order.ts_code,
            direction=order.direction,
            quantity=order.quantity,
            price=price,
            time=date,
            commission=commission
        )
        self.trades.append(trade)
        return trade


class PerformanceMetrics:
    """
    绩效指标计算
    """

    @staticmethod
    def calculate(portfolio_history: List[Dict],
                  benchmark_returns: Optional[pd.Series] = None) -> Dict:
        """
        计算绩效指标

        Args:
            portfolio_history: 组合历史
            benchmark_returns: 基准收益率

        Returns:
            Dict: 绩效指标
        """
        if not portfolio_history:
            return {}

        df = pd.DataFrame(portfolio_history)
        df['date'] = pd.to_datetime(df['date'])
        df = df.set_index('date').sort_index()

        # 计算收益率
        df['returns'] = df['total_assets'].pct_change()

        total_assets = df['total_assets']
        initial_value = total_assets.iloc[0]
        final_value = total_assets.iloc[-1]

        # 基本指标
        total_return = (final_value / initial_value - 1) * 100

        # 年化收益率
        trading_days = len(df)
        annual_return = ((final_value / initial_value) ** (252 / trading_days) - 1) * 100

        # 波动率
        volatility = df['returns'].std() * np.sqrt(252) * 100

        # 夏普比率
        risk_free_rate = 0.03
        excess_returns = df['returns'] - risk_free_rate / 252
        sharpe_ratio = excess_returns.mean() / excess_returns.std() * np.sqrt(252) if excess_returns.std() > 0 else 0

        # 最大回撤
        cummax = total_assets.cummax()
        drawdown = (total_assets - cummax) / cummax
        max_drawdown = drawdown.min() * 100

        # 卡尔马比率
        calmar_ratio = (annual_return / 100) / abs(max_drawdown / 100) if max_drawdown != 0 else 0

        return {
            'total_return': total_return,
            'annual_return': annual_return,
            'volatility': volatility,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'calmar_ratio': calmar_ratio,
            'final_value': final_value,
            'trading_days': trading_days
        }


class BacktestEngine:
    """
    回测引擎
    """

    def __init__(self, data_manager, initial_capital: float = 1000000.0,
                 start_date: Optional[str] = None,
                 end_date: Optional[str] = None):
        self.data_manager = data_manager
        self.initial_capital = initial_capital
        self.start_date = start_date
        self.end_date = end_date

        self.portfolio: Optional[Portfolio] = None
        self.strategy: Optional[Strategy] = None
        self.results: Dict = {}

        print("✅ 回测引擎初始化完成")

    def set_strategy(self, strategy: Strategy):
        """设置策略"""
        self.strategy = strategy
        print(f"✅ 策略已设置: {strategy.name}")

    def run(self, stock_list: Optional[List[str]] = None) -> Dict:
        """
        运行回测

        Args:
            stock_list: 股票列表

        Returns:
            Dict: 回测结果
        """
        print("\n" + "=" * 60)
        print("⏳ 开始回测")
        print("=" * 60)

        # 准备数据
        data_dict = self.data_manager.prepare_factor_data(
            stock_list, self.start_date, self.end_date
        )

        if not data_dict:
            print("❌ 没有数据，无法回测")
            return {}

        # 初始化组合
        self.portfolio = Portfolio(initial_capital=self.initial_capital)

        # 获取交易日历
        first_code = list(data_dict.keys())[0]
        trade_dates = data_dict[first_code]['trade_date'].tolist()

        print(f"\n📊 回测周期: {trade_dates[0]} 至 {trade_dates[-1]}")
        print(f"📅 交易日数: {len(trade_dates)}")
        print(f"💼 初始资金: {self.initial_capital:,.2f}")

        # 回测主循环
        for i, date in enumerate(trade_dates, 1):
            if i % 20 == 0 or i == len(trade_dates):
                print(f"   进度: {i}/{len(trade_dates)} ({date})", end='\r')

            # 更新市场数据
            self.portfolio.update_market_data(data_dict, date)

            # 生成并执行订单
            if self.strategy:
                orders = self.strategy.on_bar(date, data_dict, self.portfolio.positions)
                for order in orders:
                    self.portfolio.execute_order(order, data_dict, date)

        print(f"\n\n✅ 回测完成")

        # 计算绩效
        metrics = PerformanceMetrics.calculate(self.portfolio.history)

        self.results = {
            'metrics': metrics,
            'portfolio_history': self.portfolio.history,
            'trades': self.portfolio.trades,
            'final_positions': self.portfolio.positions
        }

        self._print_results(metrics)
        return self.results

    def _print_results(self, metrics: Dict):
        """打印回测结果"""
        print("\n" + "=" * 60)
        print("📊 回测结果")
        print("=" * 60)
        print(f"  总收益率: {metrics.get('total_return', 0):.2f}%")
        print(f"  年化收益率: {metrics.get('annual_return', 0):.2f}%")
        print(f"  波动率: {metrics.get('volatility', 0):.2f}%")
        print(f"  夏普比率: {metrics.get('sharpe_ratio', 0):.3f}")
        print(f"  最大回撤: {metrics.get('max_drawdown', 0):.2f}%")
        print(f"  卡尔马比率: {metrics.get('calmar_ratio', 0):.3f}")
        print(f"  期末资产: {metrics.get('final_value', 0):,.2f}")
        print(f"  交易日数: {metrics.get('trading_days', 0)}")
        print("=" * 60)


class TradingConstraint:
    """交易约束管理器（T+1、涨跌停、停牌）"""

    def __init__(self):
        self.t_plus_1_holdings: Dict[str, str] = {}  # ts_code -> buy_date
        self.limit_prices: Dict[str, Tuple[float, float]] = {}  # ts_code -> (low, high)
        self.suspended_stocks: Set[str] = set()

    def check_t_plus_1(self, ts_code: str, current_date: str,
                      direction: OrderDirection) -> Tuple[bool, str]:
        """检查T+1规则
        当日买入的股票，当日不能卖出
        """
        if direction != OrderDirection.SELL:
            return True, ""

        if ts_code not in self.t_plus_1_holdings:
            return True, ""

        buy_date = self.t_plus_1_holdings[ts_code]
        if buy_date == current_date:
            return False, f"T+1规则: 股票 {ts_code} 当日买入，不能卖出"

        return True, ""

    def check_price_limits(self, ts_code: str, price: float,
                          direction: OrderDirection) -> Tuple[bool, str]:
        """检查涨跌停
        涨停时：无法买入，只能卖出（按涨停价）
        跌停时：无法卖出，只能买入（按跌停价）
        """
        if ts_code not in self.limit_prices:
            return True, ""

        limit_low, limit_high = self.limit_prices[ts_code]

        if direction == OrderDirection.BUY:
            if price >= limit_high:
                return False, f"涨停限制: 股票 {ts_code} 已涨停，无法买入"
        else:  # SELL
            if price <= limit_low:
                return False, f"跌停限制: 股票 {ts_code} 已跌停，无法卖出"

        return True, ""

    def check_suspended(self, ts_code: str) -> Tuple[bool, str]:
        """检查停牌"""
        if ts_code in self.suspended_stocks:
            return False, f"停牌限制: 股票 {ts_code} 已停牌"
        return True, ""

    def can_trade(self, ts_code: str, current_date: str,
                direction: OrderDirection, price: float) -> Tuple[bool, str]:
        """综合判断可否交易"""
        # 检查停牌
        ok, msg = self.check_suspended(ts_code)
        if not ok:
            return False, msg

        # 检查涨跌停
        ok, msg = self.check_price_limits(ts_code, price, direction)
        if not ok:
            return False, msg

        # 检查T+1
        ok, msg = self.check_t_plus_1(ts_code, current_date, direction)
        if not ok:
            return False, msg

        return True, ""

    def register_buy(self, ts_code: str, date: str):
        """登记买入（用于T+1）"""
        self.t_plus_1_holdings[ts_code] = date

    def set_limit_prices(self, ts_code: str, limit_low: float, limit_high: float):
        """设置涨跌停价格"""
        self.limit_prices[ts_code] = (limit_low, limit_high)

    def set_suspended(self, ts_code: str, suspended: bool = True):
        """设置停牌状态"""
        if suspended:
            self.suspended_stocks.add(ts_code)
        elif ts_code in self.suspended_stocks:
            self.suspended_stocks.remove(ts_code)

    def new_day(self, date: str):
        """新的交易日，清理T+1记录（保留非当日买入的）"""
        # 只保留不是今天买入的
        to_remove = [code for code, buy_date in self.t_plus_1_holdings.items()
                    if buy_date != date]
        for code in to_remove:
            del self.t_plus_1_holdings[code]


try:
    from .transaction_cost import TransactionCostModel
    from .position_manager import PositionManager

    class EnhancedPortfolio(Portfolio):
        """增强版组合管理"""

        def __init__(self, initial_capital: float = 1000000.0,
                    commission_rate: float = 0.0003,
                    cost_model: Optional[TransactionCostModel] = None,
                    position_manager: Optional[PositionManager] = None):
            super().__init__(initial_capital, commission_rate)
            self.cost_model = cost_model
            self.position_manager = position_manager
            self.trading_constraint = TradingConstraint()
            self.cost_details: List[Dict] = []  # 成本明细

        def execute_order_with_costs(self, order: Order, data: Dict[str, pd.DataFrame],
                                    date: str) -> Optional[Trade]:
            """执行订单，含交易成本计算"""
            # 获取当前价格
            price = 0.0
            if order.ts_code in data:
                df = data[order.ts_code]
                df_date = df[df['trade_date'] == date]
                if not df_date.empty:
                    price = float(df_date['close'].iloc[0])

            if price <= 0:
                return None

            # 检查交易约束
            can_trade, msg = self.trading_constraint.can_trade(
                order.ts_code, date, order.direction, price
            )
            if not can_trade:
                return None

            # 计算交易成本
            commission = 0.0
            slippage = 0.0
            impact_cost = 0.0
            total_cost = 0.0
            exec_price = price

            if self.cost_model:
                from .transaction_cost import OrderDirection as TCOrderDirection
                tc_direction = TCOrderDirection.BUY if order.direction == OrderDirection.BUY else TCOrderDirection.SELL

                cost_result = self.cost_model.calculate_total_cost(
                    ts_code=order.ts_code,
                    direction=tc_direction,
                    quantity=order.quantity,
                    price=price,
                    date=date
                )
                commission = cost_result.total_commission
                slippage = cost_result.slippage_cost
                impact_cost = cost_result.impact_cost
                total_cost = cost_result.total_cost

                # 调整成交价（含滑点）
                if order.direction == OrderDirection.BUY:
                    exec_price = price + (slippage / order.quantity if order.quantity > 0 else 0)
                else:
                    exec_price = price - (slippage / order.quantity if order.quantity > 0 else 0)
            else:
                # 简单计算
                trade_value = price * order.quantity
                commission = trade_value * self.commission_rate

            # 执行交易
            trade_value = exec_price * order.quantity
            if order.direction == OrderDirection.BUY:
                if self.current_capital < trade_value + commission + total_cost:
                    return None

                self.current_capital -= (trade_value + commission + total_cost)

                # 更新持仓
                if order.ts_code in self.positions:
                    pos = self.positions[order.ts_code]
                    total_quantity = pos.quantity + order.quantity
                    total_cost_value = pos.avg_price * pos.quantity + exec_price * order.quantity
                    pos.quantity = total_quantity
                    pos.avg_price = total_cost_value / total_quantity
                    pos.current_price = exec_price
                    pos.market_value = total_quantity * exec_price
                else:
                    self.positions[order.ts_code] = Position(
                        ts_code=order.ts_code,
                        quantity=order.quantity,
                        avg_price=exec_price,
                        current_price=exec_price,
                        market_value=order.quantity * exec_price,
                        pnl=0,
                        pnl_ratio=0
                    )

                # 登记买入（用于T+1）
                self.trading_constraint.register_buy(order.ts_code, date)

            else:  # SELL
                if order.ts_code not in self.positions:
                    return None

                pos = self.positions[order.ts_code]
                if pos.quantity < order.quantity:
                    return None

                # 计算卖出实现的盈亏
                realized_pnl = (exec_price - pos.avg_price) * order.quantity
                self.current_capital += (trade_value - commission - total_cost)
                pos.quantity -= order.quantity

                if pos.quantity <= 0:
                    del self.positions[order.ts_code]
                else:
                    pos.market_value = pos.quantity * exec_price

            # 记录成交
            trade = Trade(
                ts_code=order.ts_code,
                direction=order.direction,
                quantity=order.quantity,
                price=exec_price,
                time=date,
                commission=commission,
                slippage=slippage,
                impact_cost=impact_cost,
                total_cost=total_cost
            )
            self.trades.append(trade)

            # 记录成本明细
            self.cost_details.append({
                'date': date,
                'ts_code': order.ts_code,
                'direction': order.direction.value,
                'quantity': order.quantity,
                'price': exec_price,
                'commission': commission,
                'slippage': slippage,
                'impact_cost': impact_cost,
                'total_cost': total_cost
            })

            return trade

    class EnhancedBacktestEngine(BacktestEngine):
        """增强版回测引擎"""

        def __init__(self, data_manager, initial_capital: float = 1000000.0,
                    start_date: Optional[str] = None,
                    end_date: Optional[str] = None,
                    cost_model: Optional[TransactionCostModel] = None,
                    position_manager: Optional[PositionManager] = None,
                    extended_data_manager = None):
            super().__init__(data_manager, initial_capital, start_date, end_date)
            self.cost_model = cost_model
            self.position_manager = position_manager
            self.extended_data_manager = extended_data_manager
            self.enhanced_portfolio: Optional[EnhancedPortfolio] = None

        def run_enhanced(self, stock_list: Optional[List[str]] = None,
                        filter_st: bool = True,
                        filter_star: bool = True,
                        filter_suspended: bool = True) -> Dict:
            """运行增强版回测
            支持过滤ST、科创板、北交所、停牌股票
            """
            print("\n" + "=" * 60)
            print("⏳ 开始增强版回测")
            print("=" * 60)

            # 准备数据
            data_dict = self.data_manager.prepare_factor_data(
                stock_list, self.start_date, self.end_date
            )

            if not data_dict:
                print("❌ 没有数据，无法回测")
                return {}

            # 过滤股票
            filtered_stock_list = list(data_dict.keys())
            if filter_st:
                filtered_stock_list = [code for code in filtered_stock_list
                                    if not code.startswith('ST') and not code.endswith('ST')]
            if filter_star:
                # 过滤科创板（688开头）和北交所（8开头）
                filtered_stock_list = [code for code in filtered_stock_list
                                    if not code.startswith('688') and not code.startswith('8')]

            # 重新过滤数据字典
            data_dict = {code: df for code, df in data_dict.items()
                        if code in filtered_stock_list}

            if not data_dict:
                print("❌ 过滤后没有数据，无法回测")
                return {}

            # 初始化增强组合
            self.enhanced_portfolio = EnhancedPortfolio(
                initial_capital=self.initial_capital,
                cost_model=self.cost_model,
                position_manager=self.position_manager
            )

            # 获取交易日历
            first_code = list(data_dict.keys())[0]
            trade_dates = data_dict[first_code]['trade_date'].tolist()

            print(f"\n📊 回测周期: {trade_dates[0]} 至 {trade_dates[-1]}")
            print(f"📅 交易日数: {len(trade_dates)}")
            print(f"💼 初始资金: {self.initial_capital:,.2f}")
            print(f"📈 股票数量: {len(data_dict)}")

            # 回测主循环
            for i, date in enumerate(trade_dates, 1):
                if i % 20 == 0 or i == len(trade_dates):
                    print(f"   进度: {i}/{len(trade_dates)} ({date})", end='\r')

                # 新的交易日
                self.enhanced_portfolio.trading_constraint.new_day(date)

                # 更新市场数据
                self.enhanced_portfolio.update_market_data(data_dict, date)

                # 生成并执行订单
                if self.strategy:
                    orders = self.strategy.on_bar(date, data_dict, self.enhanced_portfolio.positions)
                    for order in orders:
                        self.enhanced_portfolio.execute_order_with_costs(order, data_dict, date)

            print(f"\n\n✅ 增强版回测完成")

            # 计算绩效
            metrics = PerformanceMetrics.calculate(self.enhanced_portfolio.history)

            self.results = {
                'metrics': metrics,
                'portfolio_history': self.enhanced_portfolio.history,
                'trades': self.enhanced_portfolio.trades,
                'cost_details': self.enhanced_portfolio.cost_details,
                'final_positions': self.enhanced_portfolio.positions,
                'is_enhanced': True
            }

            self._print_results(metrics)
            return self.results

except ImportError:
    # 如果依赖模块还不存在，跳过增强类的定义
    pass
