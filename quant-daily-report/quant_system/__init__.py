"""
个人量化系统 - 完整可用的量化交易分析系统

基于Qlib等成熟框架经验构建，包含：
- 稳定可靠的数据来源（Tushare + Baostock）
- 30+基础因子库
- 事件驱动回测引擎
- 策略构造与组合管理
- 可视化分析报告
"""

__version__ = '2.0.0'
__author__ = 'Quant Research'

from .data_module import DataManager
from .factor_module import FactorManager
from .backtest_module import BacktestEngine
from .report_module import ReportGenerator

__all__ = [
    'DataManager',
    'FactorManager',
    'BacktestEngine',
    'ReportGenerator'
]
