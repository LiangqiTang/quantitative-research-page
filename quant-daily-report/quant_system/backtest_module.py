"""
回测模块 - 事件驱动回测引擎
包含策略执行、组合管理、绩效分析
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Callable
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
    commission: float


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
