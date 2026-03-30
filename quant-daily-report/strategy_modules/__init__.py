"""
策略模块 - 策略构架和组合优化

本目录包含：
- portfolio_optimizer.py - 组合优化器（最小方差/最大夏普/风险平价等）
- risk_controller.py - 风险控制器（止损止盈/回撤控制/波动率控制）
- advanced_strategies.py - 高级策略（动量/均值回归/配对交易/事件驱动）

使用方式：
    from strategy_modules import (
        PortfolioOptimizer, RiskController,
        MomentumStrategy, MeanReversionStrategy, PairTradingStrategy
    )
"""

from .portfolio_optimizer import (
    PortfolioOptimizer, OptimizationMethod, OptimizationResult,
    compare_optimization_results, get_simple_optimizer
)
from .risk_controller import (
    RiskController, StopType, RiskCheckResult, PositionEntry, RiskAdjustedOrder,
    get_simple_risk_controller, get_conservative_risk_controller,
    get_aggressive_risk_controller
)
from .advanced_strategies import (
    MomentumStrategy, MeanReversionStrategy, PairTradingStrategy,
    EventDrivenStrategy, MomentumType, PairSpread, Event
)

__all__ = [
    'PortfolioOptimizer', 'OptimizationMethod', 'OptimizationResult',
    'compare_optimization_results', 'get_simple_optimizer',
    'RiskController', 'StopType', 'RiskCheckResult', 'PositionEntry',
    'RiskAdjustedOrder', 'get_simple_risk_controller',
    'get_conservative_risk_controller', 'get_aggressive_risk_controller',
    'MomentumStrategy', 'MeanReversionStrategy', 'PairTradingStrategy',
    'EventDrivenStrategy', 'MomentumType', 'PairSpread', 'Event',
]
