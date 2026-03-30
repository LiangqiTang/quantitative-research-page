"""
报告模块 - 报告生成和研究Pipeline

本目录包含：
- report_module.py - 报告生成器
- pipeline.py - 量化研究Pipeline（因子研究/策略回测）

使用方式：
    from report_modules import ReportGenerator, QuantResearchPipeline
"""

from .report_module import ReportGenerator
from .pipeline import QuantResearchPipeline

__all__ = [
    'ReportGenerator',
    'QuantResearchPipeline',
]
