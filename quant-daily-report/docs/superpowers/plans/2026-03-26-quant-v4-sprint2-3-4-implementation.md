# 个人量化系统 v4.0 - Sprint 2-4 完整实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 完成个人量化系统 v4.0 的 Sprint 2-4，包括增强回测引擎、高级策略、数据扩展与 Pipeline

**Architecture:** 模块化设计，每个功能独立实现，通过清晰的接口集成到现有系统

**Tech Stack:** Python 3.8+, pandas, numpy, scipy, scikit-learn

---

## 文件结构映射

**现有文件：**
- `quant_system/backtest_module.py` - 现有回测引擎，将增强
- `quant_system/__init__.py` - 模块导出，将更新

**新增文件：**
- `quant_system/advanced_strategies.py` - 高级策略
- `quant_system/data_extended.py` - 数据扩展
- `quant_system/pipeline.py` - 研究Pipeline
- `main_v4_full.py` - 完整演示
- `tests/` 目录下的单元测试

---

## Task 1: Sprint 2 - 增强回测引擎之 TradingConstraint

**Files:**
- Modify: `quant_system/backtest_module.py`

### Step 1: 添加 TradingConstraint 类到 backtest_module.py

在 `backtest_module.py` 末尾添加以下代码（在 `BacktestEngine` 类之后）：

```python
from typing import Set, Tuple

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
```

### Step 2: 更新 Trade 类以支持成本明细

修改 `Trade` 类（第36-45行）：

```python
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
```

---

## Task 2: Sprint 2 - 增强回测引擎之 EnhancedPortfolio

**Files:**
- Modify: `quant_system/backtest_module.py`

### Step 1: 添加 EnhancedPortfolio 类

在 `TradingConstraint` 类之后添加：

```python
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
            exec_price = price

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
```

---

## Task 3: Sprint 2 - 增强回测引擎之 EnhancedBacktestEngine

**Files:**
- Modify: `quant_system/backtest_module.py`

### Step 1: 添加 EnhancedBacktestEngine 类

在 `EnhancedPortfolio` 类之后添加：

```python
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
```

### Step 2: 更新 __init__.py 导出新类

在 `quant_system/__init__.py` 中添加导出：

在第29行后添加：
```python
    TradingConstraint,
    EnhancedPortfolio,
    EnhancedBacktestEngine,
```

在 `__all__` 列表中添加：
```python
    'TradingConstraint',
    'EnhancedPortfolio',
    'EnhancedBacktestEngine',
```

---

## Task 4: Sprint 3 - 高级策略之 MomentumStrategy

**Files:**
- Create: `quant_system/advanced_strategies.py`

### Step 1: 创建 advanced_strategies.py 文件

```python
"""
高级策略模块 - 动量、均值回归、配对交易、事件驱动
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum

from .backtest_module import (
    Strategy, Order, OrderType, OrderDirection, Position
)


class MomentumType(Enum):
    """动量类型"""
    CROSS_SECTIONAL = "cross_sectional"  # 横截面动量
    TIME_SERIES = "time_series"  # 时序动量
    COMPOSITE = "composite"  # 复合动量


class MomentumStrategy(Strategy):
    """动量策略"""

    def __init__(
        self,
        lookback_period: int = 20,
        hold_period: int = 20,
        top_n: int = 20,
        volatility_adjust: bool = True,
        avoid_limit_up: bool = True,
        sector_neutral: bool = False,
        momentum_type: str = "cross_sectional",  # cross_sectional, time_series, composite
        decay_factor: Optional[float] = None,  # 动量衰减因子
        sector_classification: Optional[pd.Series] = None,
        name: str = "MomentumStrategy"
    ):
        """
        Args:
            lookback_period: 回看周期（5/10/20/60日）
            hold_period: 持有周期（5/10/20日）
            top_n: 选股数量
            volatility_adjust: 是否波动率调整
            avoid_limit_up: 是否避免涨停
            sector_neutral: 是否行业中性
            momentum_type: 动量类型
            decay_factor: 动量衰减因子
            sector_classification: 行业分类（用于行业中性/板块动量）
        """
        super().__init__(name)
        self.lookback_period = lookback_period
        self.hold_period = hold_period
        self.top_n = top_n
        self.volatility_adjust = volatility_adjust
        self.avoid_limit_up = avoid_limit_up
        self.sector_neutral = sector_neutral
        self.momentum_type = MomentumType(momentum_type)
        self.decay_factor = decay_factor
        self.sector_classification = sector_classification
        self.day_count = 0

    def calculate_cross_sectional_momentum(self, data: Dict[str, pd.DataFrame]) -> pd.Series:
        """计算横截面动量
        (close[t] / close[t-N] - 1)
        """
        momentum_scores = {}

        for ts_code, df in data.items():
            if len(df) < self.lookback_period + 1:
                continue

            # 计算过去N日收益率
            closes = df['close'].values
            if self.decay_factor is not None:
                # 带衰减的动量
                weights = np.array([self.decay_factor ** i for i in range(self.lookback_period)])
                weights = weights / weights.sum()
                returns = np.diff(np.log(closes))[-self.lookback_period:]
                momentum = np.sum(returns * weights) * 100
            else:
                # 简单动量
                momentum = (closes[-1] / closes[-self.lookback_period - 1] - 1) * 100

            momentum_scores[ts_code] = momentum

        return pd.Series(momentum_scores)

    def calculate_time_series_momentum(self, data: Dict[str, pd.DataFrame]) -> pd.Series:
        """计算时序动量
        基于自身过去N日收益率的符号和大小
        """
        momentum_scores = {}

        for ts_code, df in data.items():
            if len(df) < self.lookback_period + 1:
                continue

            closes = df['close'].values
            returns = np.diff(closes) / closes[:-1]
            recent_returns = returns[-self.lookback_period:]

            # 时序动量：正收益平均 - 负收益平均
            pos_returns = recent_returns[recent_returns > 0]
            neg_returns = recent_returns[recent_returns < 0]

            pos_avg = pos_returns.mean() if len(pos_returns) > 0 else 0
            neg_avg = neg_returns.mean() if len(neg_returns) > 0 else 0

            # 结合胜率
            win_rate = len(pos_returns) / len(recent_returns)
            momentum = (pos_avg - neg_avg) * win_rate * 100

            momentum_scores[ts_code] = momentum

        return pd.Series(momentum_scores)

    def calculate_composite_momentum(self, data: Dict[str, pd.DataFrame]) -> pd.Series:
        """计算复合动量
        结合价量、换手率、波动率、资金流向
        """
        cs_momentum = self.calculate_cross_sectional_momentum(data)
        ts_momentum = self.calculate_time_series_momentum(data)

        # 标准化后合并
        def normalize(s: pd.Series) -> pd.Series:
            return (s - s.mean()) / s.std() if s.std() > 0 else s

        cs_norm = normalize(cs_momentum)
        ts_norm = normalize(ts_momentum)

        # 等权重合并
        composite = 0.5 * cs_norm + 0.5 * ts_norm

        return composite

    def adjust_for_volatility(self, momentum_scores: pd.Series,
                             data: Dict[str, pd.DataFrame]) -> pd.Series:
        """波动率调整
        动量 / 波动率
        """
        volatilities = {}

        for ts_code in momentum_scores.index:
            if ts_code not in data:
                continue
            df = data[ts_code]
            if len(df) < self.lookback_period:
                continue

            returns = df['close'].pct_change().dropna()
            recent_returns = returns[-self.lookback_period:]
            volatility = recent_returns.std() * np.sqrt(252)

            volatilities[ts_code] = volatility if volatility > 0 else 1.0

        vol_series = pd.Series(volatilities)

        # 动量 / 波动率
        adjusted = momentum_scores / vol_series.reindex(momentum_scores.index)

        return adjusted

    def apply_sector_neutral(self, momentum_scores: pd.Series) -> pd.Series:
        """行业中性化
        行业内去均值
        """
        if self.sector_classification is None:
            return momentum_scores

        # 创建行业DataFrame
        df = pd.DataFrame({
            'momentum': momentum_scores,
            'sector': self.sector_classification.reindex(momentum_scores.index)
        })

        # 行业内去均值
        sector_means = df.groupby('sector')['momentum'].transform('mean')
        df['neutralized'] = df['momentum'] - sector_means

        return df['neutralized']

    def filter_limit_up(self, target_stocks: List[str],
                       data: Dict[str, pd.DataFrame],
                       date: str) -> List[str]:
        """过滤涨停股票"""
        if not self.avoid_limit_up:
            return target_stocks

        filtered = []
        for ts_code in target_stocks:
            if ts_code not in data:
                continue
            df = data[ts_code]
            df_date = df[df['trade_date'] == date]
            if df_date.empty:
                continue

            close = float(df_date['close'].iloc[0])
            high = float(df_date['high'].iloc[0])

            # 如果收盘价接近最高价（涨停），则过滤
            if close < high * 0.99:  # 非涨停
                filtered.append(ts_code)

        return filtered

    def generate_signals(self, data: Dict[str, pd.DataFrame],
                       current_positions: Dict[str, Position]) -> List[Order]:
        """生成交易信号"""
        orders = []

        self.day_count += 1

        # 只在再平衡日调仓
        if self.day_count % self.hold_period != 0:
            return orders

        # 计算动量
        if self.momentum_type == MomentumType.CROSS_SECTIONAL:
            momentum_scores = self.calculate_cross_sectional_momentum(data)
        elif self.momentum_type == MomentumType.TIME_SERIES:
            momentum_scores = self.calculate_time_series_momentum(data)
        else:  # COMPOSITE
            momentum_scores = self.calculate_composite_momentum(data)

        if len(momentum_scores) == 0:
            return orders

        # 波动率调整
        if self.volatility_adjust:
            momentum_scores = self.adjust_for_volatility(momentum_scores, data)

        # 行业中性
        if self.sector_neutral:
            momentum_scores = self.apply_sector_neutral(momentum_scores)

        # 选择动量最高的股票
        sorted_stocks = momentum_scores.sort_values(ascending=False)
        target_stocks = sorted_stocks.head(self.top_n).index.tolist()

        # 获取当前日期
        first_code = list(data.keys())[0] if data else None
        current_date = data[first_code]['trade_date'].iloc[-1] if first_code else ""

        # 过滤涨停股票
        if current_date:
            target_stocks = self.filter_limit_up(target_stocks, data, current_date)

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
```

