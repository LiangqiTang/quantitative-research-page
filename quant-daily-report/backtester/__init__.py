"""
A股量化日报系统 - 回测模块
基于Qlib的量化策略回测引擎
"""

# 使用延迟导入，避免依赖缺失导致模块无法导入
__all__ = [
    'QlibBacktestEngine',
    'StrategyAnalyzer',
    'PerformanceAnalyzer',
    'ParameterOptimizer',
    'get_qlib_backtester'
]

# 保持向后兼容性
__version__ = '1.0.0'
__author__ = 'Quant Research Team'

# 延迟导入实现
_strategy_analyzer = None
_performance_analyzer = None
_parameter_optimizer = None


def __getattr__(name):
    global _strategy_analyzer, _performance_analyzer, _parameter_optimizer

    if name == 'StrategyAnalyzer':
        if _strategy_analyzer is None:
            try:
                from .strategy_analyzer import StrategyAnalyzer
                _strategy_analyzer = StrategyAnalyzer
            except ImportError as e:
                raise ImportError(
                    "无法导入StrategyAnalyzer，请先安装依赖:\n"
                    "pip install scipy matplotlib seaborn"
                ) from e
        return _strategy_analyzer

    elif name == 'PerformanceAnalyzer':
        if _performance_analyzer is None:
            try:
                from .performance_analyzer import PerformanceAnalyzer
                _performance_analyzer = PerformanceAnalyzer
            except ImportError as e:
                raise ImportError(
                    "无法导入PerformanceAnalyzer，请先安装依赖:\n"
                    "pip install numpy pandas"
                ) from e
        return _performance_analyzer

    elif name == 'ParameterOptimizer':
        if _parameter_optimizer is None:
            try:
                from .parameter_optimizer import ParameterOptimizer
                _parameter_optimizer = ParameterOptimizer
            except ImportError as e:
                raise ImportError(
                    "无法导入ParameterOptimizer，请先安装依赖:\n"
                    "pip install numpy pandas scipy"
                ) from e
        return _parameter_optimizer

    elif name == 'QlibBacktestEngine':
        return get_qlib_backtester()

    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


def get_qlib_backtester():
    """
    获取Qlib回测引擎
    需要先安装Qlib: pip install qlib==0.8.6
    """
    try:
        from .qlib_backtester import QlibBacktestEngine
        return QlibBacktestEngine
    except ImportError as e:
        raise ImportError(
            "无法导入Qlib回测引擎，请先安装Qlib:\n"
            "pip install qlib==0.8.6\n"
            "然后初始化数据:\n"
            "python -m qlib.init --reset"
        ) from e