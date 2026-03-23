"""
A股量化日报系统 - 可视化模块
负责生成K线图、技术指标图、量化分析报告等
"""

from .kline_visualizer import KLineVisualizer
# from .technical_visualizer import TechnicalVisualizer  # 缺失模块: 将在后续版本中实现
from .report_generator import ReportGenerator
# from .dashboard_generator import DashboardGenerator  # 缺失模块: 将在后续版本中实现

__all__ = [
    'KLineVisualizer',
    'ReportGenerator'
    # 'TechnicalVisualizer',  # 缺失模块: 将在后续版本中实现
    # 'DashboardGenerator'  # 缺失模块: 将在后续版本中实现
]

__version__ = '1.0.0'
__author__ = 'Quant Research Team'