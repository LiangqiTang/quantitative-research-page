"""
个人量化系统 - 完整可用的量化交易分析系统

基于Qlib等成熟框架经验构建，包含：
- 稳定可靠的数据来源（Tushare + Baostock）
- 30+基础因子库 + Alpha101专业因子
- 事件驱动回测引擎
- 策略构造与组合管理
- 可视化分析报告
- 专业因子评价引擎（IC/IR/分组回测）
- 因子中性化模块（市值/行业/Barra）
- 仓位管理（等权重/风险预算）
- 交易成本模型（佣金/滑点/冲击成本）
"""

__version__ = '4.0.0'
__author__ = 'Quant Research'

# 核心模块
from .data_module import DataManager
from .factor_module import FactorManager, FactorCalculator
from .backtest_module import (
    BacktestEngine,
    Strategy,
    EqualWeightStrategy,
    FactorStrategy,
    Portfolio,
    PerformanceMetrics
)
from .report_module import ReportGenerator

# 新增专业模块
from .factor_evaluator import (
    FactorEvaluator,
    ICMethod,
    ICStats,
    LayeredBacktestResult,
    FactorDecayResult,
    FactorEvaluationResult,
    prepare_factor_panel,
    prepare_returns_panel
)
from .factor_neutralizer import (
    FactorNeutralizer,
    NeutralizationMethod,
    NeutralizationResult
)
from .alpha_factors import (
    AlphaFactorCalculator,
    AlphaFactorType,
    AlphaFactorDef
)
from .transaction_cost import (
    TransactionCostModel,
    TransactionCost,
    PriceLimitHandler,
    PriceLimitCheck,
    TradingCalendar,
    SlippageModel,
    OrderDirection,
    get_average_cost_model,
    get_conservative_cost_model,
    get_aggressive_cost_model
)
from .position_manager import (
    PositionManager,
    PositionMethod,
    PositionTarget,
    PositionAllocation,
    get_simple_position_manager,
    get_institutional_position_manager
)

# 新增 v4.0 专业模块
from .portfolio_optimizer import (
    PortfolioOptimizer,
    OptimizationMethod,
    OptimizationResult,
    compare_optimization_results,
    get_simple_optimizer
)
from .risk_controller import (
    RiskController,
    StopType,
    RiskCheckResult,
    PositionEntry,
    RiskAdjustedOrder,
    get_simple_risk_controller,
    get_conservative_risk_controller,
    get_aggressive_risk_controller
)
from .metrics_extended import (
    ExtendedPerformanceMetrics,
    TradeRecord,
    calculate_performance_summary
)
from .performance_attribution import (
    BrinsonAttribution,
    FactorAttribution,
    MultiPeriodAttribution,
    BrinsonAttributionResult,
    FactorAttributionResult,
    calculate_brinson_attribution,
    calculate_factor_attribution
)
from .overfitting_detector import (
    OverfittingDetector,
    OverfittingStatus,
    TrainTestResult,
    WalkForwardResult,
    ParameterSensitivityResult,
    detect_overfitting,
    walk_forward_validation
)

__all__ = [
    # 核心模块
    'DataManager',
    'FactorManager',
    'FactorCalculator',
    'BacktestEngine',
    'Strategy',
    'EqualWeightStrategy',
    'FactorStrategy',
    'Portfolio',
    'PerformanceMetrics',
    'ReportGenerator',

    # 因子评价
    'FactorEvaluator',
    'ICMethod',
    'ICStats',
    'LayeredBacktestResult',
    'FactorDecayResult',
    'FactorEvaluationResult',
    'prepare_factor_panel',
    'prepare_returns_panel',

    # 因子中性化
    'FactorNeutralizer',
    'NeutralizationMethod',
    'NeutralizationResult',

    # Alpha因子库
    'AlphaFactorCalculator',
    'AlphaFactorType',
    'AlphaFactorDef',

    # 交易成本
    'TransactionCostModel',
    'TransactionCost',
    'PriceLimitHandler',
    'PriceLimitCheck',
    'TradingCalendar',
    'SlippageModel',
    'OrderDirection',
    'get_average_cost_model',
    'get_conservative_cost_model',
    'get_aggressive_cost_model',

    # 仓位管理
    'PositionManager',
    'PositionMethod',
    'PositionTarget',
    'PositionAllocation',
    'get_simple_position_manager',
    'get_institutional_position_manager',

    # 组合优化
    'PortfolioOptimizer',
    'OptimizationMethod',
    'OptimizationResult',
    'compare_optimization_results',
    'get_simple_optimizer',

    # 风险控制
    'RiskController',
    'StopType',
    'RiskCheckResult',
    'PositionEntry',
    'RiskAdjustedOrder',
    'get_simple_risk_controller',
    'get_conservative_risk_controller',
    'get_aggressive_risk_controller',

    # 扩展绩效指标
    'ExtendedPerformanceMetrics',
    'TradeRecord',
    'calculate_performance_summary',

    # 业绩归因
    'BrinsonAttribution',
    'FactorAttribution',
    'MultiPeriodAttribution',
    'BrinsonAttributionResult',
    'FactorAttributionResult',
    'calculate_brinson_attribution',
    'calculate_factor_attribution',

    # 过拟合检测
    'OverfittingDetector',
    'OverfittingStatus',
    'TrainTestResult',
    'WalkForwardResult',
    'ParameterSensitivityResult',
    'detect_overfitting',
    'walk_forward_validation',
]
