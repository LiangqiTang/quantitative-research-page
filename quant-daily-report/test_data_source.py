#!/usr/bin/env python3
"""
测试数据源可用性
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 60)
print("🔍 测试数据源可用性")
print("=" * 60)

# 测试1: AKShare
print("\n1️⃣ 测试AKShare...")
try:
    import akshare as ak
    print(f"   ✅ AKShare已安装: {ak.__version__}")

    # 测试获取股票列表
    print("   📊 尝试获取股票列表...")
    try:
        # 尝试一个简单的API
        stock_info = ak.stock_individual_info_em(symbol="000001")
        print(f"   ✅ AKShare API可用")
        print(f"      股票名称: {stock_info.get('证券简称', 'N/A')}")
    except Exception as e:
        print(f"   ⚠️ AKShare API调用失败: {e}")

except Exception as e:
    print(f"   ❌ AKShare不可用: {e}")

# 测试2: Baostock
print("\n2️⃣ 测试Baostock...")
try:
    import baostock as bs
    print("   ✅ Baostock已安装")

    # 测试登录
    print("   🔑 尝试登录Baostock...")
    lg = bs.login()
    if lg.error_code == '0':
        print(f"   ✅ Baostock登录成功")

        # 测试获取数据
        print("   📊 尝试获取K线数据...")
        try:
            rs = bs.query_history_k_data_plus(
                "sh.600000",
                "date,code,open,high,low,close",
                start_date="2024-01-01",
                frequency="d",
                adjustflag="3"
            )
            if rs.error_code == '0':
                data_list = []
                count = 0
                while (rs.error_code == '0') & rs.next():
                    data_list.append(rs.get_row_data())
                    count += 1
                    if count >= 5:
                        break
                print(f"   ✅ Baostock数据获取成功，获取{len(data_list)}条记录")
            else:
                print(f"   ⚠️ Baostock数据获取失败: {rs.error_msg}")
        except Exception as e:
            print(f"   ⚠️ Baostock数据获取异常: {e}")
        finally:
            bs.logout()
            print("   🔒 Baostock已登出")
    else:
        print(f"   ❌ Baostock登录失败: {lg.error_msg}")

except Exception as e:
    print(f"   ❌ Baostock不可用: {e}")

# 测试3: Tushare（如果配置了token）
print("\n3️⃣ 测试Tushare...")
tushare_token = os.getenv('TUSHARE_TOKEN', '')
if tushare_token:
    print(f"   🔑 发现Tushare token")
    try:
        import tushare as ts
        print("   ✅ Tushare已安装")
        pro = ts.pro_api(tushare_token)
        print("   ✅ Tushare token有效")
    except Exception as e:
        print(f"   ⚠️ Tushare不可用: {e}")
else:
    print("   ℹ️ 未配置Tushare token（可选）")

print("\n" + "=" * 60)
print("✅ 数据源测试完成")
print("=" * 60)