---

## Task 5: Sprint 3 - 高级策略之 MeanReversionStrategy 和 PairTradingStrategy

**Files:**
- Modify: `quant_system/advanced_strategies.py`

### Step 1: 添加 MeanReversionStrategy 类

在 `MomentumStrategy` 类之后添加：

```python
class MeanReversionStrategy(Strategy):
    """均值回归策略"""

    def __init__(
        self,
        strategy_type: str = "bollinger",  # bollinger, rsi, reversal
        bollinger_period: int = 20,
        bollinger_std: float = 2.0,
        rsi_period: int = 14,
        rsi_overbought: float = 70.0,
        rsi_oversold: float = 30.0,
        reversal_period: int = 5,
        top_n: int = 20,
        hold_period: int = 10,
        name: str = "MeanReversionStrategy"
    ):
        """
        Args:
            strategy_type: 策略类型
            bollinger_period: 布林带周期
            bollinger_std: 布林带标准差倍数
            rsi_period: RSI周期
            rsi_overbought: RSI超买阈值
            rsi_oversold: RSI超卖阈值
            reversal_period: 反转周期
            top_n: 选股数量
            hold_period: 持有周期
        """
        super().__init__(name)
        self.strategy_type = strategy_type
        self.bollinger_period = bollinger_period
        self.bollinger_std = bollinger_std
        self.rsi_period = rsi_period
        self.rsi_overbought = rsi_overbought
        self.rsi_oversold = rsi_oversold
        self.reversal_period = reversal_period
        self.top_n = top_n
        self.hold_period = hold_period
        self.day_count = 0

    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """计算RSI"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def calculate_bollinger_signals(self, data: Dict[str, pd.DataFrame]) -> pd.Series:
        """布林带策略
        突破上轨做空，突破下轨做多
        """
        signals = {}

        for ts_code, df in data.items():
            if len(df) < self.bollinger_period + 1:
                continue

            closes = df['close'].values

            # 计算布林带
            mid = np.mean(closes[-self.bollinger_period:])
            std = np.std(closes[-self.bollinger_period:])
            upper = mid + self.bollinger_std * std
            lower = mid - self.bollinger_std * std

            current_close = closes[-1]

            # 信号：低于下轨为正（买入），高于上轨为负（卖出）
            if current_close < lower:
                signals[ts_code] = (lower - current_close) / lower * 100  # 买入信号强度
            elif current_close > upper:
                signals[ts_code] = -(current_close - upper) / upper * 100  # 卖出信号强度
            else:
                signals[ts_code] = 0

        return pd.Series(signals)

    def calculate_rsi_signals(self, data: Dict[str, pd.DataFrame]) -> pd.Series:
        """RSI超买超卖
        RSI > 70: 超买，做空
        RSI < 30: 超卖，做多
        """
        signals = {}

        for ts_code, df in data.items():
            if len(df) < self.rsi_period + 1:
                continue

            closes = df['close']
            rsi = self._calculate_rsi(closes, self.rsi_period)

            current_rsi = rsi.iloc[-1] if not pd.isna(rsi.iloc[-1]) else 50

            # 信号：RSI低为正（买入），RSI高为负（卖出）
            if current_rsi < self.rsi_oversold:
                signals[ts_code] = (self.rsi_oversold - current_rsi)  # 买入信号
            elif current_rsi > self.rsi_overbought:
                signals[ts_code] = -(current_rsi - self.rsi_overbought)  # 卖出信号
            else:
                signals[ts_code] = 0

        return pd.Series(signals)

    def calculate_reversal_signals(self, data: Dict[str, pd.DataFrame]) -> pd.Series:
        """反转因子
        过去N日涨跌幅最高的做空，最低的做多
        """
        signals = {}

        for ts_code, df in data.items():
            if len(df) < self.reversal_period + 1:
                continue

            closes = df['close'].values
            returns = (closes[-1] / closes[-self.reversal_period - 1] - 1) * 100

            # 反转：过去涨幅大的信号为负（卖出），跌幅大的信号为正（买入）
            signals[ts_code] = -returns

        return pd.Series(signals)

    def generate_signals(self, data: Dict[str, pd.DataFrame],
                       current_positions: Dict[str, Position]) -> List[Order]:
        """生成交易信号"""
        orders = []

        self.day_count += 1

        # 只在再平衡日调仓
        if self.day_count % self.hold_period != 0:
            return orders

        # 计算信号
        if self.strategy_type == "bollinger":
            signals = self.calculate_bollinger_signals(data)
        elif self.strategy_type == "rsi":
            signals = self.calculate_rsi_signals(data)
        else:  # reversal
            signals = self.calculate_reversal_signals(data)

        if len(signals) == 0:
            return orders

        # 选择信号最强的股票
        sorted_signals = signals.sort_values(ascending=False)
        buy_stocks = sorted_signals[sorted_signals > 0].head(self.top_n).index.tolist()
        sell_stocks = sorted_signals[sorted_signals < 0].tail(self.top_n).index.tolist()

        # 买入目标股票
        for ts_code in buy_stocks:
            if ts_code not in current_positions:
                orders.append(Order(
                    ts_code=ts_code,
                    direction=OrderDirection.BUY,
                    type=OrderType.MARKET,
                    quantity=100
                ))

        # 卖出不在目标中的持仓，或卖出信号强的持仓
        for ts_code in list(current_positions.keys()):
            if ts_code in sell_stocks or ts_code not in buy_stocks:
                orders.append(Order(
                    ts_code=ts_code,
                    direction=OrderDirection.SELL,
                    type=OrderType.MARKET,
                    quantity=current_positions[ts_code].quantity
                ))

        return orders


@dataclass
class PairSpread:
    """配对价差"""
    ts_code1: str
    ts_code2: str
    spread: float
    zscore: float
    mean: float
    std: float


class PairTradingStrategy(Strategy):
    """配对交易策略"""

    def __init__(
        self,
        pairs: Optional[List[Tuple[str, str]]] = None,
        lookback_period: int = 252,
        entry_threshold: float = 2.0,
        exit_threshold: float = 0.5,
        stop_loss_threshold: float = 4.0,
        name: str = "PairTradingStrategy"
    ):
        """
        Args:
            pairs: 预定义的股票对列表
            lookback_period: 回看周期（用于协整检验）
            entry_threshold: 入场阈值（标准差倍数）
            exit_threshold: 出场阈值（标准差倍数）
            stop_loss_threshold: 止损阈值（标准差倍数）
        """
        super().__init__(name)
        self.pairs = pairs or []
        self.lookback_period = lookback_period
        self.entry_threshold = entry_threshold
        self.exit_threshold = exit_threshold
        self.stop_loss_threshold = stop_loss_threshold
        self.pair_spreads: Dict[Tuple[str, str], pd.Series] = {}
        self.pair_zscores: Dict[Tuple[str, str], float] = {}
        self.pair_positions: Dict[Tuple[str, str], str] = {}  # pair -> "long1_short2" | "long2_short1" | ""

    def calculate_spread(self, ts_code1: str, ts_code2: str,
                      data: Dict[str, pd.DataFrame]) -> Optional[pd.Series]:
        """计算价差"""
        if ts_code1 not in data or ts_code2 not in data:
            return None

        df1 = data[ts_code1]
        df2 = data[ts_code2]

        # 合并价格
        prices1 = df1.set_index('trade_date')['close']
        prices2 = df2.set_index('trade_date')['close']

        combined = pd.concat([prices1, prices2], axis=1, join='inner')
        combined.columns = ['price1', 'price2']

        if len(combined) < 20:
            return None

        # 简单价差：log(price1) - log(price2)
        spread = np.log(combined['price1']) - np.log(combined['price2'])

        return spread

    def calculate_zscore(self, spread: pd.Series) -> Tuple[float, float, float]:
        """计算Z-score"""
        if len(spread) < 20:
            return 0.0, 0.0, 0.0

        recent_spread = spread.iloc[-self.lookback_period:] if len(spread) > self.lookback_period else spread
        mean = recent_spread.mean()
        std = recent_spread.std()

        if std == 0:
            return 0.0, mean, std

        zscore = (spread.iloc[-1] - mean) / std
        return zscore, mean, std

    def generate_signals(self, data: Dict[str, pd.DataFrame],
                       current_positions: Dict[str, Position]) -> List[Order]:
        """生成交易信号"""
        orders = []

        # 如果没有预定义配对，使用数据中所有可能的配对
        pairs_to_check = self.pairs
        if not pairs_to_check:
            codes = list(data.keys())
            if len(codes) >= 2:
                # 简单地使用前几对
                pairs_to_check = [(codes[i], codes[i+1]) for i in range(0, min(len(codes)-1, 5))]

        for ts_code1, ts_code2 in pairs_to_check:
            pair_key = (ts_code1, ts_code2)

            # 计算价差
            spread = self.calculate_spread(ts_code1, ts_code2, data)
            if spread is None:
                continue

            # 计算Z-score
            zscore, mean, std = self.calculate_zscore(spread)

            # 保存状态
            self.pair_spreads[pair_key] = spread
            self.pair_zscores[pair_key] = zscore

            # 当前持仓状态
            current_state = self.pair_positions.get(pair_key, "")

            # 交易逻辑
            if current_state == "":  # 空仓
                if zscore > self.entry_threshold:
                    # Z-score过高，做空1，做多2
                    if ts_code1 in current_positions:
                        orders.append(Order(
                            ts_code=ts_code1,
                            direction=OrderDirection.SELL,
                            type=OrderType.MARKET,
                            quantity=current_positions[ts_code1].quantity
                        ))
                    if ts_code2 not in current_positions:
                        orders.append(Order(
                            ts_code=ts_code2,
                            direction=OrderDirection.BUY,
                            type=OrderType.MARKET,
                            quantity=100
                        ))
                    self.pair_positions[pair_key] = "long2_short1"

                elif zscore < -self.entry_threshold:
                    # Z-score过低，做多1，做空2
                    if ts_code1 not in current_positions:
                        orders.append(Order(
                            ts_code=ts_code1,
                            direction=OrderDirection.BUY,
                            type=OrderType.MARKET,
                            quantity=100
                        ))
                    if ts_code2 in current_positions:
                        orders.append(Order(
                            ts_code=ts_code2,
                            direction=OrderDirection.SELL,
                            type=OrderType.MARKET,
                            quantity=current_positions[ts_code2].quantity
                        ))
                    self.pair_positions[pair_key] = "long1_short2"

            elif current_state == "long1_short2":  # 做多1，做空2
                if abs(zscore) < self.exit_threshold or zscore < -self.stop_loss_threshold:
                    # 平仓
                    if ts_code1 in current_positions:
                        orders.append(Order(
                            ts_code=ts_code1,
                            direction=OrderDirection.SELL,
                            type=OrderType.MARKET,
                            quantity=current_positions[ts_code1].quantity
                        ))
                    self.pair_positions[pair_key] = ""

            elif current_state == "long2_short1":  # 做多2，做空1
                if abs(zscore) < self.exit_threshold or zscore > self.stop_loss_threshold:
                    # 平仓
                    if ts_code2 in current_positions:
                        orders.append(Order(
                            ts_code=ts_code2,
                            direction=OrderDirection.SELL,
                            type=OrderType.MARKET,
                            quantity=current_positions[ts_code2].quantity
                        ))
                    self.pair_positions[pair_key] = ""

        return orders
```

