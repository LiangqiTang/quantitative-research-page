"""
宏观数据采集器
负责采集大盘指数、涨跌家数、资金流向、板块热点等宏观市场数据
"""

import requests
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional
import json

class MacroDataCollector:
    def __init__(self):
        self.sources = {
            'eastmoney': 'https://push2.eastmoney.com/api/qt/clist/get',
            '10jqka': 'https://d.10jqka.com.cn/v6/line/hsgt/quote',
            'sse': 'https://query.sse.com.cn/commonQuery.do'
        }

    def get_market_overview(self) -> Dict:
        """
        获取市场概况
        返回包含大盘指数、涨跌家数、成交额等数据的字典
        """
        try:
            data = {}

            # 1. 获取大盘指数数据
            try:
                data.update(self._get_index_data())
            except Exception as e:
                print(f"获取指数数据失败: {e}，使用模拟数据")
                data.update(self._get_mock_index_data())

            # 2. 获取涨跌家数数据
            try:
                data.update(self._get_market_breadth())
            except Exception as e:
                print(f"获取涨跌家数失败: {e}，使用模拟数据")
                data.update(self._get_mock_breadth_data())

            # 3. 获取资金流向数据
            try:
                data.update(self._get_money_flow())
            except Exception as e:
                print(f"获取资金流向失败: {e}，使用模拟数据")
                data.update(self._get_mock_money_flow_data())

            return data

        except Exception as e:
            print(f"获取市场概况失败: {e}，返回完整模拟数据")
            return self._get_full_mock_data()

    def get_hot_sectors(self, limit: int = 20) -> List[Dict]:
        """
        获取热点板块
        返回包含板块名称、涨跌幅、领涨股等信息的列表
        """
        try:
            # 从东方财富获取热点板块
            url = "https://push2.eastmoney.com/api/qt/clist/get"
            params = {
                'pn': '1',
                'pz': str(limit),
                'po': '1',
                'np': '1',
                'ut': 'bd1d9ddb04089700cf9c27f6f742628',
                'fltt': '2',
                'invt': '2',
                'fid': 'f3',
                'fs': 'b:BK0001',
                'fields': 'f1,f2,f3,f4,f5,f6,f7,f8,f9,f10,f12,f13,f14,f15,f16,f17,f18,f20,f21,f23,f24,f25,f22,f11,f62,f128,f136,f115,f152'
            }

            response = requests.get(url, params=params)
            result = response.json()

            sectors = []
            if result['data']['diff']:
                for item in result['data']['diff']:
                    sector = {
                        'code': item.get('f12', ''),
                        'name': item.get('f14', ''),
                        'change': item.get('f3', 0),
                        'change_percent': item.get('f3', 0),
                        'amount': item.get('f5', 0),
                        'volume': item.get('f4', 0),
                        'top_stock': item.get('f15', ''),
                        'top_stock_change': item.get('f16', 0),
                        'rise_count': item.get('f17', 0),
                        'fall_count': item.get('f18', 0)
                    }
                    sectors.append(sector)

            return sectors

        except Exception as e:
            print(f"获取热点板块失败: {e}")
            return []

    def _get_index_data(self) -> Dict:
        """获取主要指数数据"""
        try:
            # 上证指数、深证成指、创业板指
            index_codes = {
                'sh': '1.000001',
                'sz': '0.399001',
                'cyb': '0.399006'
            }

            url = "https://push2.eastmoney.com/api/qt/clist/get"
            params = {
                'pn': '1',
                'pz': '3',
                'po': '1',
                'np': '1',
                'ut': 'bd1d9ddb04089700cf9c27f6f742628',
                'fltt': '2',
                'invt': '2',
                'fid': 'f3',
                'fs': f"m:{index_codes['sh']},m:{index_codes['sz']},m:{index_codes['cyb']}",
                'fields': 'f1,f2,f3,f4,f5,f6,f7,f8,f9,f10,f12,f13,f14,f15,f16,f17,f18'
            }

            response = requests.get(url, params=params)
            result = response.json()

            data = {}
            if result['data']['diff']:
                for item in result['data']['diff']:
                    code = item.get('f12', '')
                    if index_codes['sh'] in code:
                        prefix = 'sh'
                    elif index_codes['sz'] in code:
                        prefix = 'sz'
                    elif index_codes['cyb'] in code:
                        prefix = 'cyb'
                    else:
                        continue

                    data[f'{prefix}_price'] = item.get('f2', 0)
                    data[f'{prefix}_change'] = item.get('f3', 0)
                    data[f'{prefix}_change_percent'] = item.get('f3', 0)
                    data[f'{prefix}_amount'] = item.get('f5', 0)
                    data[f'{prefix}_volume'] = item.get('f4', 0)

            return data

        except Exception as e:
            print(f"获取指数数据失败: {e}")
            return {}

    def _get_market_breadth(self) -> Dict:
        """获取市场广度数据（涨跌家数、涨跌停家数等）"""
        try:
            # 从东方财富获取涨跌家数
            url = "https://push2.eastmoney.com/api/qt/publish.data/get"
            params = {
                'ut': '7eea3edcaed734bea9cbfc24409ed989',
                'cb': '',
                'data_type': 'RPT_MKT_SJ_ZDFL',
                'page_size': '100',
                'page_no': '1'
            }

            response = requests.get(url, params=params)
            result = response.json()

            data = {}
            if result['data']:
                for item in result['data']:
                    if item['reportType'] == 'reportType_Z':
                        data['up_count'] = item['value1']
                        data['down_count'] = item['value2']
                        data['flat_count'] = item['value3']
                        data['up_ratio'] = data['up_count'] / (data['up_count'] + data['down_count'] + data['flat_count'])
                        break

            return data

        except Exception as e:
            print(f"获取涨跌家数失败: {e}")
            return {}

    def _get_money_flow(self) -> Dict:
        """获取资金流向数据"""
        try:
            # 获取沪深两市资金流向
            url = "https://data.eastmoney.com/zjlx/"
            response = requests.get(url)

            # 使用正则表达式提取数据（简化实现）
            import re
            pattern = r'\{"sgtAmt":(.*?),"hgtAmt":(.*?),"zdf":(.*?),"zjlx":(.*?)\}'
            match = re.search(pattern, response.text)

            if match:
                data = {
                    'north_money': float(match.group(1)) + float(match.group(2)),
                    'south_money': 0,  # 需要单独获取
                }
                return data

            return {}

        except Exception as e:
            print(f"获取资金流向失败: {e}")
            return {}

if __name__ == "__main__":
    # 测试代码
    collector = MacroDataCollector()
    print("获取市场概况...")
    overview = collector.get_market_overview()
    print(overview)

    print("\n获取热点板块...")
    sectors = collector.get_hot_sectors()
    for sector in sectors[:5]:
        print(sector)