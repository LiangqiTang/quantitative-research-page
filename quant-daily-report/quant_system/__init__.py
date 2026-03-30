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

v4.0 目录结构（按功能分类）：
- 01_data/ - 数据获取相关（索引）→ 实际代码在 data_modules/
- 02_factors/ - 因子挖掘相关（索引）→ 实际代码在 factor_modules/
- 03_strategy/ - 策略构架相关（索引）→ 实际代码在 strategy_modules/
- 04_backtest/ - 回测引擎相关（索引）→ 实际代码在 backtest_modules/
- 05_analysis/ - 分析工具相关（索引）→ 实际代码在 analysis_modules/
- 06_report/ - 报告生成相关（索引）→ 实际代码在 report_modules/
- 07_ui/ - 可视化界面
- 08_tests/ - 系统功能测试
- 09_docs/ - 功能介绍和设计文档
- 10_demos/ - 演示脚本

向后兼容性说明：
- 本模块保持完整的向后兼容性
- 旧代码 'from quant_system import X' 仍然正常工作
- 新代码推荐使用 'from data_modules import X' 等方式

注意：实际模块文件已按功能分类移动到 xxx_modules/ 目录中，
01_data/ ~ 06_report/ 目录提供分类索引，方便查找。
"""

__version__ = '4.0.0'
__author__ = 'Quant Research'

# 核心模块（从新的模块目录导入，保持向后兼容）
from data_modules import DataManager, ExtendedDataManager
from factor_modules import (
    FactorManager, FactorCalculator,
    AlphaFactorCalculator, AlphaFactorType, AlphaFactorDef,
    FactorEvaluator, ICMethod, ICStats, LayeredBacktestResult,
    FactorDecayResult, FactorEvaluationResult,
    prepare_factor_panel, prepare_returns_panel,
    FactorNeutralizer, NeutralizationMethod, NeutralizationResult
)
from backtest_modules import (
    BacktestEngine, Strategy, EqualWeightStrategy, FactorStrategy,
    Portfolio, PerformanceMetrics, TradingConstraint, EnhancedPortfolio,
    EnhancedBacktestEngine,
    TransactionCostModel, TransactionCost, PriceLimitHandler,
    PriceLimitCheck, TradingCalendar, SlippageModel, OrderDirection,
    get_average_cost_model, get_conservative_cost_model,
    get_aggressive_cost_model,
    PositionManager, PositionMethod, PositionTarget, PositionAllocation,
    get_simple_position_manager, get_institutional_position_manager
)
from strategy_modules import (
    PortfolioOptimizer, OptimizationMethod, OptimizationResult,
    compare_optimization_results, get_simple_optimizer,
    RiskController, StopType, RiskCheckResult, PositionEntry,
    RiskAdjustedOrder, get_simple_risk_controller,
    get_conservative_risk_controller, get_aggressive_risk_controller,
    MomentumStrategy, MeanReversionStrategy, PairTradingStrategy,
    EventDrivenStrategy, MomentumType, PairSpread, Event
)
from analysis_modules import (
    ExtendedPerformanceMetrics, TradeRecord, calculate_performance_summary,
    BrinsonAttribution, FactorAttribution, MultiPeriodAttribution,
    BrinsonAttributionResult, FactorAttributionResult,
    calculate_brinson_attribution, calculate_factor_attribution,
    OverfittingDetector, OverfittingStatus, TrainTestResult,
    WalkForwardResult, ParameterSensitivityResult,
    detect_overfitting, walk_forward_validation
)
from report_modules import ReportGenerator, QuantResearchPipeline

__all__ = [
    # 数据模块
    'DataManager',
    'ExtendedDataManager',

    # 因子模块
    'FactorManager',
    'FactorCalculator',
    'AlphaFactorCalculator',
    'AlphaFactorType',
    'AlphaFactorDef',
    'FactorEvaluator',
    'ICMethod',
    'ICStats',
    'LayeredBacktestResult',
    'FactorDecayResult',
    'FactorEvaluationResult',
    'prepare_factor_panel',
    'prepare_returns_panel',
    'FactorNeutralizer',
    'NeutralizationMethod',
    'NeutralizationResult',

    # 回测模块
    'BacktestEngine',
    'Strategy',
    'EqualWeightStrategy',
    'FactorStrategy',
    'Portfolio',
    'PerformanceMetrics',
    'ReportGenerator',
    'TradingConstraint',
    'EnhancedPortfolio',
    'EnhancedBacktestEngine',

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

    # 高级策略
    'MomentumStrategy',
    'MeanReversionStrategy',
    'PairTradingStrategy',
    'EventDrivenStrategy',
    'MomentumType',
    'PairSpread',
    'Event',

    # Pipeline
    'QuantResearchPipeline',
]
