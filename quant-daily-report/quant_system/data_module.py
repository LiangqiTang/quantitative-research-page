"""
数据模块 - 多源数据获取
支持Tushare、Baostock等数据源，带缓存机制
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime, timedelta
import hashlib
import json
import time


class DataManager:
    """
    数据管理器 - 多源数据获取

    支持：
    - Tushare（优先）
    - Baostock（备用）
    - 本地缓存
    """

    def __init__(self, token: Optional[str] = None, cache_dir: str = "quant_cache"):
        """
        初始化数据管理器

        Args:
            token: Tushare token
            cache_dir: 缓存目录
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)

        self.token = token
        self.ts_pro = None

        # 初始化Tushare
        if token:
            try:
                import tushare as ts
                self.ts_pro = ts.pro_api(token)
                print("✅ Tushare初始化成功")
            except Exception as e:
                print(f"⚠️  Tushare初始化失败: {e}")

        print("✅ 数据管理器初始化完成")

    def _get_cache_path(self, prefix: str, identifier: str) -> Path:
        """
        获取缓存文件路径

        Args:
            prefix: 缓存前缀
            identifier: 标识字符串

        Returns:
            Path: 缓存文件路径
        """
        hash_obj = hashlib.md5(identifier.encode())
        cache_key = hash_obj.hexdigest()
        return self.cache_dir / f"{prefix}_{cache_key}.pkl"

    def _load_cache(self, cache_path: Path, max_age_hours: int = 24) -> Optional[pd.DataFrame]:
        """
        加载缓存数据

        Args:
            cache_path: 缓存文件路径
            max_age_hours: 最大缓存年龄（小时）

        Returns:
            DataFrame: 缓存数据，过期返回None
        """
        if not cache_path.exists():
            return None

        # 检查缓存是否过期
        mtime = datetime.fromtimestamp(cache_path.stat().st_mtime)
        age = datetime.now() - mtime
        if age > timedelta(hours=max_age_hours):
            return None

        try:
            df = pd.read_pickle(cache_path)
            return df
        except Exception:
            return None

    def _save_cache(self, df: pd.DataFrame, cache_path: Path):
        """
        保存缓存数据

        Args:
            df: 数据
            cache_path: 缓存文件路径
        """
        try:
            df.to_pickle(cache_path)
        except Exception as e:
            print(f"⚠️  保存缓存失败: {e}")

    def get_stock_list(self, count: Optional[int] = None) -> List[Dict]:
        """
        获取股票列表

        Args:
            count: 限制返回数量

        Returns:
            List[Dict]: 股票列表
        """
        cache_path = self._get_cache_path("stock_list", "all")
        cached = self._load_cache(cache_path, max_age_hours=48)

        if cached is not None:
            stocks = cached.to_dict('records')
            if count:
                stocks = stocks[:count]
            print(f"✅ 从缓存加载 {len(stocks)} 只股票")
            return stocks

        stocks = []

        # 尝试Tushare
        if self.ts_pro:
            try:
                df = self.ts_pro.stock_basic(exchange='', list_status='L', fields='ts_code,symbol,name,industry,list_date')
                stocks = df.to_dict('records')
                self._save_cache(df, cache_path)
                print(f"✅ 从Tushare获取 {len(stocks)} 只股票")
                if count:
                    stocks = stocks[:count]
                return stocks
            except Exception as e:
                print(f"⚠️  Tushare获取股票列表失败: {e}")

        # 备用：使用示例数据
        print("⚠️  使用示例股票数据")
        sample_stocks = [
            {'ts_code': '000001.SZ', 'symbol': '000001', 'name': '平安银行', 'industry': '银行'},
            {'ts_code': '000002.SZ', 'symbol': '000002', 'name': '万科A', 'industry': '地产'},
            {'ts_code': '600000.SH', 'symbol': '600000', 'name': '浦发银行', 'industry': '银行'},
            {'ts_code': '600519.SH', 'symbol': '600519', 'name': '贵州茅台', 'industry': '白酒'},
            {'ts_code': '601318.SH', 'symbol': '601318', 'name': '中国平安', 'industry': '保险'},
        ]

        # 生成更多示例股票
        for i in range(15):
            base_code = 600001 + i
            sample_stocks.append({
                'ts_code': f'{base_code:06d}.SH',
                'symbol': f'{base_code:06d}',
                'name': f'示例股票{i+1}',
                'industry': '综合'
            })

        df = pd.DataFrame(sample_stocks)
        self._save_cache(df, cache_path)

        if count:
            sample_stocks = sample_stocks[:count]

        print(f"✅ 使用 {len(sample_stocks)} 只示例股票")
        return sample_stocks

    def get_daily(self, ts_code: str, start_date: str, end_date: str) -> Optional[pd.DataFrame]:
        """
        获取日线数据

        Args:
            ts_code: 股票代码
            start_date: 开始日期 (YYYYMMDD)
            end_date: 结束日期 (YYYYMMDD)

        Returns:
            DataFrame: 日线数据
        """
        cache_id = f"{ts_code}_{start_date}_{end_date}"
        cache_path = self._get_cache_path("daily", cache_id)
        cached = self._load_cache(cache_path, max_age_hours=4)

        if cached is not None:
            return cached

        df = None

        # 尝试Tushare
        if self.ts_pro:
            try:
                df = self.ts_pro.daily(ts_code=ts_code, start_date=start_date, end_date=end_date)
                if df is not None and not df.empty:
                    df = df.sort_values('trade_date').reset_index(drop=True)
                    self._save_cache(df, cache_path)
                    return df
            except Exception as e:
                print(f"⚠️  Tushare获取日线失败 ({ts_code}): {e}")

        # 生成模拟数据
        print(f"⚠️  生成模拟日线数据 ({ts_code})")
        df = self._generate_mock_daily(ts_code, start_date, end_date)
        self._save_cache(df, cache_path)
        return df

    def _generate_mock_daily(self, ts_code: str, start_date: str, end_date: str) -> pd.DataFrame:
        """
        生成模拟日线数据

        Args:
            ts_code: 股票代码
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            DataFrame: 模拟数据
        """
        # 生成日期范围
        start_dt = datetime.strptime(start_date, "%Y%m%d")
        end_dt = datetime.strptime(end_date, "%Y%m%d")

        # 生成交易日（约252天/年）
        dates = []
        current = start_dt
        while current <= end_dt:
            if current.weekday() < 5:  # 周一到周五
                dates.append(current.strftime("%Y%m%d"))
            current += timedelta(days=1)

        # 基于股票代码生成确定性的随机种子
        seed = sum(ord(c) for c in ts_code)
        np.random.seed(seed)

        # 生成价格数据
        n = len(dates)
        base_price = 50 + (seed % 50)  # 50-100的基础价格

        # 随机游走
        returns = np.random.normal(0.001, 0.02, n)
        prices = base_price * (1 + returns).cumprod()

        # 生成OHLC
        high = prices * (1 + np.random.uniform(0, 0.03, n))
        low = prices * (1 - np.random.uniform(0, 0.03, n))
        open_prices = low + np.random.uniform(0, 1, n) * (high - low)
        close = prices
        vol = np.random.randint(1000000, 10000000, n)
        amount = close * vol * 0.1

        data = {
            'ts_code': [ts_code] * n,
            'trade_date': dates,
            'open': open_prices.round(2),
            'high': high.round(2),
            'low': low.round(2),
            'close': close.round(2),
            'vol': vol,
            'amount': amount.round(2),
            'change': (close - np.roll(close, 1)).round(2),
            'pct_chg': returns.round(4) * 100,
        }
        data['change'][0] = 0
        data['pct_chg'][0] = 0

        df = pd.DataFrame(data)
        return df

    def prepare_factor_data(self, stock_list: Optional[List[str]] = None,
                           start_date: Optional[str] = None,
                           end_date: Optional[str] = None) -> Dict[str, pd.DataFrame]:
        """
        准备因子计算数据

        Args:
            stock_list: 股票列表
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            Dict: 股票代码 -> 数据DataFrame
        """
        if start_date is None:
            start_date = (datetime.now() - timedelta(days=365)).strftime("%Y%m%d")
        if end_date is None:
            end_date = datetime.now().strftime("%Y%m%d")

        if stock_list is None:
            stocks = self.get_stock_list(count=20)
            stock_list = [s['ts_code'] for s in stocks]

        print(f"\n📊 准备因子数据: {len(stock_list)} 只股票")
        print(f"   时间范围: {start_date} 至 {end_date}")

        data_dict = {}
        for i, ts_code in enumerate(stock_list):
            if (i + 1) % 5 == 0 or i == 0:
                print(f"   进度: {i+1}/{len(stock_list)}", end='\r')

            df = self.get_daily(ts_code, start_date, end_date)
            if df is not None and not df.empty:
                data_dict[ts_code] = df

        print(f"\n✅ 成功加载 {len(data_dict)} 只股票数据")
        return data_dict

    def get_index_daily(self, ts_code: str, start_date: str, end_date: str) -> Optional[pd.DataFrame]:
        """
        获取指数日线数据

        Args:
            ts_code: 指数代码
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            DataFrame: 指数数据
        """
        cache_id = f"index_{ts_code}_{start_date}_{end_date}"
        cache_path = self._get_cache_path("index", cache_id)
        cached = self._load_cache(cache_path, max_age_hours=4)

        if cached is not None:
            return cached

        df = None

        # 尝试Tushare
        if self.ts_pro:
            try:
                df = self.ts_pro.index_daily(ts_code=ts_code, start_date=start_date, end_date=end_date)
                if df is not None and not df.empty:
                    df = df.sort_values('trade_date').reset_index(drop=True)
                    self._save_cache(df, cache_path)
                    return df
            except Exception as e:
                print(f"⚠️  Tushare获取指数失败: {e}")

        # 生成模拟指数数据
        df = self._generate_mock_daily(ts_code, start_date, end_date)
        self._save_cache(df, cache_path)
        return df
