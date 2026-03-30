"""
高级策略模块 - 动量、均值回归、配对交易、事件驱动
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum

from backtest_modules.backtest_module import (
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
