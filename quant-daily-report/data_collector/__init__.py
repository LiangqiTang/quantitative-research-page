"""
A股量化日报系统 - 数据采集模块
负责从多个数据源采集市场数据、个股数据、新闻数据等
"""

from .macro_data_collector import MacroDataCollector
from .stock_data_collector import StockDataCollector
from .news_data_collector import NewsDataCollector
from .multi_source_fetcher import MultiSourceDataFetcher as MultiSourceFetcher
from .data_validator import DataQualityValidator as DataValidator
# from .cache_manager import CacheManager  # 缺失模块: 将在后续版本中实现

__all__ = [
    'MacroDataCollector',
    'StockDataCollector',
    'NewsDataCollector',
    'MultiSourceFetcher',  # = MultiSourceDataFetcher
    'DataValidator'
    # 'CacheManager'  # 缺失模块: 将在后续版本中实现
]

__version__ = '1.0.0'
__author__ = 'Quant Research Team'