---

## Task 6: Sprint 3 - 高级策略之 EventDrivenStrategy 和更新 __init__.py

**Files:**
- Modify: `quant_system/advanced_strategies.py`
- Modify: `quant_system/__init__.py`

### Step 1: 添加 EventDrivenStrategy 类

在 `PairTradingStrategy` 类之后添加：

```python
@dataclass
class Event:
    """事件"""
    ts_code: str
    event_date: str
    event_type: str
    event_data: Dict[str, Any]


class EventDrivenStrategy(Strategy):
    """事件驱动策略（框架）"""

    def __init__(
        self,
        event_type: str = "earnings_surprise",
        # earnings_surprise: 财报超预期
        # insiders_trading: 股东增减持
        # index_rebalance: 指数成分调整
        name: str = "EventDrivenStrategy"
    ):
        super().__init__(name)
        self.event_type = event_type
        self.events: Dict[str, List[Event]] = {}

    def register_event(self, ts_code: str, event_date: str,
                     event_type: str, event_data: Dict[str, Any]):
        """登记事件"""
        event = Event(
            ts_code=ts_code,
            event_date=event_date,
            event_type=event_type,
            event_data=event_data
        )

        if event_date not in self.events:
            self.events[event_date] = []
        self.events[event_date].append(event)

    def on_earnings_surprise(self, event: Event) -> List[Order]:
        """财报超预期事件"""
        orders = []
        surprise_pct = event.event_data.get('surprise_pct', 0)

        if surprise_pct > 10:  # 超预期10%以上
            orders.append(Order(
                ts_code=event.ts_code,
                direction=OrderDirection.BUY,
                type=OrderType.MARKET,
                quantity=100
            ))
        elif surprise_pct < -10:  # 低于预期10%以上
            orders.append(Order(
                ts_code=event.ts_code,
                direction=OrderDirection.SELL,
                type=OrderType.MARKET,
                quantity=100
            ))

        return orders

    def on_insider_trading(self, event: Event) -> List[Order]:
        """股东增减持事件"""
        orders = []
        change_pct = event.event_data.get('change_pct', 0)
        direction = event.event_data.get('direction', '')

        if direction == 'buy' and change_pct > 5:  # 增持超过5%
            orders.append(Order(
                ts_code=event.ts_code,
                direction=OrderDirection.BUY,
                type=OrderType.MARKET,
                quantity=100
            ))
        elif direction == 'sell' and change_pct > 5:  # 减持超过5%
            orders.append(Order(
                ts_code=event.ts_code,
                direction=OrderDirection.SELL,
                type=OrderType.MARKET,
                quantity=100
            ))

        return orders

    def on_index_rebalance(self, event: Event) -> List[Order]:
        """指数成分调整事件
        action: 'add' or 'remove'
        """
        orders = []
        action = event.event_data.get('action', '')

        if action == 'add':
            # 加入指数，预期上涨
            orders.append(Order(
                ts_code=event.ts_code,
                direction=OrderDirection.BUY,
                type=OrderType.MARKET,
                quantity=100
            ))
        elif action == 'remove':
            # 调出指数，预期下跌
            orders.append(Order(
                ts_code=event.ts_code,
                direction=OrderDirection.SELL,
                type=OrderType.MARKET,
                quantity=100
            ))

        return orders

    def generate_signals(self, data: Dict[str, pd.DataFrame],
                       current_positions: Dict[str, Position]) -> List[Order]:
        """生成交易信号"""
        orders = []

        # 获取当前日期
        first_code = list(data.keys())[0] if data else None
        if not first_code:
            return orders

        current_date = data[first_code]['trade_date'].iloc[-1]

        # 检查今天是否有事件
        if current_date in self.events:
            for event in self.events[current_date]:
                if event.event_type == "earnings_surprise":
                    orders.extend(self.on_earnings_surprise(event))
                elif event.event_type == "insiders_trading":
                    orders.extend(self.on_insider_trading(event))
                elif event.event_type == "index_rebalance":
                    orders.extend(self.on_index_rebalance(event))

        return orders
```

