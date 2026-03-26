# 个人量化系统 v4.0 - Sprint 2-4 完整实现设计方案

**日期**: 2026-03-26
**版本**: v4.0.0
**作者**: Quant Research

---

## 1. 概述

### 1.1 目标
完整实现原始计划的Sprint 2-4，打造功能全面、专业、A股适配的v4.0量化系统。

### 1.2 Scope（范围界定）

**包含**:
- Sprint 2：增强回测引擎（T+1、涨跌停、停牌、交易成本、仓位管理）
- Sprint 3：高级策略（动量策略 + 配对交易 + 均值回归 + 事件驱动框架）
- Sprint 4：数据扩展 + Pipeline + 报告增强

**暂不包含**（留到C阶段机器学习）:
- 机器学习因子挖掘
- 深度学习预测
- 强化学习

**重点强化**（针对A股日频）:
- T+1交易规则约束
- 涨跌停处理
- 停牌处理
- 行业分类（申万一级）
- 指数成分（沪深300、中证500、中证1000）
- 板块轮动支持
- 资金流向因子

---

## 2. Sprint 2: 增强回测引擎设计

### 2.1 文件修改
- `quant_system/backtest_module.py` - 重构增强

### 2.2 新增类

#### 2.2.1 TradingConstraint - 交易约束管理器
```python
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

    def check_price_limits(self, ts_code: str, price: float,
                          direction: OrderDirection) -> Tuple[bool, str]:
        """检查涨跌停
        涨停时：无法买入，只能卖出（按涨停价）
        跌停时：无法卖出，只能买入（按跌停价）
        """

    def check_suspended(self, ts_code: str) -> Tuple[bool, str]:
        """检查停牌"""

    def can_trade(self, ts_code: str, current_date: str,
                direction: OrderDirection, price: float) -> Tuple[bool, str]:
        """综合判断可否交易"""

    def register_buy(self, ts_code: str, date: str):
        """登记买入（用于T+1）"""
```

#### 2.2.2 EnhancedPortfolio - 增强版组合管理
```python
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
```

#### 2.2.3 EnhancedBacktestEngine - 增强版回测引擎
```python
class EnhancedBacktestEngine(BacktestEngine):
    """增强版回测引擎"""

    def __init__(self, data_manager, initial_capital: float = 1000000.0,
                 start_date: Optional[str] = None,
                 end_date: Optional[str] = None,
                 cost_model: Optional[TransactionCostModel] = None,
                 position_manager: Optional[PositionManager] = None,
                 extended_data_manager: Optional[ExtendedDataManager] = None):
        super().__init__(data_manager, initial_capital, start_date, end_date)
        self.cost_model = cost_model
        self.position_manager = position_manager
        self.extended_data_manager = extended_data_manager

    def run_enhanced(self, stock_list: Optional[List[str]] = None,
                    filter_st: bool = True,
                    filter_star: bool = True,
                    filter_suspended: bool = True) -> Dict:
        """运行增强版回测
        支持过滤ST、科创板、北交所、停牌股票
        """
```

### 2.3 关键功能点

1. **T+1规则**:
   - 当日买入的股票，当日不能卖出
   - 使用 `t_plus_1_holdings` 字典标记买入日期
   - 卖出时检查日期

2. **涨跌停处理**:
   - 涨停时：无法买入，只能卖出（按涨停价）
   - 跌停时：无法卖出，只能买入（按跌停价）
   - 支持"排队"模拟（如果有成交量）

3. **停牌处理**:
   - 停牌期间无法交易
   - 复牌后第一时间处理挂单

4. **交易成本集成**:
   - 订单执行时实时计算佣金、滑点、冲击成本
   - 记录到 `Trade` 对象的 `commission`、`slippage`、`impact_cost` 字段

---

## 3. Sprint 3: 高级策略设计

### 3.1 新增文件
- `quant_system/advanced_strategies.py`

### 3.2 策略类（按优先级排序）

