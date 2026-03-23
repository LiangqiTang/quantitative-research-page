"""
股票数据采集器
负责采集个股的K线数据、财务数据、资金流向等信息
"""

import akshare as ak
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Optional, Any
import baostock as bs

class StockDataCollector:
    def __init__(self):
        self.ak = ak
        # 初始化baostock
        bs.login()

    def get_stock_basic(self, symbol: str, market: str = 'sz') -> Dict:
        """
        获取股票基本信息
        :param symbol: 股票代码
        :param market: 市场类型 (sh/sz)
        :return: 包含股票基本信息的字典
        """
        try:
            # 使用AKShare获取股票基本信息
            stock_info = self.ak.stock_individual_info_em(symbol=symbol)

            basic_info = {
                'symbol': symbol,
                'name': stock_info.get('证券简称', ''),
                'industry': stock_info.get('行业板块', ''),
                'concept': stock_info.get('概念板块', ''),
                'list_date': stock_info.get('上市日期', ''),
                'total_shares': stock_info.get('总股本(万股)', 0),
                'float_shares': stock_info.get('流通A股(万股)', 0),
                'pe': stock_info.get('市盈率-动态', 0),
                'pb': stock_info.get('市净率', 0),
                'latest_price': stock_info.get('最新价', 0),
                'change_percent': stock_info.get('涨跌幅', 0)
            }

            return basic_info

        except Exception as e:
            print(f"获取股票{symbol}基本信息失败: {e}")
            return {}

    def get_stock_kline(self, symbol: str, market: str = 'sz', period: str = 'daily',
                       start_date: Optional[str] = None) -> pd.DataFrame:
        """
        获取股票K线数据
        :param symbol: 股票代码
        :param market: 市场类型 (sh/sz)
        :param period: K线周期 (daily/weekly/monthly)
        :param start_date: 开始日期（格式: YYYYMMDD）
        :return: K线数据DataFrame
        """
        try:
            if start_date is None:
                # 默认获取最近一年的数据
                end_date = datetime.now()
                start_date = (end_date - timedelta(days=365)).strftime('%Y-%m-%d')

            # 使用baostock获取更稳定的K线数据
            period_map = {
                'daily': 'd',
                'weekly': 'w',
                'monthly': 'm'
            }

            # 格式化股票代码为baostock要求的格式
            full_symbol = f"{market}.{symbol}"

            rs = bs.query_history_k_data_plus(
                full_symbol,
                "date,code,open,high,low,close,preclose,volume,amount,adjustflag,turn,tradestatus,pctChg,peTTM,pbMRQ,psTTM,pcfNcfTTM,isST",
                start_date=start_date,
                frequency=period_map.get(period, 'd'),
                adjustflag="3"  # 后复权
            )

            data_list = []
            while (rs.error_code == '0') & rs.next():
                data_list.append(rs.get_row_data())

            df = pd.DataFrame(data_list, columns=rs.fields)

            # 转换数据类型
            numeric_cols = ['open', 'high', 'low', 'close', 'volume', 'amount', 'pctChg']
            for col in numeric_cols:
                df[col] = pd.to_numeric(df[col], errors='coerce')

            df['date'] = pd.to_datetime(df['date'])
            df = df.set_index('date')

            return df

        except Exception as e:
            print(f"获取股票{symbol}K线数据失败: {e}")
            # 回退使用AKShare获取数据
            try:
                if period == 'daily':
                    df = self.ak.stock_zh_a_daily(symbol=symbol, adjust='hfq')
                elif period == 'weekly':
                    df = self.ak.stock_zh_a_weekly(symbol=symbol, adjust='hfq')
                else:  # monthly
                    df = self.ak.stock_zh_a_monthly(symbol=symbol, adjust='hfq')
                return df
            except Exception as e2:
                print(f"回退方案也失败: {e2}")
                return pd.DataFrame()

    def get_stock_financial(self, symbol: str) -> Dict:
        """
        获取股票财务数据
        :param symbol: 股票代码
        :return: 包含财务数据的字典
        """
        try:
            # 使用AKShare获取财务指标
            finance_data = self.ak.stock_financial_report_sina(symbol=symbol)
            print(f"Debug: finance_data type is {type(finance_data)}")
            if isinstance(finance_data, pd.DataFrame) and not finance_data.empty:
                # 如果是DataFrame，取第一行
                finance_data = finance_data.iloc[0].to_dict()
            print(f"Debug: finance_data keys are {finance_data.keys() if isinstance(finance_data, dict) else 'Not a dict'}")

            financial = {
                'report_date': finance_data.get('报告期', ''),
                'eps': finance_data.get('每股收益', 0),
                'eps_yoy': finance_data.get('每股收益同比增长', 0),
                'revenue': finance_data.get('营业收入', 0),
                'revenue_yoy': finance_data.get('营业收入同比增长', 0),
                'profit': finance_data.get('净利润', 0),
                'profit_yoy': finance_data.get('净利润同比增长', 0),
                'roe': finance_data.get('净资产收益率', 0),
                'roa': finance_data.get('资产收益率', 0),
                'debt_ratio': finance_data.get('资产负债率', 0),
                'gross_margin': finance_data.get('销售毛利率', 0),
                'net_margin': finance_data.get('销售净利率', 0)
            }

            return financial

        except Exception as e:
            print(f"获取股票{symbol}财务数据失败: {e}")
            return {}

    def get_mainforce_flow(self, symbol: str) -> Dict:
        """
        获取主力资金流向数据
        :param symbol: 股票代码
        :return: 包含主力资金流向的字典
        """
        try:
            # 使用AKShare获取主力资金流
            mainforce_data = self.ak.stock_mainforce_em(symbol=symbol)

            flow_data = {
                'main_in': mainforce_data.get('主力净流入-净额', 0),
                'main_in_ratio': mainforce_data.get('主力净流入-净占比', 0),
                'super_in': mainforce_data.get('超大单净流入-净额', 0),
                'super_in_ratio': mainforce_data.get('超大单净流入-净占比', 0),
                'large_in': mainforce_data.get('大单净流入-净额', 0),
                'large_in_ratio': mainforce_data.get('大单净流入-净占比', 0),
                'medium_in': mainforce_data.get('中单净流入-净额', 0),
                'medium_in_ratio': mainforce_data.get('中单净流入-净占比', 0),
                'small_in': mainforce_data.get('小单净流入-净额', 0),
                'small_in_ratio': mainforce_data.get('小单净流入-净占比', 0),
                'total_amount': mainforce_data.get('今日主力资金流向-金额', 0)
            }

            return flow_data

        except Exception as e:
            print(f"获取股票{symbol}主力资金流向失败: {e}")
            return {}

    def __del__(self):
        """析构函数，关闭baostock连接"""
        try:
            bs.logout()
        except:
            pass

if __name__ == "__main__":
    # 测试代码
    collector = StockDataCollector()

    # 测试获取股票基本信息
    print("测试获取股票基本信息...")
    basic_info = collector.get_stock_basic('000001')
    print(basic_info)

    # 测试获取K线数据
    print("\n测试获取K线数据...")
    kline_data = collector.get_stock_kline('000001')
    print(kline_data.tail())

    # 测试获取财务数据
    print("\n测试获取财务数据...")
    financial_data = collector.get_stock_financial('000001')
    print(financial_data)

    # 测试获取主力资金流
    print("\n测试获取主力资金流...")
    mainforce_data = collector.get_mainforce_flow('000001')
    print(mainforce_data)