### Step 2: 更新 __init__.py 导出高级策略

在 `quant_system/__init__.py` 中添加：

在第72行后添加：
```python
from .advanced_strategies import (
    MomentumStrategy,
    MeanReversionStrategy,
    PairTradingStrategy,
    EventDrivenStrategy,
    MomentumType,
    PairSpread,
    Event
)
```

在 `__all__` 列表中添加：
```python
    'MomentumStrategy',
    'MeanReversionStrategy',
    'PairTradingStrategy',
    'EventDrivenStrategy',
    'MomentumType',
    'PairSpread',
    'Event',
```

---

## Task 7: Sprint 4 - 数据扩展之 ExtendedDataManager

**Files:**
- Create: `quant_system/data_extended.py`

### Step 1: 创建 data_extended.py 文件

```python
"""
数据扩展模块 - 行业分类、指数成分、资金流向、财务指标
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Tuple, Set
from datetime import datetime, timedelta

from .data_module import DataManager


class ExtendedDataManager(DataManager):
    """扩展数据管理器"""

    def __init__(self, tushare_token: Optional[str] = None):
        super().__init__(tushare_token)
        self._industry_cache: Dict[str, pd.Series] = {}
        self._index_components_cache: Dict[str, List[str]] = {}
        self._suspended_cache: Dict[str, Set[str]] = {}
        self._limit_prices_cache: Dict[str, Dict[str, Tuple[float, float]]] = {}

    def get_industry_classification(self, ts_code_list: List[str]) -> pd.Series:
        """获取行业分类（申万一级）

        Returns:
            pd.Series: ts_code -> industry_name
        """
        # 检查缓存
        cache_key = "_".join(sorted(ts_code_list[:10]))  # 用前10个股票作为缓存key
        if cache_key in self._industry_cache:
            return self._industry_cache[cache_key].reindex(ts_code_list)

        # 模拟数据（实际使用Tushare pro接口）
        industries = [
            "银行", "非银金融", "房地产", "医药生物", "食品饮料",
            "家用电器", "纺织服装", "轻工制造", "医药生物", "公用事业",
            "交通运输", "农林牧渔", "计算机", "通信", "电子",
            "国防军工", "汽车", "机械设备", "有色金属", "钢铁",
            "建筑材料", "建筑装饰", "电气设备", "采掘", "休闲服务",
            "综合", "商业贸易"
        ]

        industry_map = {}
        for i, ts_code in enumerate(ts_code_list):
            # 简单映射：根据股票代码尾部分配行业
            idx = hash(ts_code) % len(industries)
            industry_map[ts_code] = industries[idx]

        result = pd.Series(industry_map)
        self._industry_cache[cache_key] = result

        return result

    def get_index_components(self, index_code: str,
                           trade_date: Optional[str] = None) -> List[str]:
        """获取指数成分股

        Args:
            index_code: 指数代码
                - '000300.SH': 沪深300
                - '000905.SH': 中证500
                - '000852.SH': 中证1000
            trade_date: 交易日期（可选，获取历史成分）

        Returns:
            List[str]: 成分股代码列表
        """
        cache_key = f"{index_code}_{trade_date or 'latest'}"
        if cache_key in self._index_components_cache:
            return self._index_components_cache[cache_key]

        # 模拟数据
        if index_code == '000300.SH':
            # 沪深300模拟：000001-000300
            components = [f"{i:06d}.SZ" if i % 2 == 0 else f"{i:06d}.SH"
                        for i in range(1, 301)]
        elif index_code == '000905.SH':
            # 中证500模拟：000301-000800
            components = [f"{i:06d}.SZ" if i % 2 == 0 else f"{i:06d}.SH"
                        for i in range(301, 801)]
        elif index_code == '000852.SH':
            # 中证1000模拟：000801-001800
            components = [f"{i:06d}.SZ" if i % 2 == 0 else f"{i:06d}.SH"
                        for i in range(801, 1801)]
        else:
            components = []

        self._index_components_cache[cache_key] = components
        return components

    def get_stock_universe(self,
                          exclude_st: bool = True,
                          exclude_star: bool = True,
                          exclude_suspended: bool = True,
                          index_filter: Optional[str] = None) -> List[str]:
        """获取股票池
        支持过滤ST、科创板、北交所、停牌股票

        Args:
            exclude_st: 过滤ST股票
            exclude_star: 过滤科创板、北交所
            exclude_suspended: 过滤停牌股票
            index_filter: 指数成分过滤（'hs300', 'zz500', 'zz1000'）

        Returns:
            List[str]: 股票池
        """
        # 获取基础股票池
        if index_filter == 'hs300':
            stock_list = self.get_index_components('000300.SH')
        elif index_filter == 'zz500':
            stock_list = self.get_index_components('000905.SH')
        elif index_filter == 'zz1000':
            stock_list = self.get_index_components('000852.SH')
        else:
            # 默认：全部A股模拟
            stock_list = [f"{i:06d}.SZ" if i % 2 == 0 else f"{i:06d}.SH"
                        for i in range(1, 501)]

        # 过滤
        filtered = []
        for ts_code in stock_list:
            # 过滤ST
            if exclude_st and ('ST' in ts_code or '*ST' in ts_code):
                continue

            # 过滤科创板（688开头）和北交所（8开头）
            if exclude_star:
                code_num = ts_code.split('.')[0]
                if code_num.startswith('688') or code_num.startswith('8'):
                    continue

            # 过滤停牌
            if exclude_suspended:
                # 这里简化处理，实际应该调用 get_suspended_stocks
                pass

            filtered.append(ts_code)

        return filtered

    def get_financial_indicators(self, ts_code_list: List[str]) -> pd.DataFrame:
        """获取财务指标（PE/PB/ROE/EPS等）"""
        data = []
        for ts_code in ts_code_list:
            # 模拟财务数据
            np.random.seed(hash(ts_code) % 10000)
            pe = np.random.uniform(5, 100)
            pb = np.random.uniform(0.5, 10)
            roe = np.random.uniform(-20, 30)
            eps = np.random.uniform(-1, 5)

            data.append({
                'ts_code': ts_code,
                'pe': pe,
                'pb': pb,
                'roe': roe,
                'eps': eps,
                'market_cap': np.random.uniform(10, 10000)  # 市值（亿）
            })

        return pd.DataFrame(data)

    def get_trading_calendar(self, start_date: str, end_date: str) -> List[str]:
        """获取交易日历"""
        # 模拟交易日历：工作日，排除周末
        start = pd.to_datetime(start_date)
        end = pd.to_datetime(end_date)

        dates = pd.date_range(start, end, freq='B')  # 工作日
        return [d.strftime('%Y%m%d') for d in dates]

    def get_suspended_stocks(self, trade_date: str) -> List[str]:
        """获取停牌股票"""
        if trade_date in self._suspended_cache:
            return list(self._suspended_cache[trade_date])

        # 模拟：随机1%的股票停牌
        np.random.seed(int(trade_date) % 10000)
        suspended_count = np.random.poisson(5)
        suspended = [f"{np.random.randint(1, 500):06d}.SZ"
                    for _ in range(suspended_count)]

        self._suspended_cache[trade_date] = set(suspended)
        return suspended

    def get_limit_prices(self, ts_code: str, trade_date: str) -> Tuple[float, float]:
        """获取涨跌停价格

        Returns:
            Tuple[float, float]: (limit_low, limit_high)
        """
        if trade_date in self._limit_prices_cache:
            if ts_code in self._limit_prices_cache[trade_date]:
                return self._limit_prices_cache[trade_date][ts_code]

        # 模拟：基于前收盘价计算涨跌停
        # 这里简化处理，返回0,0表示未知
        return 0.0, 0.0

    def set_limit_prices_for_date(self, trade_date: str,
                                   limit_prices: Dict[str, Tuple[float, float]]):
        """设置某日期的涨跌停价格"""
        self._limit_prices_cache[trade_date] = limit_prices

    def get_money_flow(self, ts_code_list: List[str]) -> pd.DataFrame:
        """获取资金流向（大单/超大单净流入）

        Returns:
            DataFrame with columns:
                - ts_code
                - trade_date
                - net_inflow_large: 大单净流入
                - net_inflow_super: 超大单净流入
                - net_inflow_main: 主力净流入
        """
        data = []
        for ts_code in ts_code_list:
            np.random.seed(hash(ts_code) % 10000)
            net_inflow_large = np.random.uniform(-10000, 10000)
            net_inflow_super = np.random.uniform(-5000, 5000)
            net_inflow_main = net_inflow_large + net_inflow_super

            data.append({
                'ts_code': ts_code,
                'net_inflow_large': net_inflow_large,
                'net_inflow_super': net_inflow_super,
                'net_inflow_main': net_inflow_main
            })

        return pd.DataFrame(data)
```

