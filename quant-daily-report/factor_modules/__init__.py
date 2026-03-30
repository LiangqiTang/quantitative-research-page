"""
因子模块 - 因子挖掘和评价

本目录包含：
- factor_module.py - 基础因子库（30+个因子）
- alpha_factors.py - Alpha因子库（60+个Alpha101风格因子）
- factor_evaluator.py - 因子评价引擎（IC/IR/分组回测/因子衰减）
- factor_neutralizer.py - 因子中性化（市值/行业/Barra/正交化）

使用方式：
    from factor_modules import (
        FactorManager, FactorCalculator,
        AlphaFactorCalculator, FactorEvaluator, FactorNeutralizer
    )
"""

from .factor_module import FactorManager, FactorCalculator
from .alpha_factors import AlphaFactorCalculator, AlphaFactorType, AlphaFactorDef
from .factor_evaluator import (
    FactorEvaluator, ICMethod, ICStats, LayeredBacktestResult,
    FactorDecayResult, FactorEvaluationResult,
    prepare_factor_panel, prepare_returns_panel
)
from .factor_neutralizer import (
    FactorNeutralizer, NeutralizationMethod, NeutralizationResult
)

__all__ = [
    'FactorManager', 'FactorCalculator',
    'AlphaFactorCalculator', 'AlphaFactorType', 'AlphaFactorDef',
    'FactorEvaluator', 'ICMethod', 'ICStats', 'LayeredBacktestResult',
    'FactorDecayResult', 'FactorEvaluationResult',
    'prepare_factor_panel', 'prepare_returns_panel',
    'FactorNeutralizer', 'NeutralizationMethod', 'NeutralizationResult',
]
