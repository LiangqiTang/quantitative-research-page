"""
多源数据获取器
负责从多个数据源获取数据，并自动进行故障转移和数据质量验证
"""

import pandas as pd
from typing import Dict, List, Optional, Any
from datetime import datetime
import asyncio
from concurrent.futures import ThreadPoolExecutor

class MultiSourceDataFetcher:
    def __init__(self):
        self.data_providers = {
            'akshare': self._get_akshare_data,
            'tushare': self._get_tushare_data,
            'baostock': self._get_baostock_data,
            'web_scraper': self._get_web_scraper_data
        }

    def fetch_stock_data(self, symbol: str, force_refresh: bool = False) -> Dict:
        """
        多源获取股票数据，自动故障转移
        :param symbol: 股票代码
        :param force_refresh: 是否强制刷新缓存
        :return: 整合后的股票数据
        """
        # 优先从缓存获取
        if not force_refresh:
            cached_data = self._get_from_cache(symbol)
            if cached_data:
                print(f"ℹ️ 从缓存获取 {symbol} 数据")
                return cached_data

        # 依次尝试不同数据源
        for provider_name, provider_func in self.data_providers.items():
            try:
                print(f"🔍 尝试从 {provider_name} 获取 {symbol} 数据...")
                data = provider_func(symbol)

                # 数据质量验证
                if self._validate_data_quality(data, provider_name):
                    print(f"✅ 从 {provider_name} 获取数据成功")
                    self._save_to_cache(symbol, data)
                    return data
                else:
                    print(f"⚠️ {provider_name} 数据质量不通过")

            except Exception as e:
                print(f"❌ 从 {provider_name} 获取数据失败: {e}")
                continue

        # 最终回退方案
        print("⚠️ 所有数据源都失败，使用回退方案")
        return self._fallback_strategy(symbol)

    async def fetch_stock_data_async(self, symbol: str, force_refresh: bool = False) -> Dict:
        """
        异步多源获取股票数据
        :param symbol: 股票代码
        :param force_refresh: 是否强制刷新缓存
        :return: 整合后的股票数据
        """
        if not force_refresh:
            cached_data = self._get_from_cache(symbol)
            if cached_data:
                print(f"ℹ️ 从缓存获取 {symbol} 数据")
                return cached_data

        # 并行尝试多个数据源
        tasks = []
        for provider_name, provider_func in self.data_providers.items():
            task = asyncio.to_thread(self._try_provider, provider_name, provider_func, symbol)
            tasks.append(task)

        # 等待第一个成功的结果
        done, pending = await asyncio.wait(
            tasks, return_when=asyncio.FIRST_COMPLETED
        )

        # 取消未完成的任务
        for task in pending:
            task.cancel()

        # 处理结果
        for task in done:
            try:
                result = await task
                if result:
                    self._save_to_cache(symbol, result)
                    return result
            except Exception as e:
                print(f"❌ 异步任务失败: {e}")

        # 全部失败，使用回退方案
        return self._fallback_strategy(symbol)

    def fetch_multiple_stocks(self, symbols: List[str],
                             force_refresh: bool = False) -> Dict[str, Dict]:
        """
        批量获取多只股票数据
        :param symbols: 股票代码列表
        :param force_refresh: 是否强制刷新缓存
        :return: 包含多只股票数据的字典
        """
        results = {}

        # 并行获取多只股票数据
        with ThreadPoolExecutor(max_workers=8) as executor:
            futures = []
            for symbol in symbols:
                future = executor.submit(
                    self.fetch_stock_data, symbol, force_refresh
                )
                futures.append((symbol, future))

            # 处理结果
            for symbol, future in futures:
                try:
                    data = future.result()
                    results[symbol] = data
                    print(f"✅ {symbol} 数据获取完成")
                except Exception as e:
                    print(f"❌ {symbol} 数据获取失败: {e}")
                    results[symbol] = {}

        return results

    async def fetch_multiple_stocks_async(self, symbols: List[str],
                                        force_refresh: bool = False) -> Dict[str, Dict]:
        """
        异步批量获取多只股票数据
        :param symbols: 股票代码列表
        :param force_refresh: 是否强制刷新缓存
        :return: 包含多只股票数据的字典
        """
        tasks = [
            self.fetch_stock_data_async(symbol, force_refresh)
            for symbol in symbols
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        return {
            symbol: result if not isinstance(result, Exception) else {}
            for symbol, result in zip(symbols, results)
        }

    def _try_provider(self, provider_name: str, provider_func, symbol: str) -> Optional[Dict]:
        """
        尝试从单个数据源获取数据
        :param provider_name: 数据源名称
        :param provider_func: 数据源函数
        :param symbol: 股票代码
        :return: 数据或None
        """
        try:
            data = provider_func(symbol)
            if self._validate_data_quality(data, provider_name):
                print(f"✅ 从 {provider_name} 获取数据成功")
                return data
            else:
                print(f"⚠️ {provider_name} 数据质量不通过")
                return None
        except Exception as e:
            print(f"❌ 从 {provider_name} 获取数据失败: {e}")
            return None

    def _validate_data_quality(self, data: Dict, source: str) -> bool:
        """
        多维度数据质量验证
        :param data: 待验证数据
        :param source: 数据源名称
        :return: 验证是否通过
        """
        try:
            validator = DataQualityValidator()

            # 基本字段验证
            basic_check = validator.has_required_fields(data)
            if not basic_check:
                print(f"❌ {source} 基本字段验证失败")
                return False

            # 数据合理性验证
            rationality_check = validator.is_data_rational(data)
            if not rationality_check:
                print(f"❌ {source} 数据合理性验证失败")
                return False

            # 跨源一致性验证
            consistency_check = validator.cross_source_consistency(data, source)
            if not consistency_check:
                print(f"❌ {source} 跨源一致性验证失败")
                return False

            return True

        except Exception as e:
            print(f"❌ 数据质量验证失败: {e}")
            return False

    def _get_from_cache(self, symbol: str) -> Optional[Dict]:
        """
        从缓存获取数据
        :param symbol: 股票代码
        :return: 缓存数据或None
        """
        # 实际实现中应该使用Redis或其他缓存机制
        # 这里简化实现，不做实际缓存
        return None

    def _save_to_cache(self, symbol: str, data: Dict):
        """
        保存数据到缓存
        :param symbol: 股票代码
        :param data: 要保存的数据
        """
        # 实际实现中应该使用Redis或其他缓存机制
        pass

    def _fallback_strategy(self, symbol: str) -> Dict:
        """
        最终回退方案
        :param symbol: 股票代码
        :return: 基础数据结构
        """
        return {
            'symbol': symbol,
            'name': symbol,
            'kline': pd.DataFrame(),
            'financial': {},
            'basic': {},
            'mainforce': {},
            'fallback': True,
            'update_time': datetime.now()
        }

    # 各个数据源的具体实现
    def _get_akshare_data(self, symbol: str) -> Dict:
        """从AKShare获取数据"""
        import akshare as ak

        try:
            stock_info = ak.stock_individual_info_em(symbol=symbol)
            kline_data = ak.stock_zh_a_daily(symbol=symbol, adjust='hfq')

            return {
                'symbol': symbol,
                'name': stock_info.get('证券简称', symbol),
                'kline': kline_data,
                'financial': {
                    'pe': stock_info.get('市盈率-动态', 0),
                    'pb': stock_info.get('市净率', 0),
                    'eps': stock_info.get('每股收益(元)', 0),
                    'revenue': stock_info.get('营业收入(亿元)', 0),
                    'profit': stock_info.get('净利润(亿元)', 0)
                },
                'basic': {
                    'industry': stock_info.get('行业板块', ''),
                    'concept': stock_info.get('概念板块', ''),
                    'list_date': stock_info.get('上市日期', ''),
                    'total_shares': stock_info.get('总股本(万股)', 0)
                },
                'source': 'akshare',
                'update_time': datetime.now()
            }

        except Exception as e:
            raise Exception(f"AKShare获取失败: {e}")

    def _get_tushare_data(self, symbol: str) -> Dict:
        """从Tushare获取数据"""
        import tushare as ts

        try:
            # 需要设置Tushare的token
            pro = ts.pro_api()

            # 获取股票基本信息
            stock_basic = pro.stock_basic(ts_code=symbol)
            if not stock_basic.empty:
                name = stock_basic.iloc[0]['name']
                industry = stock_basic.iloc[0]['industry']
            else:
                name = symbol
                industry = ''

            # 获取K线数据
            kline_data = pro.daily(ts_code=symbol, start_date='20230101')

            return {
                'symbol': symbol,
                'name': name,
                'kline': kline_data,
                'financial': {},
                'basic': {
                    'industry': industry,
                    'list_date': '',
                    'total_shares': 0
                },
                'source': 'tushare',
                'update_time': datetime.now()
            }

        except Exception as e:
            raise Exception(f"Tushare获取失败: {e}")

    def _get_baostock_data(self, symbol: str) -> Dict:
        """从Baostock获取数据"""
        import baostock as bs

        try:
            lg = bs.login()
            if lg.error_code != '0':
                raise Exception(f"Baostock登录失败: {lg.error_msg}")

            # 获取K线数据
            rs = bs.query_history_k_data_plus(
                symbol,
                "date,code,open,high,low,close,preclose,volume,amount,adjustflag,turn,tradestatus,pctChg,peTTM,pbMRQ,psTTM,pcfNcfTTM,isST",
                start_date='2023-01-01',
                frequency="d",
                adjustflag="3"
            )

            data_list = []
            while (rs.error_code == '0') & rs.next():
                data_list.append(rs.get_row_data())

            kline_data = pd.DataFrame(data_list, columns=rs.fields)

            # 获取股票基本信息
            rs_basic = bs.query_stock_basic(code=symbol)
            basic_data = rs_basic.get_row_data() if rs_basic.error_code == '0' else []

            bs.logout()

            return {
                'symbol': symbol,
                'name': basic_data[1] if basic_data else symbol,
                'kline': kline_data,
                'financial': {},
                'basic': {
                    'industry': basic_data[3] if basic_data else '',
                    'list_date': basic_data[2] if basic_data else '',
                    'total_shares': 0
                },
                'source': 'baostock',
                'update_time': datetime.now()
            }

        except Exception as e:
            try:
                bs.logout()
            except:
                pass
            raise Exception(f"Baostock获取失败: {e}")

    def _get_web_scraper_data(self, symbol: str) -> Dict:
        """从网页抓取获取数据"""
        # 实现网页抓取逻辑
        raise NotImplementedError("网页抓取功能尚未实现")

class DataQualityValidator:
    """数据质量验证器"""

    def has_required_fields(self, data: Dict) -> bool:
        """检查是否包含必要字段"""
        required_fields = ['symbol', 'name', 'kline', 'basic']

        for field in required_fields:
            if field not in data:
                print(f"❌ 缺失必要字段: {field}")
                return False

        # 检查K线数据是否为空
        if data['kline'] is None or data['kline'].empty:
            print("❌ K线数据为空")
            return False

        return True

    def is_data_rational(self, data: Dict) -> bool:
        """检查数据是否合理"""
        try:
            kline = data['kline']

            # 检查价格是否为正
            if 'close' in kline.columns:
                close_prices = pd.to_numeric(kline['close'], errors='coerce')
                if (close_prices <= 0).any():
                    print("❌ 存在非正价格")
                    return False

            # 检查成交量是否为正
            if 'volume' in kline.columns:
                volumes = pd.to_numeric(kline['volume'], errors='coerce')
                if (volumes < 0).any():
                    print("❌ 存在负成交量")
                    return False

            # 检查涨跌幅是否合理
            if 'pctChg' in kline.columns:
                pct_chg = pd.to_numeric(kline['pctChg'], errors='coerce')
                if (abs(pct_chg) > 20).any():  # 涨跌幅超过20%视为异常
                    print("❌ 存在异常涨跌幅")
                    return False

            return True

        except Exception as e:
            print(f"❌ 数据合理性检查失败: {e}")
            return False

    def cross_source_consistency(self, data: Dict, source: str) -> bool:
        """跨源一致性检查"""
        # 简单实现，实际应该和其他数据源进行对比
        return True

if __name__ == "__main__":
    # 测试代码
    fetcher = MultiSourceDataFetcher()

    # 同步获取数据
    data = fetcher.fetch_stock_data('000001')
    print(f"\n📊 获取到的数据包含:")
    print(f"  - 股票代码: {data.get('symbol')}")
    print(f"  - 股票名称: {data.get('name')}")
    print(f"  - 数据源: {data.get('source')}")
    print(f"  - K线数据行数: {len(data.get('kline', pd.DataFrame()))}")

    # 异步获取数据
    import asyncio
    async def test_async():
        data = await fetcher.fetch_stock_data_async('600036')
        print(f"\n📊 异步获取到的数据包含:")
        print(f"  - 股票代码: {data.get('symbol')}")
        print(f"  - 股票名称: {data.get('name')}")
        print(f"  - 数据源: {data.get('source')}")

    asyncio.run(test_async())