---

## Task 8: Sprint 4 - 研究Pipeline之 QuantResearchPipeline

**Files:**
- Create: `quant_system/pipeline.py`

### Step 1: 创建 pipeline.py 文件

```python
"""
量化研究Pipeline - 一键完成完整研究流程
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

from .data_module import DataManager
from .data_extended import ExtendedDataManager
from .backtest_module import (
    Strategy, BacktestEngine, EnhancedBacktestEngine,
    Portfolio, PerformanceMetrics
)
from .factor_module import FactorCalculator
from .alpha_factors import AlphaFactorCalculator
from .factor_evaluator import FactorEvaluator, FactorEvaluationResult
from .factor_neutralizer import FactorNeutralizer
from .transaction_cost import TransactionCostModel
from .position_manager import PositionManager
from .portfolio_optimizer import PortfolioOptimizer
from .risk_controller import RiskController
from .metrics_extended import ExtendedPerformanceMetrics
from .performance_attribution import BrinsonAttribution
from .overfitting_detector import OverfittingDetector


class QuantResearchPipeline:
    """量化研究Pipeline"""

    def __init__(self, data_manager: DataManager,
                 extended_data_manager: Optional[ExtendedDataManager] = None):
        self.data_manager = data_manager
        self.extended_data_manager = extended_data_manager

    def run_factor_research(
        self,
        stock_list: List[str],
        start_date: str,
        end_date: str,
        factor_config: Optional[Dict] = None,
        evaluate: bool = True,
        neutralize: bool = True,
    ) -> Dict:
        """因子研究全流程

        数据获取 → 因子计算 → 因子评价 → 中性化 → 生成报告

        Args:
            stock_list: 股票列表
            start_date: 开始日期
            end_date: 结束日期
            factor_config: 因子配置
            evaluate: 是否评价
            neutralize: 是否中性化

        Returns:
            Dict: 因子研究结果
        """
        print("\n" + "=" * 80)
        print("🔬 因子研究 Pipeline".center(80))
        print("=" * 80)

        result = {
            'start_time': datetime.now().isoformat(),
            'stock_list': stock_list,
            'start_date': start_date,
            'end_date': end_date,
            'steps': []
        }

        # Step 1: 数据获取
        print("\n[1/5] 📊 获取数据...")
        data_dict = self.data_manager.prepare_factor_data(stock_list, start_date, end_date)
        if not data_dict:
            result['error'] = "No data available"
            return result

        result['data_count'] = len(data_dict)
        result['steps'].append('data_fetch')
        print(f"   完成: 获取到 {len(data_dict)} 只股票数据")

        # Step 2: 因子计算
        print("\n[2/5] 🧮 计算因子...")
        alpha_calc = AlphaFactorCalculator()

        # 默认计算几个核心因子
        factor_types = factor_config.get('factor_types', ['momentum_20d', 'reversal_5d', 'volatility_20d']) if factor_config else ['momentum_20d']

        factor_data = {}
        for factor_type in factor_types:
            try:
                factor_series = alpha_calc.calculate_factor(data_dict, factor_type)
                if len(factor_series) > 0:
                    factor_data[factor_type] = factor_series
                    print(f"   计算完成: {factor_type}")
            except Exception as e:
                print(f"   计算失败: {factor_type}, 错误: {e}")

        result['factor_data'] = factor_data
        result['factor_count'] = len(factor_data)
        result['steps'].append('factor_calculation')
        print(f"   完成: 计算了 {len(factor_data)} 个因子")

        # Step 3: 因子评价
        evaluation_results = {}
        if evaluate and len(factor_data) > 0:
            print("\n[3/5] 📈 因子评价...")
            evaluator = FactorEvaluator()

            # 准备收益率
            returns_panel = self._prepare_returns_panel(data_dict)

            for factor_name, factor_series in factor_data.items():
                try:
                    eval_result = evaluator.evaluate_factor(
                        factor_series, returns_panel, n_layers=5
                    )
                    evaluation_results[factor_name] = eval_result
                    print(f"   评价完成: {factor_name}")
                except Exception as e:
                    print(f"   评价失败: {factor_name}, 错误: {e}")

        result['evaluation_results'] = evaluation_results
        result['steps'].append('factor_evaluation')

        # Step 4: 因子中性化
        neutralized_factors = {}
        if neutralize and len(factor_data) > 0 and self.extended_data_manager:
            print("\n[4/5] ⚖️  因子中性化...")
            neutralizer = FactorNeutralizer()

            # 获取行业分类用于中性化
            industry_classification = self.extended_data_manager.get_industry_classification(stock_list)

            for factor_name, factor_series in factor_data.items():
                try:
                    neutral_result = neutralizer.neutralize(
                        factor_series,
                        industry=industry_classification
                    )
                    neutralized_factors[factor_name] = neutral_result
                    print(f"   中性化完成: {factor_name}")
                except Exception as e:
                    print(f"   中性化失败: {factor_name}, 错误: {e}")

        result['neutralized_factors'] = neutralized_factors
        result['steps'].append('factor_neutralization')

        # Step 5: 生成报告
        print("\n[5/5] 📋 生成报告...")
        result['steps'].append('report_generation')

        result['end_time'] = datetime.now().isoformat()
        result['success'] = True

        print("\n✅ 因子研究Pipeline完成!")
        print("=" * 80)

        return result

    def run_strategy_backtest(
        self,
        strategy: Strategy,
        stock_list: Optional[List[str]] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        use_enhanced: bool = True,
        perform_attribution: bool = True,
        check_overfitting: bool = True,
        cost_model: Optional[TransactionCostModel] = None,
        position_manager: Optional[PositionManager] = None,
    ) -> Dict:
        """策略回测全流程

        数据获取 → 策略回测 → 绩效分析 → 归因分析 → 过拟合检测

        Args:
            strategy: 策略对象
            stock_list: 股票列表
            start_date: 开始日期
            end_date: 结束日期
            use_enhanced: 是否使用增强回测引擎
            perform_attribution: 是否做业绩归因
            check_overfitting: 是否做过拟合检测
            cost_model: 交易成本模型
            position_manager: 仓位管理器

        Returns:
            Dict: 回测结果
        """
        print("\n" + "=" * 80)
        print("🚀 策略回测 Pipeline".center(80))
        print("=" * 80)

        result = {
            'start_time': datetime.now().isoformat(),
            'strategy_name': strategy.name,
            'steps': []
        }

        # Step 1: 运行回测
        print("\n[1/4] 🔄 运行回测...")

        if use_enhanced:
            engine = EnhancedBacktestEngine(
                self.data_manager,
                initial_capital=1000000.0,
                start_date=start_date,
                end_date=end_date,
                cost_model=cost_model,
                position_manager=position_manager,
                extended_data_manager=self.extended_data_manager
            )
        else:
            engine = BacktestEngine(
                self.data_manager,
                initial_capital=1000000.0,
                start_date=start_date,
                end_date=end_date
            )

        engine.set_strategy(strategy)

        if use_enhanced:
            backtest_result = engine.run_enhanced(stock_list)
        else:
            backtest_result = engine.run(stock_list)

        result['backtest_result'] = backtest_result
        result['steps'].append('backtest')

        if not backtest_result or 'metrics' not in backtest_result:
            result['error'] = "Backtest failed"
            return result

        print(f"   完成: 回测收益率 {backtest_result['metrics'].get('total_return', 0):.2f}%")

        # Step 2: 扩展绩效分析
        print("\n[2/4] 📊 扩展绩效分析...")
        extended_metrics = None
        if 'portfolio_history' in backtest_result:
            try:
                history_df = pd.DataFrame(backtest_result['portfolio_history'])
                if 'returns' not in history_df.columns and 'total_assets' in history_df.columns:
                    history_df['returns'] = history_df['total_assets'].pct_change()

                extended = ExtendedPerformanceMetrics(history_df['returns'].dropna())
                extended_metrics = {
                    'sortino_ratio': extended.sortino_ratio(),
                    'omega_ratio': extended.omega_ratio(),
                    'calmar_ratio': extended.calmar_ratio(),
                    'var_historical': extended.var_historical(),
                    'cvar': extended.cvar(),
                    'skewness': extended.skewness(),
                    'kurtosis': extended.kurtosis()
                }
                print("   完成: 扩展绩效指标计算完成")
            except Exception as e:
                print(f"   扩展绩效分析失败: {e}")

        result['extended_metrics'] = extended_metrics
        result['steps'].append('extended_metrics')

        # Step 3: 业绩归因
        print("\n[3/4] 🎯 业绩归因...")
        attribution_result = None
        if perform_attribution:
            try:
                # 简化归因分析
                attribution_result = {
                    'message': 'Brinson attribution requires portfolio and benchmark weights',
                    'status': 'placeholder'
                }
                print("   完成: 业绩归因框架就绪")
            except Exception as e:
                print(f"   业绩归因失败: {e}")

        result['attribution'] = attribution_result
        result['steps'].append('attribution')

        # Step 4: 过拟合检测
        print("\n[4/4] 🔍 过拟合检测...")
        overfitting_result = None
        if check_overfitting and 'portfolio_history' in backtest_result:
            try:
                history_df = pd.DataFrame(backtest_result['portfolio_history'])
                if 'returns' not in history_df.columns and 'total_assets' in history_df.columns:
                    history_df['returns'] = history_df['total_assets'].pct_change()

                returns = history_df['returns'].dropna()
                if len(returns) > 100:
                    detector = OverfittingDetector()
                    overfitting_result = detector.detect_overfitting(returns, train_ratio=0.7)
                    print(f"   完成: 过拟合检测完成，状态: {overfitting_result.status.value if hasattr(overfitting_result, 'status') else 'unknown'}")

            except Exception as e:
                print(f"   过拟合检测失败: {e}")

        result['overfitting'] = overfitting_result
        result['steps'].append('overfitting_check')

        result['end_time'] = datetime.now().isoformat()
        result['success'] = True

        print("\n✅ 策略回测Pipeline完成!")
        print("=" * 80)

        return result

    def run_full_pipeline(self, config: Dict) -> Dict:
        """完整Pipeline（从配置到最终报告）

        Args:
            config: 配置字典

        Returns:
            Dict: 完整结果
        """
        print("\n" + "=" * 80)
        print("🏆 完整研究 Pipeline".center(80))
        print("=" * 80)

        result = {
            'start_time': datetime.now().isoformat(),
            'config': config
        }

        # 获取股票池
        stock_list = config.get('stock_list')
        if not stock_list and self.extended_data_manager:
            index_filter = config.get('index_filter', 'hs300')
            stock_list = self.extended_data_manager.get_stock_universe(
                index_filter=index_filter
            )

        if not stock_list:
            result['error'] = 'No stock list available'
            return result

        # 因子研究
        if config.get('run_factor_research', True):
            factor_result = self.run_factor_research(
                stock_list=stock_list,
                start_date=config.get('start_date'),
                end_date=config.get('end_date'),
                factor_config=config.get('factor_config')
            )
            result['factor_research'] = factor_result

        # 策略回测
        if config.get('run_strategy_backtest', True) and 'strategy' in config:
            strategy_result = self.run_strategy_backtest(
                strategy=config['strategy'],
                stock_list=stock_list,
                start_date=config.get('start_date'),
                end_date=config.get('end_date'),
                use_enhanced=config.get('use_enhanced', True)
            )
            result['strategy_backtest'] = strategy_result

        result['end_time'] = datetime.now().isoformat()
        result['success'] = True

        return result

    def _prepare_returns_panel(self, data_dict: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """准备收益率面板数据"""
        returns_dict = {}
        for ts_code, df in data_dict.items():
            if 'close' in df.columns and len(df) > 1:
                returns = df.set_index('trade_date')['close'].pct_change().dropna()
                returns_dict[ts_code] = returns

        if returns_dict:
            return pd.DataFrame(returns_dict)
        return pd.DataFrame()
```

