"""
回测模块 - 回测引擎和交易成本

本目录包含：
- backtest_module.py - 事件驱动回测引擎
- transaction_cost.py - 交易成本模型（佣金/滑点/冲击成本/涨跌停）
- position_manager.py - 仓位管理（等权重/风险预算/市值权重）

使用方式：
    from backtest_modules import (
        BacktestEngine, EnhancedBacktestEngine, Strategy,
        TransactionCostModel, PositionManager
    )
"""

from .backtest_module import (
    BacktestEngine, Strategy, EqualWeightStrategy, FactorStrategy,
    Portfolio, PerformanceMetrics, TradingConstraint, EnhancedPortfolio,
    EnhancedBacktestEngine
)
from .transaction_cost import (
    TransactionCostModel, TransactionCost, PriceLimitHandler,
    PriceLimitCheck, TradingCalendar, SlippageModel, OrderDirection,
    get_average_cost_model, get_conservative_cost_model,
    get_aggressive_cost_model
)
from .position_manager import (
    PositionManager, PositionMethod, PositionTarget, PositionAllocation,
    get_simple_position_manager, get_institutional_position_manager
)

__all__ = [
    'BacktestEngine', 'Strategy', 'EqualWeightStrategy', 'FactorStrategy',
    'Portfolio', 'PerformanceMetrics', 'TradingConstraint',
    'EnhancedPortfolio', 'EnhancedBacktestEngine',
    'TransactionCostModel', 'TransactionCost', 'PriceLimitHandler',
    'PriceLimitCheck', 'TradingCalendar', 'SlippageModel', 'OrderDirection',
    'get_average_cost_model', 'get_conservative_cost_model',
    'get_aggressive_cost_model',
    'PositionManager', 'PositionMethod', 'PositionTarget', 'PositionAllocation',
    'get_simple_position_manager', 'get_institutional_position_manager',
]