#### 3.2.1 MomentumStrategy - 动量策略（最高优先级）
```python
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
        sector_classification: Optional[pd.Series] = None
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
        self.lookback_period = lookback_period
        self.hold_period = hold_period
        self.top_n = top_n
        self.volatility_adjust = volatility_adjust
        self.avoid_limit_up = avoid_limit_up
        self.sector_neutral = sector_neutral
        self.momentum_type = momentum_type
        self.decay_factor = decay_factor
        self.sector_classification = sector_classification
        self.day_count = 0

    def calculate_cross_sectional_momentum(self, data: Dict[str, pd.DataFrame]) -> pd.Series:
        """计算横截面动量
        (close[t] / close[t-N] - 1)
        """

    def calculate_time_series_momentum(self, data: Dict[str, pd.DataFrame]) -> pd.Series:
        """计算时序动量
        基于自身过去N日收益率的符号和大小
        """

    def calculate_composite_momentum(self, data: Dict[str, pd.DataFrame]) -> pd.Series:
        """计算复合动量
        结合价量、换手率、波动率、资金流向
        """

    def adjust_for_volatility(self, momentum_scores: pd.Series,
                             data: Dict[str, pd.DataFrame]) -> pd.Series:
        """波动率调整
        动量 / 波动率
        """

    def apply_sector_neutral(self, momentum_scores: pd.Series) -> pd.Series:
        """行业中性化
        行业内去均值
        """

    def filter_limit_up(self, target_stocks: List[str],
                       data: Dict[str, pd.DataFrame],
                       date: str) -> List[str]:
        """过滤涨停股票"""

    def generate_signals(self, data: Dict[str, pd.DataFrame],
                       current_positions: Dict[str, Position]) -> List[Order]:
        """生成交易信号"""
```

#### 3.2.2 MeanReversionStrategy - 均值回归策略
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

    def calculate_bollinger_signals(self, data: Dict[str, pd.DataFrame]) -> pd.Series:
        """布林带策略
        突破上轨做空，突破下轨做多
        """

    def calculate_rsi_signals(self, data: Dict[str, pd.DataFrame]) -> pd.Series:
        """RSI超买超卖
        RSI > 70: 超买，做空
        RSI < 30: 超卖，做多
        """

    def calculate_reversal_signals(self, data: Dict[str, pd.DataFrame]) -> pd.Series:
        """反转因子
        过去N日涨跌幅最高的做空，最低的做多
        """
```

#### 3.2.3 PairTradingStrategy - 配对交易策略
```python
class PairTradingStrategy(Strategy):
    """配对交易策略"""

    def __init__(
        self,
        pairs: Optional[List[Tuple[str, str]]] = None,
        lookback_period: int = 252,
        entry_threshold: float = 2.0,
        exit_threshold: float = 0.5,
        stop_loss_threshold: float = 4.0,
    ):
        """
        Args:
            pairs: 预定义的股票对列表
            lookback_period: 回看周期（用于协整检验）
            entry_threshold: 入场阈值（标准差倍数）
            exit_threshold: 出场阈值（标准差倍数）
            stop_loss_threshold: 止损阈值（标准差倍数）
        """
        self.pairs = pairs
        self.lookback_period = lookback_period
        self.entry_threshold = entry_threshold
        self.exit_threshold = exit_threshold
        self.stop_loss_threshold = stop_loss_threshold
        self.pair_spreads: Dict[Tuple[str, str], pd.Series] = {}
        self.pair_zscores: Dict[Tuple[str, str], float] = {}

    def check_cointegration(self, ts_code1: str, ts_code2: str,
                           data: Dict[str, pd.DataFrame]) -> Tuple[bool, float]:
        """协整检验（Engle-Granger）"""

    def calculate_spread(self, ts_code1: str, ts_code2: str,
                      data: Dict[str, pd.DataFrame]) -> pd.Series:
        """计算价差"""

    def calculate_zscore(self, spread: pd.Series) -> float:
        """计算Z-score"""

    def generate_signals(self, data: Dict[str, pd.DataFrame],
                       current_positions: Dict[str, Position]) -> List[Order]:
        """生成交易信号"""
```

#### 3.2.4 EventDrivenStrategy - 事件驱动策略框架
```python
class EventDrivenStrategy(Strategy):
    """事件驱动策略（框架）"""

    def __init__(
        self,
        event_type: str = "earnings_surprise",
        # earnings_surprise: 财报超预期
        # insiders_trading: 股东增减持
        # index_rebalance: 指数成分调整
    ):
        self.event_type = event_type
        self.events: Dict[str, List[Dict]] = {}

    def register_event(self, ts_code: str, event_date: str,
                     event_type: str, event_data: Dict):
        """登记事件"""

    def on_earnings_surprise(self, ts_code: str, surprise_pct: float) -> List[Order]:
        """财报超预期事件"""

    def on_insider_trading(self, ts_code: str, change_pct: float,
                          direction: str) -> List[Order]:
        """股东增减持事件"""

    def on_index_rebalance(self, ts_code: str, action: str) -> List[Order]:
        """指数成分调整事件
        action: 'add' or 'remove'
        """