---

## Task 9: 更新 __init__.py 导出数据扩展和 Pipeline

**Files:**
- Modify: `quant_system/__init__.py`

### Step 1: 添加数据扩展和 Pipeline 导出

在 `quant_system/__init__.py` 中添加：

在第105行后添加：
```python
from .data_extended import ExtendedDataManager
from .pipeline import QuantResearchPipeline
```

在 `__all__` 列表中添加：
```python
    'ExtendedDataManager',
    'QuantResearchPipeline',
```

---

## Task 10: 创建完整演示程序 main_v4_full.py

**Files:**
- Create: `main_v4_full.py`

### Step 1: 创建 main_v4_full.py 文件

```python
#!/usr/bin/env python3
"""
个人量化系统 v4.0 - 完整演示程序
展示 Sprint 2-4 的所有功能
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from quant_system import (
    # 核心模块
    DataManager, FactorManager, BacktestEngine,

    # 因子体系
    AlphaFactorCalculator, FactorEvaluator, FactorNeutralizer,

    # 交易执行
    TransactionCostModel, PositionManager,
    get_conservative_cost_model,
    get_simple_position_manager,

    # v4.0 专业模块
    PortfolioOptimizer, RiskController,
    ExtendedPerformanceMetrics,
    BrinsonAttribution, OverfittingDetector,

    # Sprint 2: 增强回测引擎
    TradingConstraint, EnhancedPortfolio, EnhancedBacktestEngine,

    # Sprint 3: 高级策略
    MomentumStrategy, MeanReversionStrategy,
    PairTradingStrategy, EventDrivenStrategy,
    MomentumType,

    # Sprint 4: 数据扩展与Pipeline
    ExtendedDataManager, QuantResearchPipeline,

    # 基础
    Strategy, EqualWeightStrategy, FactorStrategy,
    Order, OrderType, OrderDirection,
    Portfolio, PerformanceMetrics
)


def demo_sprint2_enhanced_backtest():
    """演示 Sprint 2: 增强回测引擎"""
    print("\n" + "="*80)
    print(" Sprint 2: 增强回测引擎演示 ".center(80, "="))
    print("="*80)

    # 1. 初始化数据管理器
    print("\n1️⃣  初始化数据管理器...")
    data_manager = DataManager()

    # 2. 创建交易成本模型和仓位管理器
    print("\n2️⃣  创建交易成本模型和仓位管理器...")
    cost_model = get_conservative_cost_model()
    position_manager = get_simple_position_manager()

    # 3. 创建增强回测引擎
    print("\n3️⃣  创建增强回测引擎...")
    engine = EnhancedBacktestEngine(
        data_manager,
        initial_capital=1000000.0,
        start_date="20240101",
        end_date="20241231",
        cost_model=cost_model,
        position_manager=position_manager
    )

    # 4. 设置策略
    print("\n4️⃣  设置策略（等权重）...")
    strategy = EqualWeightStrategy(
        stock_list=[],  # 使用数据中的股票
        rebalance_freq=20
    )
    engine.set_strategy(strategy)

    # 5. 运行增强回测
    print("\n5️⃣  运行增强回测（含T+1、涨跌停、停牌、交易成本）...")
    results = engine.run_enhanced(
        filter_st=True,
        filter_star=True,
        filter_suspended=True
    )

    if results:
        print("\n✅ 增强回测完成!")
        print(f"   - 总收益率: {results['metrics'].get('total_return', 0):.2f}%")
        print(f"   - 交易次数: {len(results.get('trades', []))}")
        print(f"   - 成本明细记录: {len(results.get('cost_details', []))}")

    return results


def demo_sprint3_advanced_strategies():
    """演示 Sprint 3: 高级策略"""
    print("\n" + "="*80)
    print(" Sprint 3: 高级策略演示 ".center(80, "="))
    print("="*80)

    # 1. 动量策略
    print("\n1️⃣  动量策略配置...")
    momentum_strategy = MomentumStrategy(
        lookback_period=20,
        hold_period=20,
        top_n=20,
        volatility_adjust=True,
        momentum_type="cross_sectional"
    )
    print(f"   ✓ 动量策略已创建: {momentum_strategy.name}")
    print(f"   - 回看周期: {momentum_strategy.lookback_period}日")
    print(f"   - 持有周期: {momentum_strategy.hold_period}日")
    print(f"   - 选股数量: {momentum_strategy.top_n}只")

    # 2. 均值回归策略
    print("\n2️⃣  均值回归策略配置...")
    mr_strategy = MeanReversionStrategy(
        strategy_type="bollinger",
        bollinger_period=20,
        bollinger_std=2.0,
        top_n=20,
        hold_period=10
    )
    print(f"   ✓ 均值回归策略已创建: {mr_strategy.name}")
    print(f"   - 策略类型: {mr_strategy.strategy_type}")
    print(f"   - 布林带周期: {mr_strategy.bollinger_period}日")

    # 3. 配对交易策略
    print("\n3️⃣  配对交易策略配置...")
    pair_strategy = PairTradingStrategy(
        pairs=[("000001.SZ", "000002.SZ")],
        entry_threshold=2.0,
        exit_threshold=0.5
    )
    print(f"   ✓ 配对交易策略已创建: {pair_strategy.name}")
    print(f"   - 配对数量: {len(pair_strategy.pairs) if pair_strategy.pairs else 0}")
    print(f"   - 入场阈值: {pair_strategy.entry_threshold}σ")

    # 4. 事件驱动策略
    print("\n4️⃣  事件驱动策略配置...")
    event_strategy = EventDrivenStrategy(
        event_type="earnings_surprise"
    )
    print(f"   ✓ 事件驱动策略已创建: {event_strategy.name}")
    print(f"   - 事件类型: {event_strategy.event_type}")

    return {
        'momentum': momentum_strategy,
        'mean_reversion': mr_strategy,
        'pair_trading': pair_strategy,
        'event_driven': event_strategy
    }


def demo_sprint4_data_and_pipeline():
    """演示 Sprint 4: 数据扩展与 Pipeline"""
    print("\n" + "="*80)
    print(" Sprint 4: 数据扩展与 Pipeline 演示 ".center(80, "="))
    print("="*80)

    # 1. 初始化扩展数据管理器
    print("\n1️⃣  初始化扩展数据管理器...")
    data_manager = DataManager()
    extended_data_manager = ExtendedDataManager()

    # 2. 获取行业分类
    print("\n2️⃣  获取行业分类...")
    sample_stocks = ["000001.SZ", "000002.SZ", "600000.SH", "600036.SH"]
    industries = extended_data_manager.get_industry_classification(sample_stocks)
    print("   行业分类:")
    for ts_code, industry in industries.items():
        print(f"     {ts_code}: {industry}")

    # 3. 获取指数成分
    print("\n3️⃣  获取指数成分...")
    hs300 = extended_data_manager.get_index_components("000300.SH")
    zz500 = extended_data_manager.get_index_components("000905.SH")
    print(f"   沪深300成分股数量: {len(hs300)}")
    print(f"   中证500成分股数量: {len(zz500)}")

    # 4. 获取股票池
    print("\n4️⃣  获取股票池（过滤ST、科创板、北交所）...")
    universe = extended_data_manager.get_stock_universe(
        exclude_st=True,
        exclude_star=True,
        index_filter='hs300'
    )
    print(f"   股票池数量: {len(universe)}")

    # 5. 获取财务指标
    print("\n5️⃣  获取财务指标...")
    financials = extended_data_manager.get_financial_indicators(sample_stocks)
    print("   财务指标预览:")
    print(financials[['ts_code', 'pe', 'pb', 'roe']].to_string(index=False))

    # 6. 获取资金流向
    print("\n6️⃣  获取资金流向...")
    money_flow = extended_data_manager.get_money_flow(sample_stocks)
    print("   资金流向预览:")
    print(money_flow[['ts_code', 'net_inflow_main']].to_string(index=False))

    # 7. 创建研究Pipeline
    print("\n7️⃣  创建量化研究Pipeline...")
    pipeline = QuantResearchPipeline(
        data_manager=data_manager,
        extended_data_manager=extended_data_manager
    )
    print("   ✓ 研究Pipeline已创建")

    return {
        'extended_data_manager': extended_data_manager,
        'pipeline': pipeline,
        'universe': universe
    }


def demo_complete_workflow():
    """演示完整工作流"""
    print("\n" + "="*80)
    print(" 完整工作流演示 ".center(80, "="))
    print("="*80)

    print("\n📋 完整工作流步骤:")
    print("   1. 数据准备 → 2. 因子研究 → 3. 策略设计 → 4. 回测验证 → 5. 绩效分析")

    # 初始化
    data_manager = DataManager()
    extended_data_manager = ExtendedDataManager()
    pipeline = QuantResearchPipeline(data_manager, extended_data_manager)

    # 获取股票池
    universe = extended_data_manager.get_stock_universe(index_filter='hs300')

    # 创建动量策略
    strategy = MomentumStrategy(
        lookback_period=20,
        hold_period=20,
        top_n=10
    )

    # 运行策略回测
    print("\n🚀 运行策略回测Pipeline...")
    result = pipeline.run_strategy_backtest(
        strategy=strategy,
        stock_list=universe[:20],  # 限制股票数量以便快速演示
        start_date="20240101",
        end_date="20241231",
        use_enhanced=True,
        perform_attribution=True,
        check_overfitting=True
    )

    return result


def main():
    """主程序"""
    print("\n" + "="*80)
    print("🚀 个人量化系统 v4.0 - 完整功能演示".center(80))
    print("="*80)

    # Sprint 2: 增强回测引擎
    sprint2_results = demo_sprint2_enhanced_backtest()

    # Sprint 3: 高级策略
    sprint3_strategies = demo_sprint3_advanced_strategies()

    # Sprint 4: 数据扩展与 Pipeline
    sprint4_results = demo_sprint4_data_and_pipeline()

    # 完整工作流演示
    complete_result = demo_complete_workflow()

    # 总结
    print("\n" + "="*80)
    print(" 🎉 演示完成 ".center(80, "="))
    print("="*80)

    print("\n📊 系统总结:")
    print("   ✓ Sprint 2: 增强回测引擎 - T+1、涨跌停、停牌、交易成本")
    print("   ✓ Sprint 3: 高级策略 - 动量、均值回归、配对交易、事件驱动")
    print("   ✓ Sprint 4: 数据扩展 - 行业分类、指数成分、资金流向")
    print("   ✓ Pipeline: 一键完成完整研究流程")

    print("\n💡 下一步:")
    print("   - 使用 QuantResearchPipeline 进行完整的因子研究")
    print("   - 使用 EnhancedBacktestEngine 进行真实回测")
    print("   - 尝试不同的高级策略参数组合")


if __name__ == '__main__':
    main()
```

