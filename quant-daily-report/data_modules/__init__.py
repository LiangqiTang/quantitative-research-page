"""
数据模块 - 数据获取和管理

本目录包含：
- data_module.py - 基础数据管理器（Tushare/Baostock）
- data_extended.py - 扩展数据管理器（行业分类、指数成分等）

使用方式：
    from data_modules import DataManager, ExtendedDataManager
"""

from .data_module import DataManager
from .data_extended import ExtendedDataManager

__all__ = [
    'DataManager',
    'ExtendedDataManager',
]