```

---

## 4. Sprint 4: 数据扩展与Pipeline设计

### 4.1 新增文件
- `quant_system/data_extended.py` - 数据扩展
- `quant_system/pipeline.py` - 研究Pipeline

### 4.2 data_extended.py 核心类

```python
class ExtendedDataManager(DataManager):
    """扩展数据管理器"""

    def get_industry_classification(self, ts_code_list: List[str]) -> pd.Series:
        """获取行业分类（申万一级）

        Returns:
            pd.Series: ts_code -> industry_name
        """

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

    def get_financial_indicators(self, ts_code_list: List[str]) -> pd.DataFrame:
        """获取财务指标（PE/PB/ROE/EPS等）"""

    def get_trading_calendar(self, start_date: str, end_date: str) -> List[str]:
        """获取交易日历"""

    def get_suspended_stocks(self, trade_date: str) -> List[str]:
        """获取停牌股票"""

    def get_limit_prices(self, ts_code: str, trade_date: str) -> Tuple[float, float]:
        """获取涨跌停价格

        Returns:
            Tuple[float, float]: (limit_low, limit_high)
        """

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
```

### 4.3 pipeline.py 核心类

```python
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

    def run_strategy_backtest(
        self,
        strategy: Strategy,
        stock_list: Optional[List[str]] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        use_enhanced: bool = True,
        perform_attribution: bool = True,
        check_overfitting: bool = True,
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

        Returns:
            Dict: 回测结果
        """

    def run_full_pipeline(self, config: Dict) -> Dict:
        """完整Pipeline（从配置到最终报告）

        Args:
            config: 配置字典

        Returns:
            Dict: 完整结果
        """
```

---

## 5. 文件结构（完成后）

```
quant-daily-report/
├── quant_system/
│   ├── __init__.py              # ✅ 已更新 v4.0.0
│   ├── data_module.py           # 现有
│   ├── factor_module.py         # 现有
│   ├── backtest_module.py       # ⏳ 待增强
│   ├── report_module.py         # ⏳ 待增强
│   │
│   ├── factor_evaluator.py      # ✅ 已完成
│   ├── factor_neutralizer.py    # ✅ 已完成
│   ├── alpha_factors.py         # ✅ 已完成
│   ├── transaction_cost.py      # ✅ 已完成
│   ├── position_manager.py      # ✅ 已完成
│   ├── portfolio_optimizer.py   # ✅ 已完成
│   ├── risk_controller.py       # ✅ 已完成
│   ├── metrics_extended.py      # ✅ 已完成
│   ├── performance_attribution.py # ✅ 已完成
│   ├── overfitting_detector.py  # ✅ 已完成
│   │
│   ├── advanced_strategies.py   # ⏳ 新增
│   ├── data_extended.py         # ⏳ 新增
│   └── pipeline.py              # ⏳ 新增
│
├── main_v4.py                   # ✅ 已完成（演示）
├── main_v4_full.py              # ⏳ 新增（完整Pipeline演示）
└── show_system_features.py      # ✅ 已完成
```

---

## 6. 实施顺序

1. **Phase 1**: Sprint 2 - 增强回测引擎
   - 添加 TradingConstraint 类
   - 添加 EnhancedPortfolio 类
   - 添加 EnhancedBacktestEngine 类
   - 更新 __init__.py

2. **Phase 2**: Sprint 3 - 高级策略
   - 添加 MomentumStrategy（最高优先级）
   - 添加 MeanReversionStrategy
   - 添加 PairTradingStrategy
   - 添加 EventDrivenStrategy 框架
   - 更新 __init__.py

3. **Phase 3**: Sprint 4 - 数据扩展与Pipeline
   - 添加 ExtendedDataManager
   - 添加 QuantResearchPipeline
   - 更新 __init__.py

4. **Phase 4**: 报告增强与演示
   - 增强 report_module.py
   - 创建 main_v4_full.py
   - 测试与文档

---

## 7. 验收标准

- [ ] 增强回测引擎支持T+1、涨跌停、停牌
- [ ] 动量策略可用，支持横截面/时序/复合动量
- [ ] 数据扩展支持行业分类、指数成分、资金流向
- [ ] Pipeline可一键运行完整研究流程
- [ ] 所有模块有单元测试
- [ ] 文档完整清晰
- [ ] 目录条理清晰、整洁、一目了然

---

**设计完成日期**: 2026-03-26
**设计状态**: 待审核
