#!/usr/bin/env python3
"""
测试Tushare数据源
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
print("=" * 80)
print("🔍 测试Tushare数据源")
print("=" * 80)

# 1. 测试Tushare
print("\n1️⃣ 初始化Tushare...")
try:
    import tushare as ts
    token = os.getenv('TUSHARE_TOKEN', '')
    print(f"   Token长度: {len(token) if token else 0}")

    pro = ts.pro_api(token)
    print("   ✅ Tushare初始化成功")

    # 测试获取股票列表
    print("\n2️⃣ 测试获取股票列表...")
    stock_basic = pro.stock_basic(exchange='', list_status='L', fields='ts_code,symbol,name,area,industry,list_date')
    print(f"   ✅ 获取到 {len(stock_basic)} 只股票")
    if len(stock_basic) > 0:
        print("\n   📊 前10只股票:")
        for i, (_, row) in enumerate(stock_basic.head(10).iterrows(), 1):
            print(f"      {i}. {row['ts_code']} - {row['name']} ({row['industry']})")

    # 测试获取K线数据
    print("\n3️⃣ 测试获取K线数据...")
    test_code = '000001.SZ'
    df = pro.daily(ts_code=test_code, start_date='20240101', end_date='20241231')
    print(f"   ✅ 获取到 {len(df)} 条K线数据")
    if len(df) > 0:
        print("\n   📊 最近5条记录:")
        print(df.head())

    # 测试获取财务数据
    print("\n4️⃣ 测试获取财务数据...")
    fina = pro.fina_indicator(ts_code=test_code, start_date='20230101', end_date='20241231')
    print(f"   ✅ 获取到 {len(fina)} 条财务指标")

    print("\n" + "=" * 80)
    print("🎉 Tushare测试完成！数据来源可靠！")
    print("=" * 80)

except Exception as e:
    print(f"\n❌ Tushare测试失败: {e}")
    import traceback
    traceback.print_exc()
