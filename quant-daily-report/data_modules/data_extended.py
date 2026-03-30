"""
数据扩展模块 - 行业分类、指数成分、资金流向、财务指标
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Tuple, Set
from datetime import datetime, timedelta

from .data_module import DataManager


class ExtendedDataManager(DataManager):
    """扩展数据管理器"""

    def __init__(self, tushare_token: Optional[str] = None):
        super().__init__(tushare_token)
        self._industry_cache: Dict[str, pd.Series] = {}
        self._index_components_cache: Dict[str, List[str]] = {}
        self._suspended_cache: Dict[str, Set[str]] = {}
        self._limit_prices_cache: Dict[str, Dict[str, Tuple[float, float]]] = {}

    def get_industry_classification(self, ts_code_list: List[str]) -> pd.Series:
        """获取行业分类（申万一级）

        Returns:
            pd.Series: ts_code -> industry_name
        """
        # 检查缓存
        cache_key = "_".join(sorted(ts_code_list[:10]))  # 用前10个股票作为缓存key
        if cache_key in self._industry_cache:
            return self._industry_cache[cache_key].reindex(ts_code_list)

        # 模拟数据（实际使用Tushare pro接口）
        industries = [
            "银行", "非银金融", "房地产", "医药生物", "食品饮料",
            "家用电器", "纺织服装", "轻工制造", "医药生物", "公用事业",
            "交通运输", "农林牧渔", "计算机", "通信", "电子",
            "国防军工", "汽车", "机械设备", "有色金属", "钢铁",
            "建筑材料", "建筑装饰", "电气设备", "采掘", "休闲服务",
            "综合", "商业贸易"
        ]

        industry_map = {}
        for i, ts_code in enumerate(ts_code_list):
            # 简单映射：根据股票代码尾部分配行业
            idx = hash(ts_code) % len(industries)
            industry_map[ts_code] = industries[idx]

        result = pd.Series(industry_map)
        self._industry_cache[cache_key] = result

        return result

    def get_index_components(self, index_code: str,
                           trade_date: Optional[str] = None) -> List[str]:
        """获取指数成分股

        Args:
            index_code: 指数代码
                - '000300.SH': 沪深300
                - '000905.SH': 中证500
                - '000852.SH': 中证1000
            trade_date: 交易日期（可选，获取历史成分）

        Returns:
            List[str]: 成分股代码列表
        """
        cache_key = f"{index_code}_{trade_date or 'latest'}"
        if cache_key in self._index_components_cache:
            return self._index_components_cache[cache_key]

        # 模拟数据
        if index_code == '000300.SH':
            # 沪深300模拟：000001-000300
            components = [f"{i:06d}.SZ" if i % 2 == 0 else f"{i:06d}.SH"
                        for i in range(1, 301)]
        elif index_code == '000905.SH':
            # 中证500模拟：000301-000800
            components = [f"{i:06d}.SZ" if i % 2 == 0 else f"{i:06d}.SH"
                        for i in range(301, 801)]
        elif index_code == '000852.SH':
            # 中证1000模拟：000801-001800
            components = [f"{i:06d}.SZ" if i % 2 == 0 else f"{i:06d}.SH"
                        for i in range(801, 1801)]
        else:
            components = []

        self._index_components_cache[cache_key] = components
        return components

    def get_stock_universe(self,
                          exclude_st: bool = True,
                          exclude_star: bool = True,
                          exclude_suspended: bool = True,
                          index_filter: Optional[str] = None) -> List[str]:
        """获取股票池
        支持过滤ST、科创板、北交所、停牌股票

        Args:
            exclude_st: 过滤ST股票
            exclude_star: 过滤科创板、北交所
            exclude_suspended: 过滤停牌股票
            index_filter: 指数成分过滤（'hs300', 'zz500', 'zz1000'）

        Returns:
            List[str]: 股票池
        """
        # 获取基础股票池
        if index_filter == 'hs300':
            stock_list = self.get_index_components('000300.SH')
        elif index_filter == 'zz500':
            stock_list = self.get_index_components('000905.SH')
        elif index_filter == 'zz1000':
            stock_list = self.get_index_components('000852.SH')
        else:
            # 默认：全部A股模拟
            stock_list = [f"{i:06d}.SZ" if i % 2 == 0 else f"{i:06d}.SH"
                        for i in range(1, 501)]

        # 过滤
        filtered = []
        for ts_code in stock_list:
            # 过滤ST
            if exclude_st and ('ST' in ts_code or '*ST' in ts_code):
                continue

            # 过滤科创板（688开头）和北交所（8开头）
            if exclude_star:
                code_num = ts_code.split('.')[0]
                if code_num.startswith('688') or code_num.startswith('8'):
                    continue

            # 过滤停牌
            if exclude_suspended:
                # 这里简化处理，实际应该调用 get_suspended_stocks
                pass

            filtered.append(ts_code)

        return filtered

    def get_financial_indicators(self, ts_code_list: List[str]) -> pd.DataFrame:
        """获取财务指标（PE/PB/ROE/EPS等）"""
        data = []
        for ts_code in ts_code_list:
            # 模拟财务数据
            np.random.seed(hash(ts_code) % 10000)
            pe = np.random.uniform(5, 100)
            pb = np.random.uniform(0.5, 10)
            roe = np.random.uniform(-20, 30)
            eps = np.random.uniform(-1, 5)

            data.append({
                'ts_code': ts_code,
                'pe': pe,
                'pb': pb,
                'roe': roe,
                'eps': eps,
                'market_cap': np.random.uniform(10, 10000)  # 市值（亿）
            })

        return pd.DataFrame(data)

    def get_trading_calendar(self, start_date: str, end_date: str) -> List[str]:
        """获取交易日历"""
        # 模拟交易日历：工作日，排除周末
        start = pd.to_datetime(start_date)
        end = pd.to_datetime(end_date)

        dates = pd.date_range(start, end, freq='B')  # 工作日
        return [d.strftime('%Y%m%d') for d in dates]

    def get_suspended_stocks(self, trade_date: str) -> List[str]:
        """获取停牌股票"""
        if trade_date in self._suspended_cache:
            return list(self._suspended_cache[trade_date])

        # 模拟：随机1%的股票停牌
        np.random.seed(int(trade_date) % 10000)
        suspended_count = np.random.poisson(5)
        suspended = [f"{np.random.randint(1, 500):06d}.SZ"
                    for _ in range(suspended_count)]

        self._suspended_cache[trade_date] = set(suspended)
        return suspended

    def get_limit_prices(self, ts_code: str, trade_date: str) -> Tuple[float, float]:
        """获取涨跌停价格

        Returns:
            Tuple[float, float]: (limit_low, limit_high)
        """
        if trade_date in self._limit_prices_cache:
            if ts_code in self._limit_prices_cache[trade_date]:
                return self._limit_prices_cache[trade_date][ts_code]

        # 模拟：基于前收盘价计算涨跌停
        # 这里简化处理，返回0,0表示未知
        return 0.0, 0.0

    def set_limit_prices_for_date(self, trade_date: str,
                                   limit_prices: Dict[str, Tuple[float, float]]):
        """设置某日期的涨跌停价格"""
        self._limit_prices_cache[trade_date] = limit_prices

    def get_money_flow(self, ts_code_list: List[str]) -> pd.DataFrame:
        """获取资金流向（大单/超大单净流入）

        Returns:
            DataFrame with columns:
                - ts_code
                - trade_date
                - net_inflow_large: 大单净流入
                - net_inflow_super: 超大单净流入
                - net_inflow_main: 主力净流入
        """
        data = []
        for ts_code in ts_code_list:
            np.random.seed(hash(ts_code) % 10000)
            net_inflow_large = np.random.uniform(-10000, 10000)
            net_inflow_super = np.random.uniform(-5000, 5000)
            net_inflow_main = net_inflow_large + net_inflow_super

            data.append({
                'ts_code': ts_code,
                'net_inflow_large': net_inflow_large,
                'net_inflow_super': net_inflow_super,
                'net_inflow_main': net_inflow_main
            })

        return pd.DataFrame(data)
