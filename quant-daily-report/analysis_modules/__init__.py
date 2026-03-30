"""
分析模块 - 风险与绩效分析

本目录包含：
- metrics_extended.py - 扩展绩效指标（Sortino/Omega/Calmar/VaR/CVaR等）
- performance_attribution.py - 业绩归因（Brinson归因/因子归因）
- overfitting_detector.py - 过拟合检测（样本内外对比/Walk Forward/参数敏感性）

使用方式：
    from analysis_modules import (
        ExtendedPerformanceMetrics, BrinsonAttribution, FactorAttribution,
        OverfittingDetector
    )
"""

from .metrics_extended import (
    ExtendedPerformanceMetrics, TradeRecord, calculate_performance_summary
)
from .performance_attribution import (
    BrinsonAttribution, FactorAttribution, MultiPeriodAttribution,
    BrinsonAttributionResult, FactorAttributionResult,
    calculate_brinson_attribution, calculate_factor_attribution
)
from .overfitting_detector import (
    OverfittingDetector, OverfittingStatus, TrainTestResult,
    WalkForwardResult, ParameterSensitivityResult,
    detect_overfitting, walk_forward_validation
)

__all__ = [
    'ExtendedPerformanceMetrics', 'TradeRecord', 'calculate_performance_summary',
    'BrinsonAttribution', 'FactorAttribution', 'MultiPeriodAttribution',
    'BrinsonAttributionResult', 'FactorAttributionResult',
    'calculate_brinson_attribution', 'calculate_factor_attribution',
    'OverfittingDetector', 'OverfittingStatus', 'TrainTestResult',
    'WalkForwardResult', 'ParameterSensitivityResult',
    'detect_overfitting', 'walk_forward_validation',
]