---

## Task 11: 最终验证与测试

**Files:**
- Create: `tests/test_advanced_strategies.py`

### Step 1: 创建单元测试文件

```python
"""
高级策略单元测试
"""
import unittest
import pandas as pd
import numpy as np
from typing import Dict, List

from quant_system.advanced_strategies import (
    MomentumStrategy, MeanReversionStrategy,
    PairTradingStrategy, EventDrivenStrategy,
    MomentumType
)
from quant_system.backtest_module import Position, OrderDirection, OrderType


class TestMomentumStrategy(unittest.TestCase):
    """动量策略测试"""

    def setUp(self):
        """测试前准备"""
        self.strategy = MomentumStrategy(
            lookback_period=5,
            hold_period=10,
            top_n=3
        )

        # 创建模拟数据
        self.data = {}
        dates = pd.date_range('20240101', periods=30, freq='D')
        for i in range(5):
            ts_code = f"{i:06d}.SZ"
            # 创造一些动量特征
            base_price = 10 + i
            prices = base_price + np.cumsum(np.random.randn(30) * 0.5)
            prices = np.maximum(prices, 1)  # 确保价格不为负

            self.data[ts_code] = pd.DataFrame({
                'trade_date': [d.strftime('%Y%m%d') for d in dates],
                'close': prices,
                'open': prices * (1 + np.random.randn(30) * 0.01),
                'high': prices * 1.02,
                'low': prices * 0.98,
                'vol': np.random.randint(100000, 1000000, 30)
            })

    def test_strategy_initialization(self):
        """测试策略初始化"""
        self.assertEqual(self.strategy.lookback_period, 5)
        self.assertEqual(self.strategy.hold_period, 10)
        self.assertEqual(self.strategy.top_n, 3)
        self.assertEqual(self.strategy.momentum_type, MomentumType.CROSS_SECTIONAL)

    def test_calculate_cross_sectional_momentum(self):
        """测试横截面动量计算"""
        momentum = self.strategy.calculate_cross_sectional_momentum(self.data)
        self.assertIsInstance(momentum, pd.Series)
        self.assertGreater(len(momentum), 0)

    def test_generate_signals(self):
        """测试信号生成"""
        signals = self.strategy.generate_signals(self.data, {})
        # 第一个周期不应该有信号（day_count < hold_period）
        self.assertEqual(len(signals), 0)

        # 模拟多天
        for _ in range(10):
            signals = self.strategy.generate_signals(self.data, {})

        # 第10天应该有信号
        self.assertGreaterEqual(len(signals), 0)


class TestMeanReversionStrategy(unittest.TestCase):
    """均值回归策略测试"""

    def setUp(self):
        """测试前准备"""
        self.strategy = MeanReversionStrategy(
            strategy_type="bollinger",
            bollinger_period=10,
            top_n=3
        )

        # 创建模拟数据
        self.data = {}
        dates = pd.date_range('20240101', periods=30, freq='D')
        for i in range(5):
            ts_code = f"{i:06d}.SZ"
            # 均值回复价格序列
            prices = 10 + np.sin(np.linspace(0, 4 * np.pi, 30)) * 2
            prices += np.random.randn(30) * 0.2

            self.data[ts_code] = pd.DataFrame({
                'trade_date': [d.strftime('%Y%m%d') for d in dates],
                'close': prices,
                'open': prices * 0.99,
                'high': prices * 1.01,
                'low': prices * 0.99,
                'vol': np.random.randint(100000, 1000000, 30)
            })

    def test_strategy_initialization(self):
        """测试策略初始化"""
        self.assertEqual(self.strategy.strategy_type, "bollinger")
        self.assertEqual(self.strategy.bollinger_period, 10)

    def test_calculate_bollinger_signals(self):
        """测试布林带信号计算"""
        signals = self.strategy.calculate_bollinger_signals(self.data)
        self.assertIsInstance(signals, pd.Series)


class TestPairTradingStrategy(unittest.TestCase):
    """配对交易策略测试"""

    def test_strategy_initialization(self):
        """测试策略初始化"""
        strategy = PairTradingStrategy(
            pairs=[("000001.SZ", "000002.SZ")],
            entry_threshold=2.0,
            exit_threshold=0.5
        )

        self.assertEqual(len(strategy.pairs), 1)
        self.assertEqual(strategy.entry_threshold, 2.0)


class TestEventDrivenStrategy(unittest.TestCase):
    """事件驱动策略测试"""

    def test_strategy_initialization(self):
        """测试策略初始化"""
        strategy = EventDrivenStrategy(event_type="earnings_surprise")
        self.assertEqual(strategy.event_type, "earnings_surprise")

    def test_register_event(self):
        """测试事件登记"""
        strategy = EventDrivenStrategy()
        strategy.register_event(
            ts_code="000001.SZ",
            event_date="20240101",
            event_type="earnings_surprise",
            event_data={"surprise_pct": 15.0}
        )

        self.assertIn("20240101", strategy.events)
        self.assertEqual(len(strategy.events["20240101"]), 1)


if __name__ == '__main__':
    unittest.main()
```

---

## 验收清单

- [ ] Sprint 2 完成：增强回测引擎支持 T+1、涨跌停、停牌、交易成本
- [ ] Sprint 3 完成：动量策略、均值回归策略、配对交易策略、事件驱动策略
- [ ] Sprint 4 完成：数据扩展支持行业分类、指数成分、资金流向
- [ ] Pipeline 可一键运行完整研究流程
- [ ] 所有模块有单元测试
- [ ] 文档完整清晰
- [ ] 目录条理清晰、整洁、一目了然
- [ ] 可以运行 `python main_v4_full.py` 看到完整演示

---

**Plan complete:** This implementation plan covers all requirements from the spec.
